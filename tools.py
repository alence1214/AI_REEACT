import smtplib
import zipfile

from serpapi import GoogleSearch
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from transformers import pipeline
from decouple import config
from sqlalchemy.orm import Session

from app.googleSearchResult.repository import GoogleSearchResult
from app.sentimentResult.repository import SentimentResult
from app.searchid_list.repository import SearchIDListRepo

from fastapi import Request

from app.auth.auth_handler import decodeJWT

# SMTP server details
smtp_server = "mail.gandi.net"
smtp_port = 587
smtp_username = "register@reeact.io"
smtp_password = "register@reeact.io"
sender_email = "register@reeact.io"

# sentiment_pipeline = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
sentiment_pipeline = pipeline("sentiment-analysis",
                              model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
                              tokenizer="cardiffnlp/twitter-xlm-roberta-base-sentiment")
def analysis_sentiment(text):
    data = [text]
    analysis = sentiment_pipeline(data)[0]
    response = { "text": text, "label": analysis['label'].lower(), "score": analysis['score'] }
    
    return response

def remove_http(string):
    if string.startswith("https://"):
        return string[8:]
    elif string.startswith("http://"):
        return string[7:]
    else:
        return string

def get_user_id(request: Request):
    bearer_token = request.headers["Authorization"]
    jwt_token = bearer_token[7:]
    payload = decodeJWT(jwt_token)
    user_id = payload.get("user_id")
    return user_id

def check_user_role(request: Request):
    bearer_token = request.headers["Authorization"]
    jwt_token = bearer_token[7:]
    payload = decodeJWT(jwt_token)
    user_role = payload.get("user_role")
    if user_role == 0 or user_role == 1:
        return "Admin"
    elif user_role == 2:
        return "Customer"
    
def check_file_type(filename):
    allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf']  # Add more allowed extensions if needed
    file_extension = filename.rsplit('.', 1)[-1].lower()
    if file_extension in allowed_extensions:
        return True
    else:
        return False
    
def zip_files(file_paths, zip_name):
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for file in file_paths:
            zipf.write(file)
            
async def send_email(email: str, subject: str, email_body: str):    
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = subject
    
    msg.attach(MIMEText(email_body, "html"))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", str(e))
        return False

async def get_google_search_analysis(db: Session, user_id: int, search_keyword: str, start: int, num: int, stripe_id: str=None):
    try:
        if num:
            search = GoogleSearch({
                "q": search_keyword,
                "location": "France",
                "gl": "fr",
                "serp_api_key": config('SerpAPI_Key_Google_Search'),
                "start": start,
                "num": 150
            })
            
            search_result = search.get_dictionary()
            
            search_id = search_result.get("search_metadata")["id"]
            
            organic_results = search_result.get('organic_results')
            count = 0
            googleSearchResult_list = []
            while(count < num):
                try:
                    organic_result = organic_results[count]
                except:
                    continue
                sentiment_result = analysis_sentiment(f"{organic_result['title']} {organic_result['snippet'] if 'snippet' in organic_result else 'Unknown!'}")
                googleSearchResult = {
                    "search_id": search_id,
                    "title": organic_result["title"],
                    "link": organic_result["link"],
                    "snippet": organic_result["snippet"] if "snippet" in organic_result else "Unknown!",
                    "ranking": count,
                    "keyword": organic_result["snippet"] if "snippet" in organic_result else "Unknown!",
                    "label": sentiment_result["label"],
                    "score": str(sentiment_result["score"])
                }
                googleSearchResult_list.append(googleSearchResult)
            
            label_order = ["Negative", "Positive", "Neutral"]

            googleSearchResult_list = sorted(googleSearchResult_list, 
                                            key=lambda k: label_order.index(k["label"]))
            
            for i, googleSearchResult in enumerate(googleSearchResult_list):
                googleSearchResult["ranking"] = i
                sentimentResult = {
                    "search_id": search_id,
                    "label": googleSearchResult["label"],
                    "score": googleSearchResult["score"]
                }
                createdSentimentResult = await SentimentResult.create(db=db, sentimentResult=sentimentResult)
                createdGoogleSearchResult = await GoogleSearchResult.create(db=db, googleSearchResult=googleSearchResult)
            
            searchid_list = {
                "user_id": user_id,
                "search_id": search_id,
                "keyword_url": search_keyword,
                "stripe_id": stripe_id
            }
            await SearchIDListRepo.create(db, searchid_list)
            return {
                "search_id": search_id,
                "status": "Search successfully!!!"
            }
    except Exception as e:
        print(e)
        return False
