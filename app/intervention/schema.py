from typing import Optional
from pydantic import BaseModel

class HandleIntervention(BaseModel):
    user_id: int
    title: str
    information: str
    additional_information: Optional[str] = None
    site_url: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    status: Optional[int] = 1