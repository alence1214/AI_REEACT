from typing import Optional
from pydantic import BaseModel

class HandleSearchIDList(BaseModel):
    user_id: int
    search_id: str
    keyword_url: str
    created_at: Optional[str]
    updated_at: Optional[str]