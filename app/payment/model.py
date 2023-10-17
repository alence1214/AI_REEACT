from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class Payment(Base):
    __tablename__ = "paymentlogs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    currency_type = Column(String(80))
    payment_type = Column(String(80))
    status = Column(String(80))
    created_at = Column(DateTime)
    def __repr__(self):
        return 'PaymentLogModel(user_id=%s, amount=%s, currency_type=%s, payment_type=%s, status=%s, created_at=%s)' % (self.user_id, self.amount, self.currency_type, self.payment_type, self.status, self.created_at)
    
