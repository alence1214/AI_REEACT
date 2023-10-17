from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db

from .repository import PaymentLogRepo
from app.auth.auth_bearer import JWTBearer

from . import schema as paymentSchema

router = APIRouter()

@router.post("/checkout", dependencies=[Depends(JWTBearer())], tags=["Payment"])
async def create_payment(checkout_request: paymentSchema.CheckOut):
    """
        Get Stripe Client Secret
    """
    # try:
    #     intent = stripe.PaymentIntent.create(
    #         amount = checkout_request.amount,
    #         currency = "USD",
    #     )
        
    #     client_secret = intent['client_secret']
    #     return {
    #         "client_secret": client_secret
    #     }
    # except Exception as e:
    #     return {"error": str(e)}
    return True
    
@router.get("/paymentLog", dependencies=[Depends(JWTBearer())], tags=["Payment"])
async def get_all_payment_log(db: Session=Depends(get_db)):
    
    all_payment_log = await PaymentLogRepo.get(db)
    return{
        "all_payment_log": all_payment_log
    }
    
@router.post("/paymentLog", dependencies=[Depends(JWTBearer())], tags=["Payment"])
async def add_payment_log(paymentLog_request: paymentSchema.PaymentLog, db: Session=Depends(get_db)):
    """
        Keep Payment Log for Users
    """
    
    payment_log = await PaymentLogRepo.create(db=db, paymentLog=paymentLog_request)
    return {
        "payment_log": payment_log
    }