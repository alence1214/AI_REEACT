from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from database import Base
from app.user.model import User

class InterventionRequest(Base):
    __tablename__ = "interventionrequests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(User.id))
    title = Column(String(255))
    information = Column(String(200), nullable=False)
    additional_information = Column(String(2000))
    site_url = Column(String(500), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    status = Column(Integer)
    admin_read_status = Column(Boolean)
    user_read_status = Column(Boolean)
    
    def __repr__(self):
        return 'InterventionRequests(information=%s, additional_information=%s, created_at=%s, updated_at=%s)' % (self.information, self.additional_information, self.created_at, self.updated_at)