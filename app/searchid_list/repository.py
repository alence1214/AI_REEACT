from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from .model import SearchIDList
import datetime
from app.user.model import User

class SearchIDListRepo:
    async def create(db: Session, searchid_list: dict):
        try:
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            db_searchidlist = SearchIDList(user_id=searchid_list["user_id"],
                                        search_id=searchid_list["search_id"],
                                        keyword_url=searchid_list["keyword_url"],
                                        additional_keyword_url="",
                                        created_at=created_at)
            db.add(db_searchidlist)
            db.commit()
            db.refresh(db_searchidlist)
            return True
        except Exception as e:
            print("SearchIdListRepo Exception:", e)
            return False
        
    async def get_search_id(db: Session, user_id: int, keyword_url: str):
        try:
            print(user_id, keyword_url)
            search_id = db.query(SearchIDList).\
                filter(SearchIDList.user_id == user_id,
                        SearchIDList.keyword_url == keyword_url).first().search_id
            return search_id
        except Exception as e:
            print("SearchIdListRepo Exception:", e)
            return False
        
    async def update_search_id(db: Session, userid: str, old_search_id: str, new_search_id: str):
        try:
            db.query(SearchIDList).\
                filter(and_(SearchIDList.search_id == old_search_id,
                            SearchIDList.user_id == userid)).\
                update({SearchIDList.search_id: new_search_id})
            db.commit()
            return True
        except Exception as e:
            print("SearchIdListRepo Exception:", e)
            return False
        
    async def update_additional_keyword_url(db: Session, userid: str, search_id: str, additional_keyword_url: str):
        try:
            db.query(SearchIDList).\
                filter(and_(SearchIDList.search_id == search_id,
                            SearchIDList.user_id == userid)).\
                update({SearchIDList.additional_keyword_url: additional_keyword_url})
            db.commit()
            return True
        except Exception as e:
            print("SearchIdListRepo Exception:", e)
            return False
        
    async def get_item_by_user_id(db: Session, user_id: int):
        try:
            result = db.query(SearchIDList).filter(SearchIDList.user_id == user_id).all()
            return result
        except Exception as e:
            print("SearchIdListRepo Exception:", e)
            return False
        
    async def check_keyword_duplicate(db: Session, user_id: int, new_keywordurl: str):
        try:
            select = db.query(SearchIDList).filter(and_(SearchIDList.user_id == user_id,
                                                        SearchIDList.keyword_url == new_keywordurl)).first()
            if select:
                return False
            return True
        except Exception as e:
            print("SearchIdListRepo Exception:", e)
            return False