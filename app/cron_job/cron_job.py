import requests
import json

from database import SessionLocal
from decouple import config
from serpapi import GoogleSearch
from sqlalchemy import and_

from tools import analysis_sentiment, send_email

from app.user.model import User
from app.googleSearchResult.model import GoogleSearchResult
from app.sentimentResult.model import SentimentResult
from app.searchid_list.model import SearchIDList

from app.googleSearchResult.repository import GoogleSearchResult as GoogleSearchResultRepo
from app.sentimentResult.repository import SentimentResult as SentimentResultRepo
from app.alert.repository import AlertRepo, AlertSettingRepo
from app.cron_job.repository import CronHistoryRepo

weather_api_key = config("Weather_Key")
ip_address = "82.223.120.180"

db = SessionLocal()

class CronJob:
    async def weather_task(connected_clients):
        for customer_id, customer_socket in connected_clients:
            customer_ip_address = customer_socket.client.host
            weather_request = requests.get(f"http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={customer_ip_address}&aqi=no")
            if weather_request.status_code == 200:
                weather_response = json.loads(weather_request.content)
                await customer_socket.send_text(json.dumps(weather_response))
                print(customer_id, weather_response["location"]["name"]+" "+weather_response["location"]["country"], "Sent Weather API Response.")
        return True
    
    async def serpapi_task():
        print("Starting Monthly Cron Job...")
        user_list = db.query(User).filter(and_(User.role == 2, User.subscription_at != None)).all()
        for user in user_list:
            print(user.full_name)
            alert_cnt = 0
            search_id_lists = db.query(SearchIDList).filter(SearchIDList.user_id == user.id)
            for search_id_list_item in search_id_lists:
                print(search_id_list_item.search_id)
                new_search = GoogleSearch({
                    "q": search_id_list_item.keyword_url + " " + search_id_list_item.additional_keyword_url,
                    "serp_api_key": config('SerpAPI_Key_Google_Search'),
                    "location": "France",
                    "gl": "fr",
                    "start": 0,
                    "num": 150
                })
                new_search_result = new_search.get_dictionary()
                new_organic_results = new_search_result.get('organic_results')
                new_search_id = new_search_result.get("search_metadata")["id"]
                
                count = 0
                googleSearchResult_list = []
                while(count < 100):
                    try:
                        new_organic_result = new_organic_results[count]
                    except:
                        continue
                    new_sentiment_result = analysis_sentiment(f"{new_organic_result['title']} {new_organic_result['snippet'] if 'snippet' in new_organic_result else 'Unknown!'}")
                    googleSearchResult = {
                        "search_id": new_search_id,
                        "title": new_organic_result["title"],
                        "link": new_organic_result["link"],
                        "snippet": new_organic_result["snippet"] if "snippet" in new_organic_result else "Unknown!",
                        "ranking": count,
                        "keyword": new_organic_result["snippet"] if "snippet" in new_organic_result else "Unknown!",
                        "label": new_sentiment_result["label"],
                        "score": str(new_sentiment_result["score"])
                    }
                    googleSearchResult_list.append(googleSearchResult)
                    cnt += 1
                
                label_order = ["Negative", "Positive", "Neutral"]

                googleSearchResult_list = sorted(googleSearchResult_list, 
                                                key=lambda k: label_order.index(k["label"]))
                
                for i, googleSearchResult in enumerate(googleSearchResult_list):
                    googleSearchResult["ranking"] = i
                    sentimentResult = {
                        "search_id": new_search_id,
                        "label": googleSearchResult["label"],
                        "score": googleSearchResult["score"],
                    }
                    createdNewGoogleSearchResult = await GoogleSearchResultRepo.create(db, googleSearchResult)
                    createdNewSentimentResult = await SentimentResultRepo.create(db, sentimentResult)
                    print(createdNewGoogleSearchResult, createdNewSentimentResult)
                    if createdNewGoogleSearchResult == "Google Search Result item saved successfully!":
                        new_alert = {
                            "user_id": user.id,
                            "search_id": new_search_id,
                            "title": googleSearchResult["title"],
                            "site_url": googleSearchResult["link"],
                            "label": sentimentResult["label"],
                        }
                        created_alert = await AlertRepo.create(db, new_alert)
                        if created_alert != False:
                            alert_cnt += 1
                
                try:
                    db.query(GoogleSearchResult).filter(GoogleSearchResult.search_id == search_id_list_item.search_id).delete()
                    db.commit()
                    db.query(SearchIDList).\
                        filter(SearchIDList.search_id == search_id_list_item.search_id).\
                        update({SearchIDList.search_id: new_search_id})
                    db.commit()
                except Exception as e:
                    db.rollback()
                    continue
            alert_setting = await AlertSettingRepo.get_alert_setting(db, user.id)
            if alert_cnt > 0 and alert_setting.email:
                email_content = """
                    <h1>New Alerts</h1>
                    <p>Des nouvelles alertes sont remontées sur votre compte Reeact,</p>
                    <p>rendez-vous sur votre plateforme pour les visualiser.</p>
                """
                send_email(user.email, "Nouvelle alertes", email_content)
            db_googleSearch = db.query(GoogleSearchResult).\
                                join(SearchIDList, GoogleSearchResult.search_id == SearchIDList.search_id).\
                                join(SentimentResult, GoogleSearchResult.snippet == SentimentResult.keyword).\
                                filter(SearchIDList.user_id == user.id)
            total_count = db_googleSearch.count()
            positive_count = db_googleSearch.filter(SentimentResult.label == 'positive').count()
            negative_count = db_googleSearch.filter(SentimentResult.label == 'negative').count()
            cronhistory_data = {
                "user_id": user.id,
                "total_search_result": total_count,
                "positive_search_result": positive_count,
                "negative_search_result": negative_count
            }
            new_cronhistory = await CronHistoryRepo.create(db, cronhistory_data)
            
        return True
        
        