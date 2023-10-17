from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from database import get_db

from .repository import PromoCodeRepo
from app.auth.auth_bearer import JWTBearer, UserRoleBearer
from app.stripe_manager.stripe_manager import StripeManager

router = APIRouter()

@router.get("/admin/promocodes", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Promo"])
async def get_promocodes(db: Session=Depends(get_db)):
    result = await PromoCodeRepo.get_all(db)
    return result

@router.post("/admin/promocodes", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Promo"])
async def create_promocode(request: Request, db: Session=Depends(get_db)):
    promocode = await request.json()
    new_promo = await StripeManager.create_promo_code(promocode)
    if new_promo == None:
        raise HTTPException(status_code=403, detail="Pomo Code ID is None")
    new_promo_data = {
        "code_title": new_promo.code,
        "method": promocode["method"],
        "amount": promocode["amount"],
        "start_at": promocode["start_at"],
        "end_at": promocode["end_at"],
        "stripe_id": new_promo.stripe_id
    }
    new_promocode = await PromoCodeRepo.create(db, new_promo_data)
    return new_promocode

@router.post("/admin/promocodes/delete", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Promo"])
async def delete_promocode(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    promo_id = req_data["promo_id"]
    promo_stripe_id = await PromoCodeRepo.get_stripe_id(db, promo_id)
    if promo_stripe_id == False:
        raise HTTPException(status_code=403, detail='Promotion Code DB error.')
    stripe_res = await StripeManager.delete_promocode(promo_stripe_id)
    if stripe_res == False:
        raise HTTPException(status_code=403, detail='Promotion Code Stripe error.')
    result = await PromoCodeRepo.delete_by_id(db, promo_id)
    if result == False:
        raise HTTPException(status_code=403, detail='Promotion Code is not deleted.')
    return result