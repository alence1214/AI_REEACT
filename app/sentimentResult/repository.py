from sqlalchemy.orm import Session
from sqlalchemy import func
from . import model, schema
import app.googleSearchResult.model as googleSearchResult
import datetime

class SentimentResult:
    
    async def create(db: Session, sentimentResult: schema.SentimentResult):
        try:
            db_sentiment_result = db.query(model.SentimentResult).filter(model.SentimentResult.keyword == sentimentResult['keyword']).first()
            
            if not db_sentiment_result:
                created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                db_sentimentResult = model.SentimentResult(keyword=sentimentResult['keyword'], label=sentimentResult['label'], score=sentimentResult['score'], created_at=created_at)
                db.add(db_sentimentResult)
                db.commit()
                db.refresh(db_sentimentResult)
                
                return "Sentiment Result Item saved successfully!!!"
            
            setattr(db_sentiment_result, 'label', sentimentResult['label'])
            setattr(db_sentiment_result, 'score', sentimentResult['score'])
            
            db_sentiment_result.updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            db.add(db_sentiment_result)
            db.commit()
            db.refresh(db_sentiment_result)
            
            return "Sentiment Result Item updated successfully!!!"
        except Exception as e:
            print("Sentiment Result Exception:", e)
            db.rollback()
            return False
    
    async def get(db: Session, page: int, limit: int):
        
        skip = (page - 1) * limit
        
        # notes = db.query(models.Note).filter(models.Note.title.contains(search)).limit(limit).offset(skip).all()
        
        db_search_result = []
        
        db_sentiment_result = db.query(model.SentimentResult).limit(limit).offset(skip).all()
        
        db_googlesearch_result = db.query(googleSearchResult.GoogleSearchResult).all()
        
        count = 0
        
        while (count < len(db_sentiment_result)):
            
            sub_count = 0
            
            while(sub_count < len(db_googlesearch_result)):
                
                if(db_sentiment_result[count].keyword == db_googlesearch_result[sub_count].snippet):
                    db_search_result.append({
                        "label": db_sentiment_result[count].label,
                        "title": db_googlesearch_result[sub_count].title,
                        "link": db_googlesearch_result[sub_count].link,
                        "snippet": db_googlesearch_result[sub_count].snippet,
                        "created_at": db_sentiment_result[count].created_at,
                        "updated_at": db_sentiment_result[count].updated_at
                    })
                    
                sub_count = sub_count + 1
                
            count = count + 1
            
        
        return db_search_result
        
        
            