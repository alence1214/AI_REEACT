from typing import Optional
from pydantic import BaseModel

class UserPaymentBase(BaseModel):
    user_id: Optional[int]
    card_number: Optional[str]
    card_holder_name: Optional[str]
    expiration_date: Optional[str]
    cvc: Optional[str]
    stripe_id: Optional[str]
    
class UserPaymentCreate(UserPaymentBase):
    pass

class UserPaymentUpdate(UserPaymentBase):
    pass

class UserPaymentDelete(UserPaymentBase):
    pass
