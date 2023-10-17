from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Boolean
from database import Base
from app.user.model import User

class Messaging(Base):
    __tablename__ = "messaging"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_selection = Column(String(50), nullable=False)
    object_for = Column(String(30), nullable=False)
    messaging = Column(String(2000), nullable=False)
    attachments = Column(JSON)
    parent_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    message_to = Column(Integer, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    admin_read_status = Column(Boolean, nullable=False)
    user_read_status = Column(Boolean, nullable=False)
    def __repr__(self):
        return 'Messaging(messaging=%s, created_at=%s, updated_at=%s)' % (self.messaging, self.created_at, self.updated_at)