from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from .model import CronHistory
import datetime

class CronHistoryRepo:
    async def create(db: Session, cronhistory_data: dict):
        try:
            created_at = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
            db_cronhistory = CronHistory(user_id=cronhistory_data["user_id"],
                                         total_search_result=cronhistory_data["total_search_result"],
                                         positive_search_result=cronhistory_data["positive_search_result"],
                                         negative_search_result=cronhistory_data["negative_search_result"],
                                         created_at = created_at)
            db.add(db_cronhistory)
            db.commit()
            db.refresh(db_cronhistory)
            return db_cronhistory
        except Exception as e:
            print("Cron History Exception:", e)
            return False
        
    async def get_history(db: Session, user_id: int):
        try:
            result = db.query(CronHistory).filter(CronHistory.user_id == user_id).limit(6).all()
            return result
        except Exception as e:
            print("Cron History Exception:", e)
            return False