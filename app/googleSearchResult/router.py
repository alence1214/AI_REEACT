from decouple import config
from serpapi import GoogleSearch

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from tools import get_user_id, analysis_sentiment, remove_http

from .repository import GoogleSearchResult
from app.auth.auth_bearer import JWTBearer, UserRoleBearer
from app.sentimentResult.repository import SentimentResult
from app.searchid_list.repository import SearchIDListRepo
from app.alert.repository import AlertRepo
from app.userpayment.repository import UserPaymentRepo
from app.cron_job.repository import CronHistoryRepo

router = APIRouter()

@router.post("/add_additional_keyword_url", dependencies=[Depends(JWTBearer())], tags=["GoogleSearch"])
async def add_additional_keyword_url(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    req_data = await request.json()
    keyword_url = req_data["keyword_url"]
    additional_keyword_url = req_data["additional_keyword_url"]
    
    if additional_keyword_url == "" or additional_keyword_url == None:
        raise HTTPException(status_code=403, detail="No additional keyword or url.")
    
    old_search_id = await SearchIDListRepo.get_search_id(db, user_id, keyword_url)
    
    new_search = GoogleSearch({
        "q": keyword_url + " " +additional_keyword_url,
        "serp_api_key": config('SerpAPI_Key_Google_Search'),
        "location": "France",
        "gl": "fr",
        "start": 0,
        "num": 100
    })
    new_search_result = new_search.get_dictionary()
    new_organic_results = new_search_result.get('organic_results')
    new_search_id = new_search_result.get("search_metadata")["id"]
    count = 0
    alert_cnt = 0
    while(count < 50):
        try:
            new_organic_result = new_organic_results[count]
        except:
            break
        googleSearchResult = {
            "search_id": new_search_id,
            "title": new_organic_result["title"],
            "link": new_organic_result["link"],
            "snippet": new_organic_result["snippet"] if "snippet" in new_organic_result else "Unknown!",
            "ranking": count
        }
        new_sentiment_result = analysis_sentiment(f"{googleSearchResult['title']} {googleSearchResult['snippet']}")
        sentimentResult = {
            "keyword": googleSearchResult["snippet"],
            "label": new_sentiment_result["label"],
            "score": str(new_sentiment_result["score"])
        }
        createdNewGoogleSearchResult = await GoogleSearchResult.create(db, googleSearchResult)
        createdNewSentimentResult = await SentimentResult.create(db, sentimentResult)
        if createdNewGoogleSearchResult != False and createdNewSentimentResult != False:
            count = count + 1
        if createdNewGoogleSearchResult == "Google Search Result item saved successfully!":
            new_alert = {
                "user_id": user_id,
                "search_id": new_search_id,
                "title": googleSearchResult["title"],
                "site_url": googleSearchResult["link"],
                "label": sentimentResult["label"],
            }
            created_alert = await AlertRepo.create(db, new_alert)
            if created_alert != False:
                alert_cnt += 1
    if old_search_id != new_search_id:
        await GoogleSearchResult.delete_old_results(db, old_search_id)
    await SearchIDListRepo.update_search_id(db, user_id, old_search_id, new_search_id)
    await SearchIDListRepo.update_additional_keyword_url(db, user_id, new_search_id, additional_keyword_url)
    result = await GoogleSearchResult.get_refine_analysis(db, user_id, new_search_id)
    
    gs_statistics = await GoogleSearchResult.get_reputation_score(db, user_id)
    cronhistory_data = {
        "user_id": user_id,
        "total_search_result": gs_statistics["total_count"],
        "positive_search_result": gs_statistics["positive_count"],
        "negative_search_result": gs_statistics["negative_count"]
    }
    new_cronhistory = await CronHistoryRepo.update(db, user_id, cronhistory_data)
    
    return {
        "analyse": result
    }
    

@router.get("/google_search_analyse", dependencies=[Depends(JWTBearer())], tags=["GoogleSearch"])
async def get_google_search_analyse(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    result = await GoogleSearchResult.get_analysis(db, user_id)
    payment_data = await UserPaymentRepo.get_payment_by_user_id(db, user_id)
    return {
        "analyse": result,
        "payment_data": payment_data
    }
    
@router.get("/google_search_analyse/{search_id}", dependencies=[Depends(JWTBearer())], tags=["GoogleSearch"])
async def get_google_search_analyse_by_id(search_id: str, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    result = await GoogleSearchResult.get_refine_analysis(db, user_id, search_id)
    payment_data = await UserPaymentRepo.get_default_payment_by_user_id(db, user_id)
    reputation_score = await GoogleSearchResult.get_reputation_score(db, user_id)
    cron_history = await CronHistoryRepo.get_history(db, user_id)
    return {
        "analyse": result,
        "payment_data": payment_data,
        "cron_history": cron_history,
        "reputation_score": reputation_score
    }
    
@router.post("/analysis_ranking", dependencies=[Depends(JWTBearer())], tags=["GoogleSearch"])
async def analysis_ranking_change(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    request = await request.json()
    changed_id = request['changed_id']
    changed_rank = request['changed_rank']
    result = await GoogleSearchResult.change_rank(db, user_id, changed_id, changed_rank)
    
    if result == "Invalid request":
        raise HTTPException(status_code=403, detail=result)
    
    return result

@router.get("/sentiment_analysis", dependencies=[Depends(JWTBearer())], tags=["SentimentAnalysis"])
async def get_sentiment_result(page: int, limit: int, db: Session=Depends(get_db)):
    """
        Get the Sentiment Analysis Results
    """
    
    db_sentiment_analysis_result = await SentimentResult.get(db=db, page=page, limit=limit)
    
    return db_sentiment_analysis_result

@router.get("/keyword_urls", dependencies=[Depends(JWTBearer())], tags=["GoogleSearch"])
async def get_keyword_urls(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    keyword_urls = await SearchIDListRepo.get_item_by_user_id(db, user_id)
    if keyword_urls == False:
        raise HTTPException(status_code=403, detail="DB Error!")
    return {
        "keyword_urls": keyword_urls
    }

@router.get("/search_contents/{keyword}", dependencies=[Depends(JWTBearer())], tags=["Search Box"])
async def search_contents(keyword: str, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    search_results = await GoogleSearchResult.search_content_by_user_id(db, user_id, keyword)
    if search_results == False:
        raise HTTPException(status_code=403, detail="DB Error!")
    return search_results

@router.get("/admin/search_contents/{keyword}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Search Box"])
async def admin_search_contents(keyword: str, db: Session=Depends(get_db)):
    search_result = await GoogleSearchResult.admin_search_content(db, keyword)
    if search_result == False:
        raise HTTPException(status_code=403, detail="DB Error!")
    return search_result
