from stripe import Webhook

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from tools import get_user_id, get_google_search_analysis

from .stripe_manager import StripeManager
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import decode_email_verify_JWT
from app.user.repository import UserRepo
from app.email_verify.repository import EmailVerifyRepo
from app.invoice.repository import InvoiceRepo
from app.searchid_list.repository import SearchIDListRepo
from app.intervention.repository import InterventionRepo
from app.promo_code.repository import PromoCodeRepo
from app.cron_job.repository import CronHistoryRepo
from app.googleSearchResult.repository import GoogleSearchResult

router = APIRouter()

@router.post("/stripe/pay_for_signup", tags=["Stripe"])
async def pay_for_signup(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    user_data = req_data["user_data"]
    payment_data = req_data["payment_data"]
    promo_code = req_data["promo_code"] if "promo_code" in req_data else None
    
    email_verify_token = req_data["email_verify_token"] if "email_verify_token" in req_data else None
    if email_verify_token == None:
        raise HTTPException(status_code=400, detail="No Email Verify Token.")
    email_verify_payload = decode_email_verify_JWT(email_verify_token)
    if email_verify_payload == False:
        raise HTTPException(status_code=400, detail="Invalid Token!")
    if user_data["email"] != email_verify_payload["email"]:
        raise HTTPException(status_code=400, detail="Token doesn't match.")
    verify_result = await EmailVerifyRepo.check_verify_code(db, email_verify_payload["email"], email_verify_payload["verify_code"])
    if verify_result != True:
        raise HTTPException(status_code=400, detail=verify_result)
    
    email_verify_delete = await EmailVerifyRepo.delete(db, email_verify_payload["email"])
    print(email_verify_delete)
    
    db_user = await UserRepo.fetch_by_email(db, email=user_data['email'])
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists!")
    
    new_customer = await StripeManager.create_customer(user_data)
    # new_payment_method = await StripeManager.create_payment_method(payment_data)
    # print(f"New payment method: {new_payment_method}")
    
    if new_customer != None:
        
        new_payment_method = await StripeManager.link_test_card_to_customer(new_customer.stripe_id)
        await StripeManager.set_default_payment_method(new_customer.stripe_id, new_payment_method.stripe_id)
        
        subscription_for_signup = await StripeManager.pay_for_monthly_usage(new_customer.stripe_id, promo_code)
        
        return {
            "customer_id": new_customer.stripe_id,
            "payment_method_id": new_payment_method.stripe_id,
            "subscription_at": subscription_for_signup.stripe_id
        }
    
    return False

@router.post("/stripe/pay_for_invoice/{invoice_id}", dependencies=[Depends(JWTBearer())], tags=["Stripe"])
async def pay_for_invoice(invoice_id: int, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    invoice_stripe_id = await InvoiceRepo.get_stripe_id(db, invoice_id, user_id)
    result = await StripeManager.pay_for_invoice(invoice_stripe_id)
    if result == None:
        raise HTTPException(status_code=403, detail="Pay for Invoice Failed!")
    await InvoiceRepo.complete_invoice(db, invoice_id)
    await InterventionRepo.complete_request(db, user_id, invoice_id)
    return True

@router.post("/stripe/pay_for_new_keywordurl", dependencies=[Depends(JWTBearer())], tags=["Stripe"])
async def pay_for_new_keywordurl(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    req_data = await request.json()
    new_keywordurl = req_data["new_keywordurl"]
    check_duplicate = await SearchIDListRepo.check_keyword_duplicate(db, user_id, new_keywordurl)
    if not check_duplicate:
        raise HTTPException(status_code=403, detail="This keyword already exists.")
    
    subscription_id = await UserRepo.get_subscription_id(db, user_id)
    customer_id = await StripeManager.get_cus_id_from_sub_id(subscription_id)
    subscription_for_new_keywordurl = await StripeManager.pay_for_new_keywordurl(customer_id)
    
    if customer_id == None or subscription_for_new_keywordurl==None:
        raise HTTPException(status_code=403, detail="Stripe Error")
    
    invoice_data = await StripeManager.create_invoice_data_from_subscription_id(subscription_for_new_keywordurl, user_id)
    result = await InvoiceRepo.create(db, invoice_data)
    
    gs_result = await get_google_search_analysis(db, user_id, new_keywordurl, 0, 50, subscription_for_new_keywordurl)
    
    gs_statistics = await GoogleSearchResult.get_reputation_score(db, user_id)
    cronhistory_data = {
        "user_id": user_id,
        "total_search_result": gs_statistics["total_count"],
        "positive_search_result": gs_statistics["positive_count"],
        "negative_search_result": gs_statistics["negative_count"]
    }
    new_cronhistory = await CronHistoryRepo.update(db, user_id, cronhistory_data)
    
    return {
        "subscription":subscription_for_new_keywordurl,
        "gs_result": gs_result,
        "new_keywordurl": new_keywordurl
    }

@router.post("/stripe/create_payment_intent", dependencies=[Depends(JWTBearer())], tags=["Stripe"])
async def create_payment_intent(user_id: int, amount: int, db: Session=Depends(get_db)):
    try:
        
        subscription_id = await UserRepo.get_subscription_id(user_id, db)
        customer_id = await StripeManager.get_cus_id_from_sub_id(subscription_id)
        payment_intent_id = await StripeManager.create_payment_intent(customer_id, amount)
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=403, detail=str(e))
    
    return payment_intent_id

@router.post("/stripe/checkout_intent", dependencies=[Depends(JWTBearer())], tags=["Stripe"])
async def create_intent_checkout_session(paymentintent_id: str):
    try:
        
        session_id = await StripeManager.create_intent_checkout_session(paymentintent_id)
        return session_id
    
    except Exception as e:
        
        print(e)
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/webhook", tags=["Stripe"])
async def handle_webhook(event: Request):
    sig_header = event.headers["Stripe-Signature"]
    event_data = await event.json()
    payload = event_data["data"]
    endpoint_secret = "whsec_87384c0981bf9157b12277372d7a43ab8510217e3f33c79fcfccc4d5d9321ff5"

    try:
        event = Webhook.construct_event(payload, sig_header, endpoint_secret)
        # Handle the event based on its type
        if event["type"] == "invoice.payment_succeeded":
            # Handle successful payment event
            # Access event data using event["data"]["object"]
            print("invoice.payment_succeeded")
        elif event["type"] == "invoice.payment_failed":
            # Handle failed payment event
            # Access event data using event["data"]["object"]
            pass
        elif event["type"] == "product.created":
            print("product.created")
        else:
            # Handle other event types
            pass
    except ValueError as e:
        # Invalid payload or signature
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stipe/check_promocode", tags=["Stripe"])
async def check_promocode(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    code_title = req_data["code_title"]
    try:
        promo_code = await PromoCodeRepo.get_promocode_by_title(db, code_title)
        if promo_code == False:
            raise HTTPException(status_code=403, detail="Can't get data from DB.")
        if promo_code == "Promocode doesn't exist.":
            raise HTTPException(status_code=403, detail=promo_code)
        check_promo_code = await StripeManager.check_promo_code(promo_code.stripe_id)
        if not check_promo_code:
            raise HTTPException(status_code=400, detail="Promotion code is not vailde!")
        return promo_code
    except Exception as e:
        print("Promocode Exception:", e)
        raise HTTPException(status_code=403, detail=str(e))