from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from database import Base
from app.user.model import User

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_detail = Column(String(255))
    invoice_detail = Column(JSON)
    payment_method = Column(String(30))
    bill_from = Column(Integer, ForeignKey(User.id), nullable=False)
    bill_to = Column(Integer, ForeignKey(User.id), nullable=False)
    total_amount = Column(String(10), nullable=False)
    status = Column(String(255))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    stripe_id = Column(String(80))
    pdf_url = Column(String(255))
    
    def __repr__(self):
        return "Invoices"