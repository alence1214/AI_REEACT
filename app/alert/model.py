from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from database import Base
from app.user.model import User

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(User.id))
    search_id = Column(String(60))
    title = Column(String(255))
    site_url = Column(String(255))
    label = Column(String(20))
    read_status = Column(Boolean)
    created_at = Column(DateTime)
    
    def __repr__(self) -> str:
        return f"""Alert(id={self.id},
                        user_id={self.user_id},
                        search_id={self.search_id},
                        title={self.title},
                        site_url={self.site_url},
                        label={self.label},
                        read_state={self.read_status},
                        created_at={self.created_at}
                        )
    """
    
class AlertSetting(Base):
    __tablename__ = "alertsetting"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(User.id))
    positive = Column(Boolean)
    negative = Column(Boolean)
    netural = Column(Boolean)
    search_engine = Column(Boolean)
    blog = Column(Boolean)
    social_networks = Column(Boolean)
    email = Column(Boolean)
    sms = Column(Boolean)
    contact_frequency = Column(Integer)