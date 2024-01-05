from sqlalchemy.orm import Session
from .model import EmailVerify
import datetime
from datetime import timedelta
import random

class EmailVerifyRepo:
    
    async def create(db: Session, emailverify: dict):
        try:
            created_at = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
            db_res = db.query(EmailVerify).filter(EmailVerify.email == emailverify["email"]).first()
            if not db_res:
                db_emailverify = EmailVerify(email=emailverify["email"],
                                            verify_code=emailverify["verify_code"],
                                            created_at=created_at)
                db.add(db_emailverify)
                db.commit()
                db.refresh(db_emailverify)
                return db_emailverify
            
            setattr(db_res, "verify_code", emailverify["verify_code"])
            setattr(db_res, "created_at", created_at)
            db.add(db_res)
            db.commit()
            db.refresh(db_res)
            return db_res
        except Exception as e:
            print("EmailVerify Create Failed:", e)
            db.rollback()
            return False
        
    async def delete(db: Session, email: str):
        try:
            res = db.query(EmailVerify).filter(EmailVerify.email == email).delete()
            db.commit()
            return res
        except Exception as e:
            print("EmailVerify Create Failed:", e)
            db.rollback()
            return False
        
    async def get_verify_code(db: Session, email: str):
        try:
            verify_code = db.query(EmailVerify).filter(EmailVerify.email == email).first().verify_code
            return verify_code
        except Exception as e:
            print("Getting Verify Code Failed:", e)
            return False
        
    async def check_verify_code(db: Session, email: str, verify_code: str):
        try:
            db_email_verify = db.query(EmailVerify).filter(EmailVerify.email == email).first()
            if db_email_verify == None:
                return "L'adresse e-mail n'existe pas."
            if db_email_verify.verify_code != verify_code:
                return "Code de vérification invalide."
            cur_time = datetime.datetime.now()
            verify_time = db_email_verify.created_at
            time_delta = cur_time - verify_time
            ten_minutes = timedelta(minutes=60)
            if time_delta > ten_minutes:
                new_verify_code = str(random.randint(100000, 999999))
                db.query(EmailVerify).filter(EmailVerify.email == email).\
                    update({EmailVerify.verify_code: new_verify_code,
                            EmailVerify.created_at: cur_time})
                db.commit()
                return "Code de vérification expiré."
            return True
        except Exception as e:
            print("Getting Verify Code Failed:", e)
            db.rollback()
            return str(e)