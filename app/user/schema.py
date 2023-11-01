from typing import Optional
from pydantic import EmailStr
from pydantic import BaseModel

class UserBase(BaseModel):
    email: Optional[EmailStr]
    full_name: Optional[str]
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str]
    social_reason: Optional[str] = None
    activity: Optional[str] = None
    number_siret: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    province: Optional[str] = None
    pays: Optional[str] = None
    phone: Optional[str] = None
    site_internet: Optional[str] = None
    google_id: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
    payment_verified: Optional[bool] = None
    email_verified: Optional[bool] = None
    subscription_at: Optional[str] = None
    subscription_expired: Optional[int] = None # 1-True 2-False
    role: Optional[int] = 2 # 1-Admin 2-User
    avatar_url: Optional[str] = "static/avatar.png"
    user_type: Optional[str] = "Particulier"
    forgot_password_token: Optional[str] = None
    
class UserCreate(UserBase):
    pass

class UserUpdate(UserBase):
    pass

class UserLogin(BaseModel):
    email: str
    password: str