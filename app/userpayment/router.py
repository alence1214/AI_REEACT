from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from tools import get_user_id

from .repository import UserPaymentRepo
from app.auth.auth_bearer import JWTBearer
from app.user.repository import UserRepo
from app.stripe_manager.stripe_manager import StripeManager

router = APIRouter()

@router.post("/add_new_card", dependencies=[Depends(JWTBearer())], tags=["User"])
async def add_new_card(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    req_data = await request.json()
    card_id = req_data["payment_data"]
    customer_id = await UserRepo.get_user_stripe_id(db, user_id)
    
    new_payment_method = await StripeManager.link_payment_method_to_customer(customer_id, card_id.get("pm_id"))
    if type(new_payment_method) == str:
        raise HTTPException(status_code=403, detail=new_payment_method)
    
    set_default_payment_method = await StripeManager.set_default_payment_method(customer_id, card_id.get("pm_id"))
    
    if type(set_default_payment_method) == str:
        raise HTTPException(status_code=403, detail=set_default_payment_method)
    
    card_data = await StripeManager.get_card_data_by_id(card_id.get("pm_id"))
    if type(card_data) == str:
        raise HTTPException(status_code=403, detail="Impossible d'obtenir les données de la carte.")
    
    card_data["card_holdername"] = card_id.get("card_holdername")
    
    created_payment = await UserPaymentRepo.create(db=db, userpayment=card_data, user_id=user_id)
    if created_payment == False:
        raise HTTPException(status_code=403, detail="Erreur de base de données de paiement.")
    set_default = await UserPaymentRepo.set_as_default(db, user_id, created_payment.id)
    if not set_default:
        raise HTTPException(status_code=403, detail="Échec du paiement par défaut.")
    return created_payment

@router.post("/delete_card", dependencies=[Depends(JWTBearer())], tags=["User"])
async def delete_card(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    req_data = await request.json()
    card_id = req_data["card_id"]
    check_valid = await UserPaymentRepo.check_valid_card(db, user_id, card_id)
    if check_valid == False:
        raise HTTPException(status_code=403, detail="Requête invalide.")
    is_default = await UserPaymentRepo.is_default_card(db, user_id, card_id)
    if is_default:
        raise HTTPException(status_code=403, detail="La carte par défaut ne peut pas être supprimée !")
    card_stripe_id = await UserPaymentRepo.get_stripe_id(db, card_id)
    if card_stripe_id == False:
        raise HTTPException(status_code=403, detail="Impossible d'obtenir l'identifiant Stripe.")
    delete_from_stripe = await StripeManager.delete_payment_method(card_stripe_id)
    if delete_from_stripe == False:
        raise HTTPException(status_code=403, detail="Impossible de retirer la carte de Stripe.")
    delete_from_db = await UserPaymentRepo.delete(db, card_id)
    if delete_from_db == False or delete_from_db == 0:
        raise HTTPException(status_code=403, detail="Impossible de retirer la carte de la base de données.")
    return "Card deleted successfully."

@router.post("/set_default_card", dependencies=[Depends(JWTBearer())], tags=["User"])
async def set_default_card(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    req_data = await request.json()
    card_id = req_data["card_id"]
    
    check_valid = await UserPaymentRepo.check_valid_card(db, user_id, card_id)
    if not check_valid:
        raise HTTPException(status_code=403, detail="Demande non valide.")
    
    card_stripe_id = await UserPaymentRepo.get_stripe_id(db, card_id)
    
    customer_id = await UserRepo.get_user_stripe_id(db, user_id)
    
    set_default_payment_method = await StripeManager.set_default_payment_method(customer_id, card_stripe_id)
    if not set_default_payment_method:
        raise HTTPException(status_code=403, detail="Échec du mode de paiement par défaut défini par Stripe.")
    
    set_default = await UserPaymentRepo.set_as_default(db, user_id, card_id)
    if set_default == False:
        raise HTTPException(status_code=403, detail="Échec du paiement par défaut.")

    return set_default
    
@router.get("/all_payment_methods", dependencies=[Depends(JWTBearer())], tags=["User"])
async def get_all_payment_method(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    payment_methods = await UserPaymentRepo.get_payment_by_user_id(db, user_id)
    if payment_methods == False:
        raise HTTPException(status_code=403, detail="Impossible d'obtenir les modes de paiement.")
    return payment_methods
