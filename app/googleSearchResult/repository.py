from sqlalchemy import text, case, literal
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from . import model, schema
import datetime
import re

from database import metadata

from app.sentimentResult.model import SentimentResult
from app.searchid_list.model import SearchIDList
from app.user.model import User
from app.messaging.model import Messaging
from app.invoice.model import Invoice
from app.intervention.model import InterventionRequest
from app.intervention_response.model import InterventionResponse
from app.alert.model import Alert
from app.promo_code.model import PromoCode
from app.stripe_manager.stripe_manager import StripeManager

class GoogleSearchResult:
    
    async def create(db: Session, googleSearchResult: schema.GoogleSearchResult):
        try:
            db_google_search_result = db.query(model.GoogleSearchResult).\
                filter(and_(model.GoogleSearchResult.snippet == googleSearchResult['snippet'],
                            model.GoogleSearchResult.link == googleSearchResult['link'],
                            model.GoogleSearchResult.search_id == googleSearchResult['search_id'])).first()
            
            if not db_google_search_result:
                created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                db_googleSearchResult = model.GoogleSearchResult(search_id=googleSearchResult['search_id'], 
                                                                title=googleSearchResult['title'], 
                                                                link=googleSearchResult['link'], 
                                                                snippet=googleSearchResult['snippet'], 
                                                                created_at=created_at,
                                                                ranking=googleSearchResult['ranking'],
                                                                request_status=False)
                db.add(db_googleSearchResult)
                db.commit()
                db.refresh(db_googleSearchResult)
                print(db_googleSearchResult.id)
                return "Google Search Result item saved successfully!"
            
            setattr(db_google_search_result, 'search_id', googleSearchResult['search_id'])
            setattr(db_google_search_result, 'title', googleSearchResult['title'])
            setattr(db_google_search_result, 'link', googleSearchResult['link'])
            setattr(db_google_search_result, 'snippet', googleSearchResult['snippet'])
            setattr(db_google_search_result, 'ranking', googleSearchResult['ranking'])
            setattr(db_google_search_result, 'request_status', False)
            
            db_google_search_result.updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            print(db_google_search_result.id)
            db.add(db_google_search_result)
            db.commit()
            db.refresh(db_google_search_result)
            return "Google Search Result Item updated successfully!"
        except Exception as e:
            print(e)
            db.rollback()
            return False
    
    async def get_all(db: Session):
        try:
            return db.query(model.GoogleSearchResult).all()
        except Exception as e:
            print(e)
            return False
    
    async def get_analysis(db: Session, user_id: int):
        try:
            # Define your custom sort order
            custom_order = ["negative", "positive", "neutral"]

            # Create a case statement to map the custom order to the column values
            custom_sort = case(
                [
                    (SentimentResult.label == value, order) for order, value in enumerate(custom_order)
                ],
                else_=len(custom_order)
            )
            
            search_keywords = db.query(SearchIDList.keyword_url,
                                       SearchIDList.additional_keyword_url,
                                       SearchIDList.search_id).\
                                filter(SearchIDList.user_id == user_id).all()
            result = db.query(model.GoogleSearchResult.id,
                            model.GoogleSearchResult.search_id,
                            model.GoogleSearchResult.title,
                            model.GoogleSearchResult.link,
                            model.GoogleSearchResult.snippet,
                            model.GoogleSearchResult.created_at,
                            model.GoogleSearchResult.created_at,
                            SearchIDList.user_id,
                            SentimentResult.label,
                            SentimentResult.score,
                            SearchIDList.keyword_url).\
                                join(SearchIDList, model.GoogleSearchResult.search_id == SearchIDList.search_id).\
                                join(SentimentResult, model.GoogleSearchResult.snippet == SentimentResult.keyword).\
                                filter(and_(SearchIDList.user_id == user_id,
                                            model.GoogleSearchResult.search_id == search_keywords[0][2])).\
                                order_by(model.GoogleSearchResult.ranking)
            positive_count = result.filter(SentimentResult.label == 'positive').count()
            negative_count = result.filter(SentimentResult.label == 'negative').count()
            
            final_result = []
            user_data = db.query(User).filter(User.id == user_id).first()
            subscription_status = await StripeManager.check_subscription(user_data.subscription_at)
            if subscription_status == False:
                pattern = r'[a-zA-Z]'
                for data in result.all():
                    data = dict(data)
                    if data["label"] == 'positive' or data["label"] == 'negative':
                        data["title"] = re.sub(pattern, '*', data["title"])
                        data["link"] = re.sub(pattern, '*', data["link"])
                        data["snippet"] = re.sub(pattern, '*', data["snippet"])
                    final_result.append(data)
            else:
                final_result = result.all()
            
            return {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "keyword_urls": search_keywords,
                "result": final_result
            }
        except Exception as e:
            print("Get Analysis Data Exception:", e)
            return False
        
    async def get_refine_analysis(db: Session, user_id: int, search_id: str):
        try:
            # Define your custom sort order
            custom_order = ["negative", "positive", "neutral"]

            # Create a case statement to map the custom order to the column values
            custom_sort = case(
                [
                    (SentimentResult.label == value, order) for order, value in enumerate(custom_order)
                ],
                else_=len(custom_order)
            )
            result = db.query(model.GoogleSearchResult.id,
                            model.GoogleSearchResult.search_id,
                            model.GoogleSearchResult.title,
                            model.GoogleSearchResult.link,
                            model.GoogleSearchResult.snippet,
                            model.GoogleSearchResult.created_at,
                            model.GoogleSearchResult.created_at,
                            model.GoogleSearchResult.request_status,
                            SearchIDList.user_id,
                            SentimentResult.label,
                            SentimentResult.score,
                            SearchIDList.keyword_url).\
                                join(SearchIDList, model.GoogleSearchResult.search_id == SearchIDList.search_id).\
                                join(SentimentResult, model.GoogleSearchResult.snippet == SentimentResult.keyword).\
                                where(and_(SearchIDList.user_id == user_id, SearchIDList.search_id == search_id)).\
                                order_by(model.GoogleSearchResult.ranking)
            positive_count = result.filter(SentimentResult.label == 'positive').count()
            negative_count = result.filter(SentimentResult.label == 'negative').count()
            
            search_keywords = db.query(SearchIDList.keyword_url,
                                       SearchIDList.additional_keyword_url,
                                       SearchIDList.search_id).\
                                filter(SearchIDList.user_id == user_id).all()
            final_result = []
            user_data = db.query(User).filter(User.id == user_id).first()
            subscription_status = await StripeManager.check_subscription(user_data.subscription_at)
            if subscription_status == False:
                pattern = r'[a-zA-Z]'
                for data in result.all():
                    data = dict(data)
                    if data["label"] == 'positive' or data["label"] == 'negative':
                        data["title"] = re.sub(pattern, '*', data["title"])
                        data["link"] = re.sub(pattern, '*', data["link"])
                        data["snippet"] = re.sub(pattern, '*', data["snippet"])
                    final_result.append(data)
            else:
                final_result = result.all()
            return {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "keyword_urls": search_keywords,
                "result": final_result
            }
        except Exception as e:
            print(e)
            return False

    async def change_rank(db: Session, user_id: int, changed_id: int, changed_rank: int):
        try:
            selection = db.query(model.GoogleSearchResult).\
                filter(model.GoogleSearchResult.id == changed_id).first()
            search_id = selection.search_id
            user_search_id = db.query(SearchIDList.search_id).\
                filter(SearchIDList.user_id == user_id, 
                    SearchIDList.search_id == search_id).all()
                
            if user_search_id == None:
                return "Invalid request"
            
            original_rank = selection.ranking
            rank_change = 1 if original_rank > changed_rank else -1
            start = changed_rank if original_rank > changed_rank else original_rank+1
            end = original_rank if original_rank > changed_rank else changed_rank+1
            
            for i in range(start, end):
                res_ = db.query(model.GoogleSearchResult).\
                    filter(and_(model.GoogleSearchResult.search_id == search_id, 
                        model.GoogleSearchResult.ranking == i)).first()
                setattr(res_, "ranking", i+rank_change)
                db.add(res_)
                db.commit()
                db.refresh(res_)
            
            res = db.query(model.GoogleSearchResult).\
                filter(model.GoogleSearchResult.id == changed_id).first()
            setattr(res, "ranking", changed_rank)
            db.add(res)
            db.commit()
            db.refresh(res)
        except Exception as e:
            print(e)
            db.rollback()
            return False
        return "Changed Successfully"
        
    async def get_reputation_score(db: Session, user_id: int):
        try:
            result = db.query(model.GoogleSearchResult.id,
                            model.GoogleSearchResult.search_id,
                            model.GoogleSearchResult.title,
                            model.GoogleSearchResult.link,
                            model.GoogleSearchResult.snippet,
                            model.GoogleSearchResult.created_at,
                            model.GoogleSearchResult.created_at,
                            SearchIDList.user_id,
                            SentimentResult.label,
                            SentimentResult.score,
                            SearchIDList.keyword_url).\
                                join(SearchIDList, model.GoogleSearchResult.search_id == SearchIDList.search_id).\
                                join(SentimentResult, model.GoogleSearchResult.snippet == SentimentResult.keyword).\
                                filter(SearchIDList.user_id == user_id)
            total_count = result.count()
            positive_count = result.filter(SentimentResult.label == 'positive').count()
            negative_count = result.filter(SentimentResult.label == 'negative').count()
            reputation_score = int((total_count - negative_count) / total_count * 100)
            return {
                "total_count": total_count,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "reputation_score": reputation_score
            }
        except Exception as e:
            print(e)
            return False
    
    async def delete_old_results(db: Session, search_id: str):
        try:
            result = db.query(model.GoogleSearchResult).filter(model.GoogleSearchResult.search_id == search_id).delete()
            db.commit()
            return True
        except Exception as e:
            print("delete_old_results", e)
            db.rollback()
            return False
        
    async def search_content_by_user_id(db: Session, user_id: int, keyword: str):
        try:
            search_results = {}
            search_keywords = db.query(SearchIDList.keyword_url,
                                       SearchIDList.additional_keyword_url,
                                       SearchIDList.search_id).\
                                filter(SearchIDList.user_id == user_id).all()
            search_ids = [search_keyword.search_id for search_keyword in search_keywords]
            print(search_ids)
            analyse_search_result = db.query(model.GoogleSearchResult.id,
                        model.GoogleSearchResult.search_id,
                        model.GoogleSearchResult.title,
                        model.GoogleSearchResult.link,
                        model.GoogleSearchResult.snippet,
                        model.GoogleSearchResult.created_at,
                        SearchIDList.user_id,
                        SentimentResult.label,
                        SearchIDList.keyword_url).\
                            join(SearchIDList, model.GoogleSearchResult.search_id == SearchIDList.search_id).\
                            join(SentimentResult, model.GoogleSearchResult.snippet == SentimentResult.keyword).\
                            filter(and_(SearchIDList.user_id == user_id,
                                        # model.GoogleSearchResult.search_id in search_ids,
                                        or_(model.GoogleSearchResult.title.like(f"%{keyword}%"),
                                            model.GoogleSearchResult.link.like(f"%{keyword}%"),
                                            model.GoogleSearchResult.snippet.like(f"%{keyword}%"),
                                            SentimentResult.label.like(f"%{keyword}%")))).\
                            order_by(model.GoogleSearchResult.ranking).all()
            search_results["Analyse"] = analyse_search_result
            
            # service_search_result = db.query(InterventionRequest.id,
            #                                 InterventionRequest.user_id,
            #                                 InterventionRequest.information,
            #                                 InterventionRequest.additional_information,
            #                                 InterventionRequest.site_url,
            #                                 InterventionRequest.status,
            #                                 InterventionResponse.response).\
            #                             join(InterventionResponse, InterventionRequest.id == InterventionResponse.request_id).\
            #                             filter(and_(InterventionRequest.user_id == user_id,
            #                                         or_(and_(or_(InterventionRequest.information.like(f"%{keyword}%"),
            #                                                     InterventionRequest.additional_information.like(f"%{keyword}%"),
            #                                                     InterventionRequest.site_url.like(f"%{keyword}%"),
            #                                                     InterventionResponse.response.like(f"%{keyword}%")),
            #                                                 InterventionRequest.status == 3)))).all()
            service_search_result = db.query(InterventionRequest).\
                                        filter(and_(InterventionRequest.user_id == user_id,
                                                    or_(InterventionRequest.information.like(f"%{keyword}%"),
                                                    InterventionRequest.additional_information.like(f"%{keyword}%"),
                                                    InterventionRequest.site_url.like(f"%{keyword}%")))).all()
            search_results["Intervention"] = service_search_result
            
            invoice_search_result = db.query(Invoice).filter(and_(or_(Invoice.bill_from == user_id,
                                                                      Invoice.bill_to == user_id),
                                                                  or_(Invoice.service_detail.like(f"%{keyword}%"),
                                                                      Invoice.invoice_detail.like(f"%{keyword}%")))).all()
            search_results["Invoice"] = invoice_search_result
            
            alert_search_result = db.query(Alert).filter(and_(Alert.user_id == user_id,
                                                              or_(Alert.title.like(f"%{keyword}%"),
                                                                  Alert.site_url.like(f"%{keyword}%"),
                                                                  Alert.label.like(f"%{keyword}%")))).all()
            search_results["Alert"] = alert_search_result
            
            message_search_result = db.query(Messaging).filter(and_(or_(Messaging.user_id == user_id,
                                                                        Messaging.message_to == user_id),
                                                                    or_(Messaging.messaging.like(f"%{keyword}%"),
                                                                        Messaging.analysis_selection.like(f"%{keyword}%"),
                                                                        Messaging.object_for.like(f"%{keyword}%"),
                                                                        Messaging.attachments.like(f"%{keyword}%")))).all()
            search_results["Messaging"] = message_search_result
            
            return search_results
        except Exception as e:
            print("search_content_by_user_id", e)
            return False

    async def admin_search_content(db: Session, keyword: str):
        try:
            search_results = {}
            
            user_search_result = db.query(User.id,
                                          User.full_name,
                                          User.social_reason,
                                          User.email,
                                          User.province,
                                          User.subscription_at).\
                                    filter(and_(User.role == 2,
                                                or_(User.full_name.like(f"%{keyword}%"),
                                                    User.email.like(f"%{keyword}%"),
                                                    User.social_reason.like(f"%{keyword}%"),
                                                    User.activity.like(f"%{keyword}%"),
                                                    User.number_siret.like(f"%{keyword}%"),
                                                    User.vat_number.like(f"%{keyword}%"),
                                                    User.address.like(f"%{keyword}%"),
                                                    User.postal_code.like(f"%{keyword}%"),
                                                    User.province.like(f"%{keyword}%"),
                                                    User.pays.like(f"%{keyword}%"),
                                                    User.phone.like(f"%{keyword}%"),
                                                    User.site_internet.like(f"%{keyword}%")))).all()
            search_results["User"] = user_search_result
            
            service_search_result = db.query(InterventionRequest.id,
                                            InterventionRequest.user_id,
                                            InterventionRequest.information,
                                            InterventionRequest.additional_information,
                                            InterventionRequest.site_url,
                                            InterventionRequest.status,
                                            User.full_name).\
                                        join(User, InterventionRequest.user_id == User.id).\
                                        filter(or_(InterventionRequest.information.like(f"%{keyword}%"),
                                                    InterventionRequest.additional_information.like(f"%{keyword}%"),
                                                    InterventionRequest.site_url.like(f"%{keyword}%"))).all()
            search_results["Intervention"] = service_search_result
            
            invoice_search_result = db.query(Invoice).filter(or_(Invoice.service_detail.like(f"%{keyword}%"),
                                                                Invoice.invoice_detail.like(f"%{keyword}%"))).all()
            search_results["Invoice"] = invoice_search_result
            
            promo_search_result = db.query(PromoCode).filter(PromoCode.code_title.like(f"%{keyword}%")).all()
            search_results["Promo"] = promo_search_result
            
            message_search_result = db.query(Messaging.id,
                                            User.full_name,
                                            Messaging.analysis_selection,
                                            Messaging.updated_at,
                                            Messaging.user_read_status,
                                            Messaging.admin_read_status).\
                                        join(User, Messaging.user_id == User.id).\
                                        filter(or_(Messaging.messaging.like(f"%{keyword}%"),
                                                    Messaging.analysis_selection.like(f"%{keyword}%"),
                                                    Messaging.object_for.like(f"%{keyword}%"),
                                                    Messaging.attachments.like(f"%{keyword}%"))).all()
            search_results["Messaging"] = message_search_result
            
            return search_results
        except Exception as e:
            print("admin_search_content", e)
            return False
        
    async def update_request_status(db: Session, id: int, status: bool):
        try:
            db.query(model.GoogleSearchResult).filter(model.GoogleSearchResult.id == id).\
                                                update({model.GoogleSearchResult.request_status: status})
            db.commit()
            return True
        except Exception as e:
            print("update_request_status", e)
            db.rollback()
            return False

    async def check_request_status(db: Session, id: int):
        try:
            result = db.query(model.GoogleSearchResult).filter(model.GoogleSearchResult.id == id).first()
            if result.request_status:
                return False
            else:
                return True
        except Exception as e:
            print("check_request_status", e)
            return False
    
    async def change_search_result(db: Session, gs_id: int, action: str):
        try:
            if action == 'remove':
                db.query(model.GoogleSearchResult).filter(model.GoogleSearchResult.id == gs_id).delete()
                db.commit()
                return "removed"
            else:
                gs_item = db.query(model.GoogleSearchResult).filter(model.GoogleSearchResult.id == gs_id).first()
                sentiment = db.query(SentimentResult).filter(SentimentResult.keyword == gs_item.snippet).first()
                setattr(sentiment, "label", action)
                db.add(sentiment)
                db.commit()
                db.refresh(sentiment)
                return gs_item
        except Exception as e:
            print("change_search_result", e)
            db.rollback()
            return False