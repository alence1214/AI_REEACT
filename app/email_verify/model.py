from sqlalchemy import Column, String, DateTime, Integer
from database import Base

class EmailVerify(Base):
    __tablename__ = "emailverify"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(50), index=True)
    verify_code = Column(String(6))
    created_at = Column(DateTime)