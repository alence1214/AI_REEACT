from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from database import Base
from app.user.model import User
from app.intervention.model import InterventionRequest

class InterventionResponse(Base):
    __tablename__ = "interventionresponses"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey(InterventionRequest.id), nullable=False)
    response_type = Column(Integer, nullable=False)
    response = Column(String(500), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    status = Column(Boolean, nullable=False)
    respond_to = Column(Integer, nullable=False)
    
    def __repr__(self) -> str:
        return "InterventionResponse"