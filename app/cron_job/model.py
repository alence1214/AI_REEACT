from sqlalchemy import Column, Integer, DateTime, ForeignKey
from database import Base

from app.user.model import User

class CronHistory(Base):
    __tablename__ = "cronhistory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(User.id))
    total_search_result = Column(Integer)
    positive_search_result = Column(Integer)
    negative_search_result = Column(Integer)
    created_at = Column(DateTime)
    