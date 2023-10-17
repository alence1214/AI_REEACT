from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base

class SentimentResult(Base):
    __tablename__ = "sentimentresults"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(2000), nullable=False)
    label = Column(String(80), nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    def __repr__(self):
        return 'SentimentResults(keyword=%s, label=%s, score=%s, created_at=%s, updated_at=%s)' % (self.keyword, self.label, self.score, self.created_at, self.updated_at)