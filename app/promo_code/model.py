from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from database import Base

class PromoCode(Base):
    __tablename__ = "promocodes"
    
    id = Column(Integer, primary_key=True, index=True)
    code_title = Column(String(30), nullable=False)
    method = Column(Boolean)
    amount = Column(Float)
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    useage = Column(Integer)
    stripe_id = Column(String(80), nullable=False, index=True, unique=True)