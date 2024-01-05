import random

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from tools import send_email, get_user_id

from .repository import EmailVerifyRepo
from app.user.repository import UserRepo
from app.auth.auth_handler import email_verify_JWT
from app.auth.auth_bearer import JWTBearer

router = APIRouter()

@router.post("/confirm", tags=["User"])
async def confirm(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    email = req_data["email"]
    username = req_data["username"]
    result = await UserRepo.fetch_by_email(db, email)
    if result:
        raise HTTPException(status_code=400, detail="L'adresse e-mail existe déjà!")
    result = await UserRepo.fetch_by_username(db, username)
    if result:
        raise HTTPException(status_code=400, detail="Le nom d'utilisateur existe déjà!")
    verify_code = str(random.randint(100000, 999999))
    emailverify = {
        "email": email,
        "verify_code": verify_code
    }
    result = await EmailVerifyRepo.create(db, emailverify)
    if result == False:
        raise HTTPException(status_code=400, detail="Échec de la création du code de vérification par e-mail!")
    return {
        "email": email
    }

@router.post("/generate_code", dependencies=[Depends(JWTBearer())], tags=["User"])
async def confirm(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    email = req_data["email"]
    result = await UserRepo.fetch_by_email(db, email)
    if result:
        raise HTTPException(status_code=400, detail="L'adresse e-mail existe déjà!")
    verify_code = str(random.randint(100000, 999999))
    emailverify = {
        "email": email,
        "verify_code": verify_code
    }
    result = await EmailVerifyRepo.create(db, emailverify)
    if result == False:
        raise HTTPException(status_code=400, detail="Échec de la création du code de vérification par e-mail!")
    return {
        "email": email
    }

@router.post("/confirm_email", dependencies=[Depends(JWTBearer())], tags=["User"])
async def confirm_email(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    email = req_data["email"]
    result = await UserRepo.fetch_by_email(db, email)
    if result:
        raise HTTPException(status_code=400, detail="L'adresse e-mail existe déjà!")
    return email

@router.post("/confirm_username", dependencies=[Depends(JWTBearer())], tags=["User"])
async def confirm_username(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    username = req_data["username"]
    result = await UserRepo.fetch_by_username(db, username)
    if result:
        raise HTTPException(status_code=400, detail="Le nom d'utilisateur existe déjà!")
    return username

@router.get("/send_verify_code/{email}", tags=["User"])
async def send_verify_code(email: str, db: Session=Depends(get_db)):
    verify_code = await EmailVerifyRepo.get_verify_code(db, email)
    if verify_code == False:
        raise HTTPException(status_code=400, detail="Le code de vérification par e-mail n'existe pas!")
    subject = "Vérification de l'E-mail!"
    email_body = f"""
    <html>
        <body>
            <p>Hi!</p>
            <p>Vous avez presque fini.</p>
            <p>REEACT Code de validation: <strong>{verify_code}</strong>.</p>
            <p>Entrez le code de vérification s'il vous plaît !</p>
        </body>
    </html>
    """
    send_result = await send_email(email, subject, email_body)
    if send_result == False:
        raise HTTPException(status_code=400, detail="L'e-mail n'a pas été envoyé !")
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

@router.post("/verify_setting_code", dependencies=[Depends(JWTBearer())], tags=["User"])
async def email_setting_verify(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    req_data = await request.json()
    email = req_data["email"]
    verify_code = req_data["verify_code"]
    
    verify_result = await EmailVerifyRepo.check_verify_code(db, email, verify_code)
    if verify_result != True:
        raise HTTPException(status_code=400, detail=verify_result)
    
    token = email_verify_JWT(email, verify_code)
    add_token = await UserRepo.add_forgot_password_token(db, user_id, token)
    if add_token == False:
        raise HTTPException(status_code=400, detail="Échec de l'ajout de jeton.")
    return {
        "token": token
    }