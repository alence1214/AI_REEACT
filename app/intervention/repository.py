from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, extract
from . import model, schema
import datetime
from app.user.model import User
from app.intervention_response.model import InterventionResponse
from app.googleSearchResult.model import GoogleSearchResult
from app.sentimentResult.model import SentimentResult

class InterventionRepo:
    
    async def create(db: Session, intervention: dict, user_id: int):
        try:
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            db_intervention = model.InterventionRequest(user_id=user_id,
                                                        title=intervention["title"],
                                                        information=intervention["information"],
                                                        additional_information=intervention["additional_information"],
                                                        site_url=intervention["site_url"],
                                                        created_at=created_at,
                                                        updated_at=created_at,
                                                        status=0,
                                                        admin_read_status=False,
                                                        user_read_status=True)
            db.add(db_intervention)
            db.commit()
            db.refresh(db_intervention)
            return db_intervention
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
    
    async def get(db: Session):
        try:
            results = db.query(model.InterventionRequest).all()
            return results
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
    
    async def get_all_interventions(db: Session):
        try:
            results = db.query(model.InterventionRequest.id,
                               model.InterventionRequest.user_id,
                            User.full_name,
                            model.InterventionRequest.title,
                            model.InterventionRequest.information,
                            model.InterventionRequest.updated_at,
                            model.InterventionRequest.site_url,
                            model.InterventionRequest.status,
                            model.InterventionRequest.admin_read_status,
                            model.InterventionRequest.user_read_status).\
                        join(User, model.InterventionRequest.user_id == User.id).\
                        order_by(model.InterventionRequest.updated_at.desc()).all()
            return results
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        
    async def get_inter_by_id(db: Session, inter_id: int):
        try:
            result = db.query(model.InterventionRequest.id,
                              model.InterventionRequest.user_id,
                            User.full_name,
                            model.InterventionRequest.title,
                            model.InterventionRequest.information,
                            model.InterventionRequest.additional_information,
                            InterventionResponse.response,
                            model.InterventionRequest.updated_at,
                            model.InterventionRequest.site_url,
                            model.InterventionRequest.status,
                            model.InterventionRequest.admin_read_status,
                            model.InterventionRequest.user_read_status).\
                        join(User, model.InterventionRequest.user_id == User.id).\
                        join(InterventionResponse, InterventionResponse.request_id == model.InterventionRequest.id, isouter=True).\
                        filter(model.InterventionRequest.id == inter_id).\
                        order_by(InterventionResponse.created_at.asc()).first()
            return result
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
    
    async def get_all_intervention_in_progress(db: Session):
        try:
            result = db.query(model.InterventionRequest.id,
                              model.InterventionRequest.user_id,
                            User.full_name,
                            model.InterventionRequest.title,
                            model.InterventionRequest.information,
                            model.InterventionRequest.updated_at,
                            model.InterventionRequest.site_url,
                            model.InterventionRequest.status,
                            model.InterventionRequest.admin_read_status,
                            model.InterventionRequest.user_read_status).\
                        join(User, model.InterventionRequest.user_id == User.id).\
                        filter(model.InterventionRequest.status == 1).\
                        order_by(model.InterventionRequest.updated_at.desc()).all()
            return result
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        
    async def get_all_intervention_in_pending(db):
        try:
            result = db.query(model.InterventionRequest.id,
                              model.InterventionRequest.user_id,
                            User.full_name,
                            model.InterventionRequest.title,
                            model.InterventionRequest.information,
                            model.InterventionRequest.updated_at,
                            model.InterventionRequest.site_url,
                            model.InterventionRequest.status,
                            model.InterventionRequest.admin_read_status,
                            model.InterventionRequest.user_read_status).\
                        join(User, model.InterventionRequest.user_id == User.id).\
                        filter(model.InterventionRequest.status == 2).\
                        order_by(model.InterventionRequest.updated_at.desc()).all()
            return result
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
    
    async def get_user_id(db: Session, intervention_id):
        try:
            result = db.query(model.InterventionRequest).filter(model.InterventionRequest.id == intervention_id).first()
            user_id = result.user_id
            return user_id
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
    
    async def get_by_user_id(db: Session, user_id: int):
        try:
            interventions = db.query(model.InterventionRequest.id,
                                     model.InterventionRequest.user_id,
                                     model.InterventionRequest.title,
                                     model.InterventionRequest.information,
                                     model.InterventionRequest.additional_information,
                                     model.InterventionRequest.updated_at,
                                     model.InterventionRequest.site_url,
                                     model.InterventionRequest.status,
                                     model.InterventionRequest.admin_read_status,
                                     model.InterventionRequest.user_read_status,
                                     SentimentResult.label).\
                join(GoogleSearchResult, and_(model.InterventionRequest.title == GoogleSearchResult.title, 
                                              model.InterventionRequest.site_url == GoogleSearchResult.link)).\
                join(SentimentResult, GoogleSearchResult.snippet == SentimentResult.keyword).\
                filter(model.InterventionRequest.user_id == user_id).\
                order_by(model.InterventionRequest.updated_at.desc()).all()
            return interventions
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False

    async def get_daily_intervention_data_by_user_id(db: Session, user_id: int):
        try:
            cur_date = datetime.date.today()
            cur_day = cur_date.day
            cur_month = cur_date.month
            cur_year = cur_date.year
            # interventions = db.query(model.InterventionRequest.id,
            #                          model.InterventionRequest.information,
            #                          model.InterventionRequest.additional_information,
            #                          model.InterventionRequest.updated_at,
            #                          model.InterventionRequest.site_url,
            #                          model.InterventionRequest.status,
            #                          SentimentResult.label).\
            #                     join(GoogleSearchResult, and_(model.InterventionRequest.information == GoogleSearchResult.title, 
            #                                                 model.InterventionRequest.site_url == GoogleSearchResult.link)).\
            #                     join(SentimentResult, GoogleSearchResult.snippet == SentimentResult.keyword).\
            #                     filter(and_(extract("day", model.InterventionRequest.created_at) == cur_day,
            #                                 extract("month", model.InterventionRequest.created_at) == cur_month,
            #                                 extract("year", model.InterventionRequest.created_at) == cur_year,
            #                                 model.InterventionRequest.user_id == user_id)).\
            #                     order_by(model.InterventionRequest.updated_at.desc()).all()

            interventions = db.query(model.InterventionRequest.id,
                                     model.InterventionRequest.user_id,
                                     model.InterventionRequest.title,
                                     model.InterventionRequest.information,
                                     model.InterventionRequest.additional_information,
                                     model.InterventionRequest.updated_at,
                                     model.InterventionRequest.site_url,
                                     model.InterventionRequest.status,
                                     model.InterventionRequest.admin_read_status,
                                     model.InterventionRequest.user_read_status).\
                                filter(and_(extract("day", model.InterventionRequest.created_at) == cur_day,
                                            extract("month", model.InterventionRequest.created_at) == cur_month,
                                            extract("year", model.InterventionRequest.created_at) == cur_year,
                                            model.InterventionRequest.user_id == user_id)).\
                                order_by(model.InterventionRequest.updated_at.desc()).all()
            return interventions
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        
    async def get_weekly_intervention_data_by_user_id(db: Session, user_id: int):
        try:
            cur_date = datetime.date.today()
            cur_weekday = cur_date.weekday()
            cur_day = cur_date.day
            cur_month = cur_date.month
            cur_year = cur_date.year
            start_cur_week = cur_day - cur_weekday
            # interventions = db.query(model.InterventionRequest.id,
            #                          model.InterventionRequest.information,
            #                          model.InterventionRequest.additional_information,
            #                          model.InterventionRequest.updated_at,
            #                          model.InterventionRequest.site_url,
            #                          model.InterventionRequest.status,
            #                          SentimentResult.label).\
            #                     join(GoogleSearchResult, and_(model.InterventionRequest.information == GoogleSearchResult.title, 
            #                                                 model.InterventionRequest.site_url == GoogleSearchResult.link)).\
            #                     join(SentimentResult, GoogleSearchResult.snippet == SentimentResult.keyword).\
            #                     filter(and_(extract("day", model.InterventionRequest.created_at) <= cur_day,
            #                                 extract("day", model.InterventionRequest.created_at) >= start_cur_week,
            #                                 extract("month", model.InterventionRequest.created_at) == cur_month,
            #                                 extract("year", model.InterventionRequest.created_at) == cur_year,
            #                                 model.InterventionRequest.user_id == user_id)).\
            #                     order_by(model.InterventionRequest.updated_at.desc()).all()

            interventions = db.query(model.InterventionRequest.id,
                                     model.InterventionRequest.user_id,
                                     model.InterventionRequest.title,
                                     model.InterventionRequest.information,
                                     model.InterventionRequest.additional_information,
                                     model.InterventionRequest.updated_at,
                                     model.InterventionRequest.site_url,
                                     model.InterventionRequest.status,
                                     model.InterventionRequest.admin_read_status,
                                     model.InterventionRequest.user_read_status).\
                                filter(and_(extract("day", model.InterventionRequest.created_at) <= cur_day,
                                            extract("day", model.InterventionRequest.created_at) >= start_cur_week,
                                            extract("month", model.InterventionRequest.created_at) == cur_month,
                                            extract("year", model.InterventionRequest.created_at) == cur_year,
                                            model.InterventionRequest.user_id == user_id)).\
                                order_by(model.InterventionRequest.updated_at.desc()).all()
            print(interventions)
            return interventions
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        
    async def get_monthly_intervention_data_by_user_id(db: Session, user_id: int):
        try:
            cur_date = datetime.date.today()
            cur_month = cur_date.month
            cur_year = cur_date.year
            # interventions = db.query(model.InterventionRequest.id,
            #                          model.InterventionRequest.information,
            #                          model.InterventionRequest.additional_information,
            #                          model.InterventionRequest.updated_at,
            #                          model.InterventionRequest.site_url,
            #                          model.InterventionRequest.status,
            #                          SentimentResult.label).\
            #                     join(GoogleSearchResult, and_(model.InterventionRequest.information == GoogleSearchResult.title, 
            #                                                 model.InterventionRequest.site_url == GoogleSearchResult.link)).\
            #                     join(SentimentResult, GoogleSearchResult.snippet == SentimentResult.keyword).\
            #                     filter(and_(extract("month", model.InterventionRequest.created_at) == cur_month,
            #                                 extract("year", model.InterventionRequest.created_at) == cur_year,
            #                                 model.InterventionRequest.user_id == user_id)).\
            #                     order_by(model.InterventionRequest.updated_at.desc()).all()
            
            interventions = db.query(model.InterventionRequest.id,
                                     model.InterventionRequest.user_id,
                                     model.InterventionRequest.title,
                                     model.InterventionRequest.information,
                                     model.InterventionRequest.additional_information,
                                     model.InterventionRequest.updated_at,
                                     model.InterventionRequest.site_url,
                                     model.InterventionRequest.status,
                                     model.InterventionRequest.admin_read_status,
                                     model.InterventionRequest.user_read_status).\
                                filter(and_(extract("month", model.InterventionRequest.created_at) == cur_month,
                                            extract("year", model.InterventionRequest.created_at) == cur_year,
                                            model.InterventionRequest.user_id == user_id)).\
                                order_by(model.InterventionRequest.updated_at.desc()).all()
            return interventions
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False

    async def check_valid_user(db: Session, user_id: int, intervention_id: int):
        is_valid = False
        try:
            requested_user_id = db.query(model.InterventionRequest).\
                filter(model.InterventionRequest.id == intervention_id).first()
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        if(user_id == requested_user_id.user_id):
            is_valid = True
        
        return is_valid
    
    async def request_approved(db: Session, intervention_id: int):
        cur_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            res = db.query(model.InterventionRequest).filter(model.InterventionRequest.id == intervention_id).\
                update({model.InterventionRequest.updated_at: cur_datetime,
                        model.InterventionRequest.status: 1})
            db.commit()
            return res
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False

    async def get_all_count(db:Session):
        try:
            count = db.query(model.InterventionRequest).count()
            return count
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
    
    async def reject_intervention(db: Session, intervention_id):
        try:
            inter = db.query(model.InterventionRequest).\
                filter(model.InterventionRequest.id == intervention_id).\
                update({model.InterventionRequest.status: 3})
            db.commit()
            return inter
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        
    async def update_status(db: Session, intervention_id: int, status: int):
        try:
            inter = db.query(model.InterventionRequest).\
                filter(model.InterventionRequest.id == intervention_id).\
                update({model.InterventionRequest.status: status})
            db.commit()
            return inter
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
            
    async def complete_request(db: Session, user_id: int, invoice_id: int):
        try:
            # quote = db.query(InterventionResponse.response).filter(InterventionResponse.response == '{"quote":18}', InterventionResponse.response_type==1).first()
            
            inter_id = db.query(model.InterventionRequest).\
                join(InterventionResponse, InterventionResponse.request_id == model.InterventionRequest.id).\
                filter(and_(model.InterventionRequest.user_id == user_id, 
                            InterventionResponse.response_type == 1, 
                            InterventionResponse.response == '{"quote":'+str(invoice_id)+'}')).first().id
            print(inter_id)
            result = db.query(model.InterventionRequest).filter(model.InterventionRequest.id == inter_id).\
                update({model.InterventionRequest.status: 4})
            db.commit()
            
            # print(quote)
            return result
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        
    async def get_daily_intervention_data(db: Session, inter_type: str=None):
        try:
            cur_date = datetime.date.today()
            cur_day = cur_date.day
            cur_month = cur_date.month
            cur_year = cur_date.year
            inter_data = db.query(model.InterventionRequest.id,
                                  model.InterventionRequest.user_id,
                                User.full_name,
                                model.InterventionRequest.title,
                                model.InterventionRequest.information,
                                model.InterventionRequest.additional_information,
                                model.InterventionRequest.updated_at,
                                model.InterventionRequest.site_url,
                                model.InterventionRequest.admin_read_status,
                                model.InterventionRequest.user_read_status,
                                model.InterventionRequest.status).\
                            join(User, model.InterventionRequest.user_id == User.id).\
                            filter(and_(extract("day", model.InterventionRequest.created_at) == cur_day,
                                        extract("month", model.InterventionRequest.created_at) == cur_month,
                                        extract("year", model.InterventionRequest.created_at) == cur_year)).\
                            order_by(model.InterventionRequest.updated_at.desc())
            total_count = inter_data.count()
            in_progress_count = inter_data.filter(model.InterventionRequest.status == 1).count()
            pending_count = inter_data.filter(model.InterventionRequest.status == 2).count()
            result = {
                "total_count": total_count,
                "in_progress_count": in_progress_count,
                "pending_count": pending_count,
                "inter_data": None
            }
            if inter_type == None or inter_type == "total_count":
                result["inter_data"] = inter_data.all()
            if inter_type == "in_progress_count":
                result["inter_data"] = inter_data.filter(model.InterventionRequest.status == 1).all()
            if inter_type == "pending_count":
                result["inter_data"] = inter_data.filter(model.InterventionRequest.status == 2).all()
            return result
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        
    async def get_weekly_intervention_data(db: Session, inter_type: str=None):
        try:
            cur_date = datetime.date.today()
            cur_weekday = cur_date.weekday()
            cur_day = cur_date.day
            cur_month = cur_date.month
            cur_year = cur_date.year
            start_cur_week = cur_day - cur_weekday
            inter_data = db.query(model.InterventionRequest.id,
                                  model.InterventionRequest.user_id,
                                User.full_name,
                                model.InterventionRequest.title,
                                model.InterventionRequest.information,
                                model.InterventionRequest.additional_information,
                                model.InterventionRequest.updated_at,
                                model.InterventionRequest.site_url,
                                model.InterventionRequest.admin_read_status,
                                model.InterventionRequest.user_read_status,
                                model.InterventionRequest.status).\
                            join(User, model.InterventionRequest.user_id == User.id).\
                            filter(and_(extract("day", model.InterventionRequest.created_at) <= cur_day,
                                        extract("day", model.InterventionRequest.created_at) >= start_cur_week,
                                        extract("month", model.InterventionRequest.created_at) == cur_month,
                                        extract("year", model.InterventionRequest.created_at) == cur_year)).\
                            order_by(model.InterventionRequest.updated_at.desc())
            total_count = inter_data.count()
            in_progress_count = inter_data.filter(model.InterventionRequest.status == 1).count()
            pending_count = inter_data.filter(model.InterventionRequest.status == 2).count()
            result = {
                "total_count": total_count,
                "in_progress_count": in_progress_count,
                "pending_count": pending_count,
                "inter_data": None
            }
            if inter_type == None or inter_type == "total_count":
                result["inter_data"] = inter_data.all()
            if inter_type == "in_progress_count":
                result["inter_data"] = inter_data.filter(model.InterventionRequest.status == 1).all()
            if inter_type == "pending_count":
                result["inter_data"] = inter_data.filter(model.InterventionRequest.status == 2).all()
            return result
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        
    async def get_monthly_intervention_data(db: Session, inter_type: str=None):
        try:
            cur_date = datetime.date.today()
            cur_month = cur_date.month
            cur_year = cur_date.year
            inter_data = db.query(model.InterventionRequest.id,
                                  model.InterventionRequest.user_id,
                                User.full_name,
                                model.InterventionRequest.title,
                                model.InterventionRequest.information,
                                model.InterventionRequest.additional_information,
                                model.InterventionRequest.updated_at,
                                model.InterventionRequest.site_url,
                                model.InterventionRequest.admin_read_status,
                                model.InterventionRequest.user_read_status,
                                model.InterventionRequest.status).\
                            join(User, model.InterventionRequest.user_id == User.id).\
                            filter(and_(extract("month", model.InterventionRequest.created_at) == cur_month,
                                        extract("year", model.InterventionRequest.created_at) == cur_year)).\
                            order_by(model.InterventionRequest.updated_at.desc())
            total_count = inter_data.count()
            in_progress_count = inter_data.filter(model.InterventionRequest.status == 1).count()
            pending_count = inter_data.filter(model.InterventionRequest.status == 2).count()
            result = {
                "total_count": total_count,
                "in_progress_count": in_progress_count,
                "pending_count": pending_count,
                "inter_data": None
            }
            if inter_type == None or inter_type == "total_count":
                result["inter_data"] = inter_data.all()
            if inter_type == "in_progress_count":
                result["inter_data"] = inter_data.filter(model.InterventionRequest.status == 1).all()
            if inter_type == "pending_count":
                result["inter_data"] = inter_data.filter(model.InterventionRequest.status == 2).all()
            return result
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        
    async def get_limited_data(db: Session, user_id: int, limit_count: int):
        try:
            inter_data = db.query(model.InterventionRequest.id,
                                  model.InterventionRequest.user_id,
                                User.full_name,
                                model.InterventionRequest.title,
                                model.InterventionRequest.information,
                                model.InterventionRequest.updated_at,
                                model.InterventionRequest.site_url,
                                model.InterventionRequest.admin_read_status,
                                model.InterventionRequest.user_read_status,
                                model.InterventionRequest.status).\
                            join(User, model.InterventionRequest.user_id == User.id).\
                            filter(User.id == user_id).\
                            order_by(model.InterventionRequest.updated_at.desc()).\
                            limit(limit_count).all()
            return inter_data
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
    
    async def check_quote_sent(db: Session, intervention_id: int):
        try:
            inter_response = db.query(InterventionResponse).\
                                filter(and_(InterventionResponse.request_id == intervention_id,
                                            InterventionResponse.response_type == 1)).first()
            if inter_response == None:
                return False
            return True
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
    
    async def update_datetime(db: Session, intervention_id: int):
        try:
            now = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
            db.query(model.InterventionRequest).\
                filter(model.InterventionRequest.id == intervention_id).\
                update({model.InterventionRequest.updated_at: now})
            db.commit()
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
    
    async def update_read_status(db:Session, intervention_id: int, user_role: bool, read_status: bool):
        try:
            result = db.query(model.InterventionRequest).\
                        filter(model.InterventionRequest.id == intervention_id).\
                        update({model.InterventionRequest.admin_read_status: read_status} if user_role else {model.InterventionRequest.user_read_status: read_status})
            db.commit()
            return result
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False
        
    async def get_unread_count(db: Session, user_id: int, user_role: bool):
        try:
            count = db.query(model.InterventionRequest.id,
                             model.InterventionRequest.user_id,
                             model.InterventionRequest.admin_read_status).\
                        filter(model.InterventionRequest.admin_read_status == False).\
                        count() if user_role == False \
                        else db.query(model.InterventionRequest.id,
                                      model.InterventionRequest.user_id,
                                      model.InterventionRequest.user_read_status).\
                                join(InterventionResponse, model.InterventionRequest.id == InterventionResponse.request_id).\
                                filter(and_(model.InterventionRequest.user_id == user_id,
                                            model.InterventionRequest.user_read_status == False)).count()
            return count
        except Exception as e:
            print("Exception in InterventionRepo:", e)
            return False