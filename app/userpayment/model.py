from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey
from database import Base
from app.user.model import User

class UserPayment(Base):
    __tablename__ = "userpayments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(User.id))
    card_number = Column(String(30), nullable=False)
    card_holder_name = Column(String(30), nullable=False)
    expiration_date = Column(Date, nullable=False)
    cvc = Column(String(10), nullable=False)
    stripe_id = Column(String(80), nullable=False)
    created_at = Column(DateTime)
    default = Column(Boolean)
    
    def __repr__(self):
        return 'UserPayment()'