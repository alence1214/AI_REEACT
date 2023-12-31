from sqlalchemy.orm import Session
from . import model, schema
import datetime

class PaymentLogRepo:
    
    async def create(db: Session, paymentLog: schema.PaymentLog):
        created_at = datetime.datetime.now()
        created_year = str(created_at.year)
        created_month = str(created_at.month)
        created_day = str(created_at.day)
        db_paymentLog = model.Payment(user_id=paymentLog.user_id, amount=paymentLog.amount, currency_type=paymentLog.currency_type, payment_type=paymentLog.payment_type, status=paymentLog.status, created_at=created_year+"-"+created_month+"-"+created_day)
        db.add(db_paymentLog)
        db.commit()
        db.refresh(db_paymentLog)
        return db_paymentLog
    
    async def get(db: Session):
        
        all_payment_log = db.query(model.Payment).all()
        return all_payment_log