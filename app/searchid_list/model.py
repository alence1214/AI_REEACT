from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base
from app.user.model import User

class SearchIDList(Base):
    __tablename__ = "searchidlist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    search_id = Column(String(50), nullable=False)
    keyword_url = Column(String(500), nullable=False)
    additional_keyword_url = Column(String(255))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    stripe_id = Column(String(100))
    
    def __repr__(self) -> str:
        return "SearchIDList"