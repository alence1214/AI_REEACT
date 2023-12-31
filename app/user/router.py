import time, datetime
import pandas as pd
from decouple import config

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from tools import get_user_id, get_google_search_analysis, send_email

from .repository import UserRepo
from app.websocket.ws import connected_clients
from app.auth.auth_bearer import JWTBearer, UserRoleBearer, SubscriptionBearer
from app.auth.auth_handler import signJWT, generateJWT, decode_token, decode_email_verify_JWT
from app.alert.repository import AlertSettingRepo
from app.invoice.repository import InvoiceRepo
from app.intervention.repository import InterventionRepo
from app.cron_job.repository import CronHistoryRepo
from app.googleSearchResult.repository import GoogleSearchResult
from app.searchid_list.repository import SearchIDListRepo
from app.userpayment.repository import UserPaymentRepo
from app.stripe_manager.stripe_manager import StripeManager
from app.email_verify.repository import EmailVerifyRepo

from . import schema as userSchema

router = APIRouter()

@router.get("/admin/users", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "User"])
async def get_all_user(db: Session = Depends(get_db)):
    """Get all user list

    Raises:
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    
    db_all_users = await UserRepo.get_all_user_table(db)
    user_count = len(db_all_users)
    active_user_count = await UserRepo.get_active_user_count(db)
    intervention_count = await InterventionRepo.get_all_count(db)
    invoice_count = await InvoiceRepo.get_all_count(db)
    return {
        "user_count": user_count,
        "active_user_count": active_user_count,
        "intervention_count": intervention_count,
        "invoice_count": invoice_count,
        "user_data": db_all_users
    }

@router.get("/admin/users/{req_type}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "User"])
async def get_specific_users(req_type: str, db: Session=Depends(get_db)):
    result = None
    if req_type == "active_accounts":
        result = await UserRepo.get_active_user_table(db)
    else:
        result = await UserRepo.get_all_user_table(db)
    return {
        "user_data": result
    }
    
@router.post("/admin/users", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "User"])
async def create_new_user(request: Request, db: Session=Depends(get_db)):
    request_data = await request.json()
    user_data = request_data["user_data"]
    db_user = await UserRepo.fetch_by_email(db, email=user_data['email'])
    if db_user:
        raise HTTPException(status_code=400, detail="L'utilisateur existe déjà!")
    db_user = await UserRepo.fetch_by_username(db, username=user_data['full_name'])
    if db_user:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà!")

    result = await UserRepo.create(db, user_data)
    if result == False:
        raise HTTPException(status_code=400, detail="Échec de la création de l'utilisateur !")
    
    payload = {
        "user_id": result.id,
        "email": result.email,
        "full_name": result.full_name,
        "time": time.time()
    }
    token = generateJWT(payload)

    add_token = await UserRepo.add_forgot_password_token(db, result.id, token)
    if add_token == False:
        raise HTTPException(status_code=400, detail="Échec de l'ajout du jeton.")
    
    welcome_msg = f"""
    <html>
        <body>
            <h2>Bonjour {result.full_name}</h2>
            <p>Reeact vous invite à rejoindre votre interface d’analyse via le lien ci dessous :</p>
            <p><a href="{config("SITE_URL")}/forgot-password?token={token}">Reset Password!</a></p>
            <p>Voici votre identifiant de connexion :</p>
            <p>{result.email}</p>x
            <img src="{config("SITE_URL")}/static/logoblue.png" alt="Reeact"></img>
        </body>
    </html>
    """
    await send_email(result.email, "Bienvenue sur Reeact!", welcome_msg)
    
    return result
    
@router.get("/admin/user/{user_id}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "User"])
async def get_user_by_id(user_id: int, db: Session=Depends(get_db)):
    user = await UserRepo.get_user_by_id(db, user_id)
    keyword_url_data = await SearchIDListRepo.get_item_by_user_id(db, user_id)
    return {
        "user_data": user,
        "keyword_url_data": keyword_url_data
    }

@router.post("/admin/activate_user", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "User"])
async def activate_user(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    user_id = req_data['user_id']
    is_activate = req_data['activated']
    if user_id == None or is_activate == None:
        raise HTTPException(status_code=403, detail="Erreur de données de demande !")
    res = await UserRepo.activate_user(db, user_id, is_activate)
    if res == False:
        raise HTTPException(status_code=403, detail="DB Error!")
    return {
        "result": True
    }

@router.get("/admin/setting", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "User"])
async def get_my_user_data(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    result = await UserRepo.get_user_by_id(db, user_id)
    return result

@router.post("/admin/setting", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "User"])
async def update_my_user_data(user_data: userSchema.UserUpdate, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    user_data.role = 0
    token = user_data.forgot_password_token
    origin_user_data = await UserRepo.get_user_by_id(db, user_id)
    if origin_user_data.full_name != user_data.full_name:
        check_username = await UserRepo.fetch_by_username(db, user_data.full_name)
        if check_username:
            raise HTTPException(status_code=403, detail="Nom d'utilisateur existe déjà.")
    if origin_user_data.email != user_data.email:
        check_email = await UserRepo.fetch_by_email(db, user_data.email)
        if check_email:
            raise HTTPException(status_code=403, detail="L'e-mail existe déjà.")
        check_token = await UserRepo.check_password_forgot_token(db, token)
        if check_token == False:
            raise HTTPException(status_code=403, detail="jeton invalide")
    result = await UserRepo.update_user_by_id(db, user_data, user_id)
    return result

@router.get("/admin/statistics/", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Statistics"])
async def get_statistics(db: Session=Depends(get_db)):
    cur_date = datetime.datetime.now()
    cur_month = cur_date.month
    cur_year = cur_date.year
    pre_month = cur_month - 1 if cur_month != 1 else 12
    pre_year = cur_year if cur_month != 1 else cur_year - 1
    pre1_month = pre_month - 1 if pre_month != 1 else 12
    pre1_year = pre_year if pre_month != 1 else pre_year - 1
    pre_month_acc = await UserRepo.get_monthly_acc_count(db, pre_year, pre_month)
    pre1_month_acc = await UserRepo.get_monthly_acc_count(db, pre1_year, pre1_month)
    acc_count = await UserRepo.get_daily_acc_data(db)
    turnover_data = await InvoiceRepo.get_daily_turnover_data(db)
    intervention_data = await InterventionRepo.get_daily_intervention_data(db)
    statistics_data = {
        "active_account": len(connected_clients),
        "cur_month_acc": pre_month_acc,
        "pre_month_acc": pre1_month_acc,
        "acc_count": acc_count,
        "turnover_data": turnover_data,
        "intervention_data": intervention_data
    }
    return statistics_data

@router.get("/admin/statistics/{req_type}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Statistics"])
async def get_statistics(req_type: str, db: Session=Depends(get_db)):
    cur_date = datetime.datetime.now()
    cur_month = cur_date.month
    cur_year = cur_date.year
    pre_month = cur_month - 1 if cur_month != 1 else 12
    pre_year = cur_year if cur_month != 1 else cur_year - 1
    pre1_month = pre_month - 1 if pre_month != 1 else 12
    pre1_year = pre_year if pre_month != 1 else pre_year - 1
    pre_month_acc = await UserRepo.get_monthly_acc_count(db, pre_year, pre_month)
    pre1_month_acc = await UserRepo.get_monthly_acc_count(db, pre1_year, pre1_month)
    acc_count = None
    turnover_data = None
    intervention_data = None
    
    if req_type == None or req_type == "today":
        acc_count = await UserRepo.get_daily_acc_data(db)
        turnover_data = await InvoiceRepo.get_daily_turnover_data(db)
        intervention_data = await InterventionRepo.get_daily_intervention_data(db)
    elif req_type == "weekly":
        acc_count = await UserRepo.get_weekly_acc_data(db)
        turnover_data = await InvoiceRepo.get_weekly_turnover_data(db)
        intervention_data = await InterventionRepo.get_weekly_intervention_data(db)
    elif req_type == "monthly":
        acc_count = await UserRepo.get_monthly_acc_data(db)
        turnover_data = await InvoiceRepo.get_monthly_turnover_data(db)
        intervention_data = await InterventionRepo.get_monthly_intervention_data(db)
    month_name = ["Janvier", "Février", "Mars", "Avril", "Peut", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    statistics_data = {
        "active_account": len(connected_clients),
        "pre_month": month_name[pre_month-1],
        "pre_month_acc": pre_month_acc,
        "pre1_month": month_name[pre1_month-1],
        "pre1_month_acc": pre1_month_acc,
        "acc_count": acc_count,
        "turnover_data": turnover_data,
        "intervention_data": intervention_data
    }
    return statistics_data

@router.get("/admin/turnover/download/{req_type}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Statistics"])
async def download_statistics(req_type: str, db: Session=Depends(get_db)):
    cur_time = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    file_path = f"static/invoices/{cur_time}.xlsx"

    user_list = await UserRepo.get_customers(db)
    statistics_data = []
    for user in user_list:
        user_statistic = dict()
        user_statistic["Customer Name"] = user.full_name
        user_statistic["Subscription Date"] = await StripeManager.get_subscription_start_date(user.subscription_at)
        user_statistic["Amount Pack Base"] = "29 €" if user.subscription_at != None else ""
        additional_word = await SearchIDListRepo.get_item_by_user_id(db, user.id)
        user_statistic["Amount Additional Words"] = len(additional_word) - 1
        user_statistic["Amount Total"] = str(29 + 10 * (len(additional_word) - 1))+" €"
        
        print(user_statistic)
        statistics_data.append(user_statistic)
        
    df = pd.DataFrame(statistics_data)

    with pd.ExcelWriter(f"static/invoices/{cur_time}.xlsx") as writer:
        df.to_excel(writer, index=False)
    return {"file_path": file_path}

@router.post("/user/signup", tags=["User"])
async def create_user(user_request: Request, db: Session = Depends(get_db)):
    """
        Create a User and store it in the database
    """
    request_data = await user_request.json()
    user_data = request_data['user_data']
    # payment_data = request_data['payment_data']
    
    email_verify_token = request_data["email_verify_token"] if "email_verify_token" in request_data else None
    # if email_verify_token == None:
    #     raise HTTPException(status_code=400, detail="No Email Verify Token.")
    # email_verify_payload = decode_email_verify_JWT(email_verify_token)
    # if email_verify_payload == False:
    #     raise HTTPException(status_code=400, detail="Invalid Token!")
    # if user_data["email"] != email_verify_payload["email"]:
    #     raise HTTPException(status_code=400, detail="Token doesn't match.")
    # verify_result = await EmailVerifyRepo.check_verify_code(db, email_verify_payload["email"], email_verify_payload["verify_code"])
    # if verify_result != True:
    #     raise HTTPException(status_code=400, detail=verify_result)
    
    db_user = await UserRepo.fetch_by_email(db, email=user_data['email'])
    if db_user:
        raise HTTPException(status_code=400, detail="L'email existe déjà!")
    db_user = await UserRepo.fetch_by_username(db, username=user_data['full_name'])
    if db_user:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà!")
    user_data["email_verified"] = True
    user_data["payment_verified"] = False
    
    new_customer = await StripeManager.create_customer(user_data)
    if new_customer == None:
        raise HTTPException(status_code=400, detail="La création du client Stripe a échoué !")
    
    user_data["stripe_id"] = new_customer.stripe_id
    
    created_user = await UserRepo.create(db=db, user=user_data)
    if created_user == False:
        await StripeManager.delete_customer(new_customer.stripe_id)
        raise HTTPException(status_code=403, detail="La création de l'utilisateur a échoué !")
    
    created_user_alert_setting = await AlertSettingRepo.create(db, {"user_id": created_user.id})
    
    # card_data = await StripeManager.get_card_data_by_id(payment_data.get("payment_method_id"))
    # if type(card_data) != dict:
    #     raise HTTPException(status_code=403, detail="Cannot get card data.")
    
    # card_data["card_holdername"] = payment_data.get("card_holdername")
    
    # created_payment = await UserPaymentRepo.create(db=db, userpayment=card_data, user_id=created_user.id)
    # if created_payment == False:
    #     raise HTTPException(status_code=403, detail="UserPaymentRepo Creation is Failed!")
    
    # set_default = await UserPaymentRepo.set_as_default(db, created_user.id, created_payment.id)
    # if not set_default:
    #     raise HTTPException(status_code=403, detail="Set Default Payment Failed.")
    
    # invoice_data = await StripeManager.create_invoice_data_from_subscription_id(created_user.subscription_at, created_user.id)
    # if type(invoice_data) == str:
    #     raise HTTPException(status_code=403, detail=invoice_data)
    
    # result = await InvoiceRepo.create(db, invoice_data)
    # if result == False:
    #     raise HTTPException(status_code=403, detail="InvoiceRepo Creation is Failed!")
    
    gs_result = None
    if user_data["keyword_url"] != '':
        gs_result = await get_google_search_analysis(db, created_user.id, user_data["keyword_url"], 0, 100)
        if gs_result == False:
            await UserRepo.delete_user(db, created_user.id)
            await StripeManager.delete_customer(new_customer.stripe_id)
            raise HTTPException(status_code=403, detail="La création des résultats de recherche Google a échoué !")
    
    # gs_statistics = await GoogleSearchResult.get_reputation_score(db, created_user.id)
    # cronhistory_data = {
    #     "user_id": created_user.id,
    #     "total_search_result": gs_statistics.get("total_count"),
    #     "positive_search_result": gs_statistics.get("positive_count"),
    #     "negative_search_result": gs_statistics.get("negative_count")
    # }
    # new_cronhistory = await CronHistoryRepo.create(db, cronhistory_data)
    # await EmailVerifyRepo.delete(db, created_user.email)
    
    jwt = signJWT(created_user.id, user_data['email'], created_user.role, created_user.subscription_at)
    welcome_msg = f"""
    <html>
        <body>
            <h2>Bonjour {created_user.full_name}</h2>
            <p>Nous sommes ravis de vous accueillir en tant que nouvel utilisateur de la plateforme Reeact!</p>
            <p>Nous sommes impatients de travailler avec vous et de vous offrir le meilleur service possible.</p>
            <p>Si vous avez des questions ou des besoins spécifiques, n'hésitez pas à nous contacter.</p>
            <p>Bonne analyse!<br/>L’équipe Reeact</p>
            <img src="{config("SITE_URL")}/static/logoblue.png" alt="Reeact"></img>
        </body>
    </html>
    """
    await send_email(created_user.email, "Bienvenue sur Reeact!", welcome_msg)
    
    admin_maile_content = f"""
    <html>
        <body>
            <h2>Bonjour!</h2>
            <p>Un nouvel utilisateur s’est inscrit sur votre plateforme, voici les informations d’inscriptions :</p>
            <p>{created_user.full_name}</p>
            <p>{created_user.email}</p>
            <p>Merci!<br/>L’équipe Reeact</p>
            <img src="{config("SITE_URL")}/static/logoblue.png" alt="Reeact"></img>
        </body>
    </html>
    """
    admin_list = await UserRepo.get_admins_data(db)
    for admin in admin_list:
        await send_email(admin.email, "Nouveau utilisateur", admin_maile_content)
    
    return {
        "user": created_user,
        "jwt": jwt,
        "gs_result": gs_result,
        # "new_cronhistory": new_cronhistory
    }

@router.post("/user/login", tags=["User"])
async def login(user_request: userSchema.UserLogin, db: Session = Depends(get_db)):
    """
        Login User with Email and Password
    """
    db_user = await UserRepo.fetch_by_email_password(db, email=user_request.email, password=user_request.password)
    if db_user != "L'utilisateur n'existe pas!" and db_user != "Le mot de passe n'est pas correct!" and db_user != "L'utilisateur est suspendu." and db_user != False:
        # if db_user.role == 2 and db_user.subscription_at == None:
        #     create_date = datetime.datetime.strptime(db_user.created_at, "%Y-%m-%d").date()
        #     unsubscribe_date = datetime.datetime.strptime(db_user.updated_at, "%Y-%m-%d").date()
        #     expire_year = unsubscribe_date.year
        #     expire_month = unsubscribe_date.month + 1 if create_date.day <= unsubscribe_date.day else unsubscribe_date.month
        #     expire_day = create_date.day
        #     expire_year = expire_year + 1 if expire_month == 13 else expire_year
        #     expire_month = 1 if expire_month == 13 else expire_month
        #     expire_date = datetime.date(expire_year, expire_month, expire_day)
        #     if datetime.date.today() > expire_date:
        #         raise HTTPException(status_code=400, detail="Your Subscription Date Expired!")
        jwt = signJWT(db_user.id, db_user.email, db_user.role, db_user.subscription_at)
        return {
            "user": db_user,
            "jwt": jwt
        }
    else:
        raise HTTPException(status_code=400, detail=db_user)

@router.get("/password_forgot/{email}", tags=["User"])
async def password_forgot(email: str, db: Session=Depends(get_db)):
    email_confirm = await UserRepo.fetch_by_email(db, email)
    if not email_confirm:
        raise HTTPException(status_code=403, detail="L'utilisateur n'existe pas.")
    payload = {
        "user_id": email_confirm.id,
        "email": email,
        "full_name": email_confirm.full_name,
        "time": time.time()
    }
    token = generateJWT(payload)
    email_body = f"""
    <html>
        <body>
            <p>Bonjour!</p>
            <p>Si cette demande ne vous appartient pas, veuillez ignorer ce message.</p>
            <p>S'il vous plaît allez à <a href="{config("SITE_URL")}/forgot-password?token={token}">réinitialiser le mot de passe</a>.</p>
            <p>Veuillez saisir le code du site !</p>
        </body>
    </html>
    """
    add_token = await UserRepo.add_forgot_password_token(db, email_confirm.id, token)
    if add_token == False:
        raise HTTPException(status_code=400, detail="Échec de l'ajout du jeton.")
    send_result = await send_email(email, "Réinitialiser le mot de passe!", email_body)
    if send_result == False:
        raise HTTPException(status_code=400, detail="E-mail non envoyé !")
    return "Email sent successfully!"

@router.post("/password_forgot", tags=["User"])
async def check_password_forgot_token(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    token = req_data["token"]
    check_token = await UserRepo.check_password_forgot_token(db, token)
    if check_token == False:
        raise HTTPException(status_code=403, detail="jeton invalide")
    return True

@router.post("/change_password", tags=["user"])
async def change_password(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    token = req_data["token"]
    password = req_data["password"]
    payload = decode_token(token)
    
    check_token = await UserRepo.check_password_forgot_token(db, token)
    if check_token == False:
        raise HTTPException(status_code=403, detail="jeton invalide")
    
    user_id = payload["user_id"] if "user_id" in payload else None
    if user_id == None:
        raise HTTPException(status_code=403, detail="jeton invalide")
    user = userSchema.UserUpdate(forgot_password_token=" ",
                                password=password,
                                email=payload["email"],
                                full_name=payload["full_name"])
    change_password = await UserRepo.update_user_by_id(db, user, user_id)
    if change_password == False:
        raise HTTPException(status_code=403, detail="Échec de la mise à jour du mot de passe.")
    return "Password updated successfully."

@router.get("/user/dashboard", dependencies=[Depends(JWTBearer())], tags=["Dashboard"])
async def get_dashboard_data(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    reputation_score = await GoogleSearchResult.get_reputation_score(db, user_id)
    cron_history = await CronHistoryRepo.get_history(db, user_id)
    weekly_wallet_useage = await InvoiceRepo.get_weekly_wallet_useage(db, user_id)
    pre_month = datetime.date.today().month - 1 if datetime.date.today().month != 1 else 12
    pre_year = datetime.date.today().year if datetime.date.today().month != 1 else datetime.date.today().year - 1
    pre_weekly_wallet_useage = await InvoiceRepo.get_weekly_wallet_useage(db, user_id, pre_month, pre_year)
    daily_wallet_useage = await InvoiceRepo.get_daily_wallet_useage(db, user_id)
    inter_req_data = await InterventionRepo.get_daily_intervention_data_by_user_id(db, user_id)
    default_card_data = await UserPaymentRepo.get_default_card(db, user_id)
    cron_score = await CronHistoryRepo.get_reputation_score(db, user_id)
    return {
        "reputation_score": reputation_score,
        "cron_history": cron_history,
        "cron_score": cron_score,
        "weekly_wallet_useage": weekly_wallet_useage,
        "pre_weekly_wallet_useage": pre_weekly_wallet_useage,
        "daily_wallet_useage": daily_wallet_useage,
        "inter_req_data": inter_req_data,
        "latest_card_data": default_card_data
    }
    
@router.get("/user/setting", dependencies=[Depends(JWTBearer())], tags=["User"])
async def get_user_profile(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    user_data = await UserRepo.get_user_by_id(db, user_id)
    payment_data = await UserPaymentRepo.get_payment_by_user_id(db, user_id)
    keyword_url_data = await SearchIDListRepo.get_item_by_user_id(db, user_id)
    if user_data == False:
        HTTPException(status_code=403, detail="Database Error!")
    return {
        "user_data": user_data,
        "payment_data": payment_data,
        "keyword_url_data": keyword_url_data
    }

@router.post("/user/setting", dependencies=[Depends(JWTBearer())], tags=["User"])
async def update_my_user_data(user_data: userSchema.UserUpdate, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    token = user_data.forgot_password_token
    origin_user_data = await UserRepo.get_user_by_id(db, user_id)
    if origin_user_data.full_name != user_data.full_name:
        check_username = await UserRepo.fetch_by_username(db, user_data.full_name)
        if check_username:
            raise HTTPException(status_code=403, detail="Nom d'utilisateur existe déjà.")
    if origin_user_data.email != user_data.email:
        check_email = await UserRepo.fetch_by_email(db, user_data.email)
        if check_email:
            raise HTTPException(status_code=403, detail="L'e-mail existe déjà.")
        check_token = await UserRepo.check_password_forgot_token(db, token)
        if check_token == False:
            raise HTTPException(status_code=403, detail="jeton invalide")
    result = await UserRepo.update_user_by_id(db, user_data, user_id)
    return result

@router.put("/user/update/{user_id}", dependencies=[Depends(JWTBearer())], tags=["User"])
async def update_user(user_id: int, user_request: userSchema.UserUpdate, db: Session = Depends(get_db)):
    """
        Update User with id
    """
    
    db_user = await UserRepo.update_user_by_id(db, user=user_request, id=user_id)
    if db_user != "User not exist to update":
        return {
            "updated_user": db_user
        }
    return {
        "status": db_user
    }
    
@router.get("/user/unsubscribe", dependencies=[Depends(JWTBearer), Depends(SubscriptionBearer())], tags=["User"])
async def unsubscribe_signup(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    subscription_id = await UserRepo.get_subscription_id(db, user_id)
    unsubscribe = await StripeManager.unsubscribe(subscription_id)
    if unsubscribe == False:
        raise HTTPException(status_code=403, detail="Stripe Error!")
    update_user = await UserRepo.unsubscribe(db, user_id)
    if update_user == False:
        raise HTTPException(status_code=403, detail="Database Error!")
    jwt = signJWT(update_user.id, update_user.email, update_user.role, update_user.subscription_at)
    return {
        "jwt": jwt
    }

@router.get("/user/delete_keyword/{keyword_id}", dependencies=[Depends(JWTBearer()), Depends(SubscriptionBearer())], tags=["User"])
async def delete_keyword_url(keyword_id: int, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    valid_keyword = await SearchIDListRepo.check_valid(db, user_id, keyword_id)
    if valid_keyword == False:
        raise HTTPException(status_code=403, detail="Requête invalide!")
    subscription_id = await SearchIDListRepo.get_subscription_id(db, keyword_id)
    if subscription_id == False or subscription_id == None:
        raise HTTPException(status_code=403, detail="Impossible de supprimer ce mot-clé.")
    unsubscribe = await StripeManager.unsubscribe(subscription_id)
    if unsubscribe == False:
        raise HTTPException(status_code=403, detail="Stripe Error!")
    unsubscribe_from_db = await SearchIDListRepo.unsubscribe_item(db, keyword_id)
    if unsubscribe_from_db == False:
        raise HTTPException(status_code=403, detail="Database Error!")
    return "Sucessfully removed!"