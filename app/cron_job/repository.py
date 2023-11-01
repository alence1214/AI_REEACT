from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, extract
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
        
    async def update(db: Session, user_id: int, cronhistory_data: dict):
        try:
            cur_month = datetime.datetime.today().month
            cur_year = datetime.datetime.today().year
            created_at = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
            select = db.query(CronHistory).\
                filter(and_(CronHistory.user_id == user_id,
                            extract("month", CronHistory.created_at) == cur_month,
                            extract("year", CronHistory.created_at) == cur_year)).\
                update({CronHistory.total_search_result: cronhistory_data["total_search_result"],
                        CronHistory.positive_search_result: cronhistory_data["positive_search_result"],
                        CronHistory.negative_search_result: cronhistory_data["negative_search_result"],
                        CronHistory.created_at: created_at}, synchronize_session='fetch')
            db.commit()
            print(select)
            return select
        except Exception as e:
            print("Cron History Exception:", e)
            return False
        
    async def get_history(db: Session, user_id: int):
        try:
            result = db.query(CronHistory).\
                        filter(CronHistory.user_id == user_id).\
                        order_by(CronHistory.created_at.asc()).\
                        limit(6).all()
            return result
        except Exception as e:
            print("Cron History Exception:", e)
            return False
    
    async def get_reputation_score(db: Session, user_id: int):
        try:
            today = datetime.date.today()
            cur_month = today.month
            cur_year = today.year
            pre_month = cur_month-1 if cur_month>1 else 12
            pre_year = cur_year if cur_month>1 else cur_year-1
            cur_month_score = db.query(CronHistory).filter(and_(CronHistory.user_id == user_id,
                                                       extract("month", CronHistory.created_at) == cur_month,
                                                       extract("year", CronHistory.created_at) == cur_year)).first()
            pre_month_score = db.query(CronHistory).filter(and_(CronHistory.user_id == user_id,
                                                       extract("month", CronHistory.created_at) == pre_month,
                                                       extract("year", CronHistory.created_at) == pre_year)).first()
            if not cur_month_score:
                return {
                    "positive_raisen": 0,
                    "negative_raisen": 0,
                    "general_raisen": 0
                }
            if not pre_month_score:
                return {
                    "positive_raisen": round(cur_month_score.positive_search_result / cur_month_score.total_search_result * 100, 2),
                    "negative_raisen": round(cur_month_score.negative_search_result / cur_month_score.total_search_result * 100, 2),
                    "general_raisen": round((cur_month_score.total_search_result-cur_month_score.negative_search_result) / cur_month_score.total_search_result * 100, 2)
                }
            return {
                "positive_raisen": round(((cur_month_score.positive_search_result / cur_month_score.total_search_result * 100) - (pre_month_score.positive_search_result / pre_month_score.total_search_result * 100)), 2),
                "negative_raisen": round(((cur_month_score.negative_search_result / cur_month_score.total_search_result * 100) - (pre_month_score.negative_search_result / pre_month_score.total_search_result * 100)), 2),
                "general_raisen": round(((cur_month_score.total_search_result-cur_month_score.negative_search_result) / cur_month_score.total_search_result * 100) - ((pre_month_score.total_search_result-pre_month_score.negative_search_result) / pre_month_score.total_search_result * 100), 2)
            }
        except Exception as e:
            print("get_reputation_score:", e)
            return False