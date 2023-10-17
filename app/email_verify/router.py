import random

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from tools import send_email

from .repository import EmailVerifyRepo
from app.user.repository import UserRepo
from app.auth.auth_handler import email_verify_JWT

router = APIRouter()

@router.post("/confirm_email", tags=["User"])
async def confirm_email(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    email = req_data["email"]
    result = await UserRepo.fetch_by_email(db, email)
    if result:
        raise HTTPException(status_code=400, detail="User already exists!")
    verify_code = str(random.randint(100000, 999999))
    emailverify = {
        "email": email,
        "verify_code": verify_code
    }
    result = await EmailVerifyRepo.create(db, emailverify)
    if result == False:
        raise HTTPException(status_code=400, detail="Email Verify Code Create Failed!")
    return email    

@router.get("/send_verify_code/{email}", tags=["User"])
async def send_verify_code(email: str, db: Session=Depends(get_db)):
    verify_code = await EmailVerifyRepo.get_verify_code(db, email)
    if verify_code == False:
        raise HTTPException(status_code=400, detail="Email Verify Code Not Exist!")
    subject = "Email Verification!"
    email_body = f"""
    <html>
        <body>
            <p>Hi,</p>
            <p>You are almost up to finish.</p>
            <p>Your email verification code is: {verify_code}.</p>
            <p>Please type code to site!</p>
        </body>
    </html>
    """
    send_result = await send_email(email, subject, email_body)
    if send_result == False:
        raise HTTPException(status_code=400, detail="Email Not Sent!")
    return True

@router.post("/verify_code", tags=["User"])
async def email_verify(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    email = req_data["email"]
    verify_code = req_data["verify_code"]
    
    verify_result = await EmailVerifyRepo.check_verify_code(db, email, verify_code)
    if verify_result != True:
        raise HTTPException(status_code=400, detail=verify_result)
    
    token = email_verify_JWT(email, verify_code)
    return token