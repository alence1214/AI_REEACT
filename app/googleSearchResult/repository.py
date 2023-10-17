from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from . import model, schema
import datetime

from app.sentimentResult.model import SentimentResult
from app.searchid_list.model import SearchIDList

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
                                                                ranking=googleSearchResult['ranking'])
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
            
            db_google_search_result.updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            print(db_google_search_result.id)
            db.add(db_google_search_result)
            db.commit()
            db.refresh(db_google_search_result)
            return "Google Search Result Item updated successfully!"
        except Exception as e:
            print(e)
            return False
    
    async def get_all(db: Session):
        try:
            return db.query(model.GoogleSearchResult).all()
        except Exception as e:
            print(e)
            return False
    
    async def get_analysis(db: Session, user_id: int):
        try:
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
            return {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "keyword_urls": search_keywords,
                "result": result.all()
            }
        except Exception as e:
            print("Get Analysis Data Exception:", e)
            return False
        
    async def get_refine_analysis(db: Session, user_id: int, search_id: str):
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
                                where(and_(SearchIDList.user_id == user_id, SearchIDList.search_id == search_id)).\
                                order_by(model.GoogleSearchResult.ranking)
            positive_count = result.filter(SentimentResult.label == 'positive').count()
            negative_count = result.filter(SentimentResult.label == 'negative').count()
            
            search_keywords = db.query(SearchIDList.keyword_url,
                                       SearchIDList.additional_keyword_url,
                                       SearchIDList.search_id).\
                                filter(SearchIDList.user_id == user_id).all()
            return {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "keyword_urls": search_keywords,
                "result": result.all()
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
                db.commit()
                db.refresh(res_)
            
            res = db.query(model.GoogleSearchResult).\
                filter(model.GoogleSearchResult.id == changed_id).first()
            setattr(res, "ranking", changed_rank)
            db.commit()
            db.refresh(res)
        except Exception as e:
            print(e)
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
            return {
                "total_count": total_count,
                "positive_count": positive_count,
                "negative_count": negative_count
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
            return False