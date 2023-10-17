from typing import Optional
from pydantic import BaseModel

class PromoCodeSchema(BaseModel):
    code_title: str
    method: bool
    amount: float
    start_at: Optional[str]
    end_at: Optional[str] = None
    stripe_id: str
    
class PromoCodeCreate(PromoCodeSchema):
    code_title: str
    method: bool
    amount: float
    start_at: Optional[str]
    end_at: Optional[str]

class PromoCodeUpdate(PromoCodeSchema):
    pass