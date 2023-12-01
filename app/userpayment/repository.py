from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from . import model, schema
import datetime

class UserPaymentRepo:
    
    async def create(db: Session, userpayment: dict, user_id: int):
        try:
            try:
                expiration_date = datetime.datetime.strptime(userpayment['expiration_date'], "%m/%y")
            except Exception as er:
                print(er)
                expiration_date = datetime.datetime.strptime("12/23", "%m/%y")
            created_at = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
            db_userpayment = model.UserPayment(user_id=user_id,
                                            card_number=userpayment['card_number'],
                                            card_holder_name=userpayment['card_holdername'],
                                            expiration_date=expiration_date,
                                            cvc=userpayment['cvc'],
                                            stripe_id=userpayment['payment_method_id'],
                                            created_at=created_at,
                                            default=False)
            db.add(db_userpayment)
            db.commit()
            db.refresh(db_userpayment)
            return db_userpayment
        except Exception as e:
            print("UserPaymentRepo Exception:", e)
            db.rollback()
            return False
        
    async def delete(db: Session, card_id: int):
        try:
            res = db.query(model.UserPayment).filter(model.UserPayment.id == card_id).delete()
            db.commit()
            return res
        except Exception as e:
            print("UserPaymentRepo Exception:", e)
            db.rollback()
            return False
        
    async def check_valid_card(db: Session, user_id: int, card_id: int):
        try:
            selection = db.query(model.UserPayment).\
                            filter(and_(model.UserPayment.user_id == user_id,
                                        model.UserPayment.id == card_id)).first()
            if selection:
                return True
            return False
        except Exception as e:
            print("UserPaymentRepo Exception:", e)
            return False
    
    async def is_default_card(db: Session, user_id: int, card_id: int):
        try:
            selection = db.query(model.UserPayment).\
                            filter(and_(model.UserPayment.user_id == user_id,
                                        model.UserPayment.id == card_id)).first()
            if selection.default:
                return True
            return False
        except Exception as e:
            print("UserPaymentRepo Exception:", e)
            return False
    
    async def get_default_card(db: Session, user_id: int):
        try:
            card_data = db.query(model.UserPayment).filter(and_(model.UserPayment.user_id == user_id,
                                                                model.UserPayment.default == True)).first()
            card_data.card_number = '*' * 12 + card_data.card_number[-4:]
            card_data.cvc = '***'
            return card_data
        except Exception as e:
            print("UserPaymentRepo Exception:", e)
            return False
        
    async def get_payment_by_user_id(db: Session, user_id: int):
        try:
            res = db.query(model.UserPayment).filter(model.UserPayment.user_id == user_id).all()
            payment_data = []
            for payment in res:
                print(payment)
                payment.card_number = '*' * 12 + payment.card_number[-4:]
                payment.cvc = '***'
                payment.stripe_id = "unknown"
                payment_data.append(payment)
            return payment_data
        except Exception as e:
            print("UserPaymentRepo Exception:", e)
            return False
    
    async def get_default_payment_by_user_id(db: Session, user_id: int):
        try:
            res = db.query(model.UserPayment).filter(and_(model.UserPayment.user_id == user_id,
                                                          model.UserPayment.default == True)).first()

            res.card_number = '*' * 12 + res.card_number[-4:]
            res.cvc = '***'
            res.stripe_id = "unknown"
            return res
        except Exception as e:
            print("UserPaymentRepo Exception:", e)
            return False
    
    async def set_as_default(db: Session, user_id: int, card_id: int):
        try:
            db.query(model.UserPayment).\
                filter(model.UserPayment.user_id == user_id).\
                update({model.UserPayment.default: False})
            db.commit()
            db.query(model.UserPayment).\
                filter(and_(model.UserPayment.user_id == user_id,
                            model.UserPayment.id == card_id)).\
                update({model.UserPayment.default: True})
            db.commit()
            return True
        except Exception as e:
            print("UserPaymentRepo Exception:", e)
            db.rollback()
            return False
        
    async def get_stripe_id(db: Session, card_id: int):
        try:
            stripe_id = db.query(model.UserPayment).filter(model.UserPayment.id == card_id).first().stripe_id
            return stripe_id
        except Exception as e:
            print("UserPaymentRepo Exception:", e)
            return False