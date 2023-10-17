from sqlalchemy import extract, or_, and_
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from . import model, schema
import datetime

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

class UserRepo:
    
    async def create(db: Session, user: dict):
        try:
            hashed_password = get_password_hash(user['password'])
            created_at = datetime.datetime.now()
            created_year = str(created_at.year)
            created_month = str(created_at.month)
            created_day = str(created_at.day)
            user["google_id"] = user["google_id"] if "google_id" in user else ""
            user["payment_verified"] = user["payment_verified"] if "payment_verified" in user else False
            user["email_verified"] = True #user["email_verified"] if "email_verified" in user else False
            user["avatar_url"] = user["avatar_url"] if "avatar_url" in user else "static/avatar.png"
            user["social_reason"] = user["social_reason"] if "social_reason" in user else ""
            user["number_siret"] = user["number_siret"] if "number_siret" in user else ""
            user["vat_number"] = user["vat_number"] if "vat_number" in user else ""
            user["activity"] = user["activity"] if "activity" in user else ""
            db_user = model.User(email=user['email'],
                                full_name=user['full_name'], 
                                password=hashed_password,
                                social_reason=user["social_reason"],
                                activity=user["activity"],
                                number_siret=user["number_siret"],
                                vat_number=user["vat_number"],
                                address=user["address"],
                                postal_code=user["postal_code"],
                                province=user["province"],
                                pays=user["pays"],
                                phone=user["phone"],
                                site_internet=user["site_internet"],
                                google_id=user["google_id"],
                                payment_verified=user["email_verified"],
                                email_verified=user["payment_verified"],
                                subscription_at=user["subscription_at"],
                                created_at=created_year+"-"+created_month+"-"+created_day, 
                                subscription_expired=True, 
                                role=user["role"],
                                avatar_url=user["avatar_url"],
                                user_type=user["user_type"],
                                forgot_password_token="")
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
    
    async def get_all_user(db: Session):
        try:
            user = db.query(model.User.id,
                        model.User.full_name,
                        model.User.social_reason,
                        model.User.email,
                        model.User.province,
                        model.User.subscription_at).all()
            return user
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
        
    async def get_active_users(db: Session):
        try:
            user = db.query(model.User.id,
                        model.User.full_name,
                        model.User.social_reason,
                        model.User.email,
                        model.User.province,
                        model.User.subscription_at).\
                        filter(model.User.subscription_at != None).all()
            return user
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
        
    async def get_active_user_count(db: Session):
        try:
            count = db.query(model.User).filter(model.User.subscription_at != None).count()
            return count
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
    
    async def get_user_by_id(db: Session, user_id:  int):
        try:
            user = db.query(model.User).filter(model.User.id == user_id).first()
            return user
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
    
    async def get_user_role(db: Session, id):
        try:
            user = db.query(model.User).filter(model.User.id == id).first()
            user_role = user.role
            return user_role
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
    
    async def fetch_by_email(db: Session, email):
        try:
            return db.query(model.User).filter(model.User.email == email).first()
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
    
    async def fetch_by_email_password(db: Session, email, password):
        try:
            print("Received Data", email, password)
            user = db.query(model.User).filter(model.User.email == email).first()
            print("Selected User:", user)
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
        if not user:
            return "User not exist"
        if not verify_password(password, user.password):
            return "Password is not correct"
        return user
    
    async def update_user_by_id(db: Session, user: schema.UserUpdate, id: int):
        try:
            db_user = db.query(model.User).filter(model.User.id == id).first()
            if not db_user:
                return "User not exist to update"
            user_role = db_user.role
            # Update Model Class Variable from requestedd fields
            for var, value in vars(user).items():
                print(var, value)
                if (var == "password"):
                    hashed_updated_pass = get_password_hash(value)
                    setattr(db_user, var, hashed_updated_pass)
                if not (var == "password"):
                    setattr(db_user, var, value) if value else None
                    
            if user_role == 0 or user_role == 1:
                setattr(db_user, "role", user_role)
                
            updated_at = datetime.datetime.now()
            updated_year = str(updated_at.year)
            updated_month = str(updated_at.month)
            updated_day = str(updated_at.day)
            
            db_user.updated_at = updated_year+"-"+updated_month+"-"+updated_day
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
    
    async def get_subscription_id(db: Session, user_id: int):
        try:
            user = db.query(model.User).filter(model.User.id == user_id).first()
            subscription_id = user.subscription_at
            return subscription_id
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
        
    async def get_total_count(db: Session):
        try:
            total_count = db.query(model.User).filter(model.User.role == 2).count()
            return total_count
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
        
    async def get_monthly_acc_count(db: Session, month: int):
        try:
            acc_count = db.query(model.User).filter(and_(extract('month', model.User.created_at) == month, model.User.role == 2)).count()
            return acc_count
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
        
    async def get_daily_acc_data(db: Session):
        try:
            cur_time = datetime.datetime.now()
            cur_day = cur_time.day
            cur_month = cur_time.month
            cur_year = cur_time.year
            cur_week_day = cur_time.weekday()
            daily_acc_count = []
            for i in range(cur_day-cur_week_day, cur_day+1):
                inscription_cnt = db.query(model.User).\
                    filter(and_(extract("day", model.User.created_at) == i,
                                extract("month", model.User.created_at) == cur_month,
                                extract("year", model.User.created_at) == cur_year,
                                model.User.subscription_at != None)).count()
                unscription_cnt = db.query(model.User).\
                    filter(and_(extract("day", model.User.created_at) == i,
                                extract("month", model.User.created_at) == cur_month,
                                extract("year", model.User.created_at) == cur_year,
                                model.User.subscription_at == None)).count()
                daily_acc_count.append({
                    "inscription": inscription_cnt,
                    "unscription_cnt": unscription_cnt
                })
            return daily_acc_count
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
    
    async def get_weekly_acc_data(db: Session):
        try:
            cur_date = datetime.date.today()
            cur_month = cur_date.month
            cur_year = cur_date.year
            cur_week = cur_date.weekday()
            first_day_of_month = datetime.date(cur_date.year, cur_date.month, 1)
            week_first_day = first_day_of_month.weekday()
            days = (cur_date - first_day_of_month).days
            weeks = days // 7
            
            weekly_acc_data = []
            for i in range(weeks + 2):
                start_date = first_day_of_month + datetime.timedelta(days=0 if i == 0 else 7 * i - week_first_day)
                start_day = start_date.day
                end_date = start_date + datetime.timedelta(days=6-week_first_day if i == 0 else 6)
                end_date = end_date if end_date <= cur_date else end_date - datetime.timedelta(days=6-cur_week)
                end_day = end_date.day
                
                inscription_cnt = db.query(model.User).\
                    filter(and_(end_day >= extract("day", model.User.created_at),
                                extract("day", model.User.created_at) >= start_day,
                                extract("month", model.User.created_at) == cur_month,
                                extract("year", model.User.created_at) == cur_year,
                                model.User.subscription_at != None)).count()
                unscription_cnt = db.query(model.User).\
                    filter(and_(end_day >= extract("day", model.User.created_at),
                                extract("day", model.User.created_at) >= start_day,
                                extract("month", model.User.created_at) == cur_month,
                                extract("year", model.User.created_at) == cur_year,
                                model.User.subscription_at == None)).count()
                weekly_acc_data.append({
                    "inscription": inscription_cnt,
                    "unscription_cnt": unscription_cnt
                })
            return weekly_acc_data
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
        
    async def get_monthly_acc_data(db: Session):
        try:
            cur_time = datetime.datetime.now()
            cur_month = cur_time.month
            cur_year = cur_time.year
            monthly_acc_count = []
            for i in range(1, cur_month + 1):
                inscription_cnt = db.query(model.User).\
                    filter(and_(extract("month", model.User.created_at) == i,
                                extract("year", model.User.created_at) == cur_year,
                                model.User.subscription_at != None)).count()
                unscription_cnt = db.query(model.User).\
                    filter(and_(extract("month", model.User.created_at) == i,
                                extract("year", model.User.created_at) == cur_year,
                                model.User.subscription_at == None)).count()
                monthly_acc_count.append({
                    "inscription": inscription_cnt,
                    "unscription_cnt": unscription_cnt
                })
            return monthly_acc_count
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
        
    async def check_password_forgot_token(db: Session, token: str):
        try:
            db_user = db.query(model.User).filter(model.User.forgot_password_token == token).first()
            if db_user:
                return True
            return False
        except Exception as e:
            print("UserRepo Exception:", e)
            return False
        
    async def add_forgot_password_token(db: Session, user_id: int, token: str):
        try:
            db.query(model.User).filter(model.User.id == user_id).\
                update({model.User.forgot_password_token: token})
            db.commit()
            return True
        except Exception as e:
            print("UserRepo Exception:", e)
            return False