from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from .model import PromoCode
from .schema import PromoCodeCreate
import datetime

class PromoCodeRepo:
    
    async def create(db: Session, promo_code: dict):
        try:
            db_promo_code = PromoCode(code_title=promo_code["code_title"],
                                      method=promo_code["method"],
                                      amount=promo_code["amount"],
                                      start_at=promo_code["start_at"],
                                      end_at=promo_code["end_at"],
                                      useage=0,
                                      stripe_id=promo_code["stripe_id"])
            db.add(db_promo_code)
            db.commit()
            db.refresh(db_promo_code)
            return db_promo_code
        except Exception as e:
            print("PromoCode Exception:", e)
            db.rollback()
            return False
        
    async def get_all(db: Session):
        try:
            result = db.query(PromoCode).all()
            return result
        except Exception as e:
            print("PromoCode Exception:", e)
            return False
    
    async def get_promocode_by_title(db: Session, code_title: str):
        try:
            result = db.query(PromoCode).filter(PromoCode.code_title == code_title).first()
            if result == None:
                return "Promocode doesn't exist."
            return result
        except Exception as e:
            print("PromoCode Exception:", e)
            return str(e)
        
    async def increase_useage(db: Session, promo_id: str):
        try:
            promocode = db.query(PromoCode).filter(PromoCode.code_title == promo_id).first()
            setattr(promocode, "useage", promocode.useage + 1)
            db.add(promocode)
            db.commit()
            db.refresh(promocode)
        except Exception as e:
            print("PromoCode Exception:", e)
            db.rollback()
            return False
        
    async def delete_by_id(db: Session, promo_id: int):
        try:
            result = db.query(PromoCode).filter(PromoCode.id == promo_id).delete()
            db.commit()
            return result
        except Exception as e:
            print("PromoCode Exception:", e)
            db.rollback()
            return str(e)
        
    async def get_stripe_id(db: Session, promo_id: int):
        try:
            stripe_id = db.query(PromoCode).filter(PromoCode.id == promo_id).first().stripe_id
            return stripe_id
        except Exception as e:
            print("PromoCode Exception:", e)
            return str(e)