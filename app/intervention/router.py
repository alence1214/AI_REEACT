from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from tools import get_user_id, check_user_role

from fastapi import Query, Path

from .repository import InterventionRepo
from app.auth.auth_bearer import JWTBearer, UserRoleBearer
from app.intervention_response.repository import InterventionResponseRepo
from app.invoice.repository import InvoiceRepo
from app.stripe_manager.stripe_manager import StripeManager
from app.user.repository import UserRepo
from app.googleSearchResult.repository import GoogleSearchResult
from app.alert.repository import AlertRepo

router = APIRouter()

@router.get("/admin/interventions", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Intervention"])
async def get_all_interventions(db: Session=Depends(get_db)):
    result = await InterventionRepo.get_all_interventions(db)
    interventions_in_progress = await InterventionRepo.get_all_intervention_in_progress(db)
    pending_interventions = await InterventionRepo.get_all_intervention_in_pending(db)
    return {
        "total_count": len(result),
        "in_progress_count": len(interventions_in_progress),
        "pending_count": len(pending_interventions),
        "interventions": result
    }

@router.get("/admin/intervention_request/{inter_id}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Intervention"])
async def get_inter_request_data(inter_id: int, db: Session=Depends(get_db)):
    inter_data = await InterventionRepo.get_inter_by_id(db, inter_id)
    if inter_data == False or inter_data == None:
        raise HTTPException(status_code=403, detail="Intervention DB error.")
    mark_as_read = await InterventionRepo.update_read_status(db, inter_id, True, True)
    print(mark_as_read)
    return {
        "inter_data": inter_data
    }

@router.get("/admin/interventions/{req_type}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Intervention"])
async def get_all_interventions(req_type: str=Path(...), inter_type: str=Query(default=None), db: Session=Depends(get_db)):
    result = None
    if req_type == "today":
        result = await InterventionRepo.get_daily_intervention_data(db, inter_type)
    elif req_type == "weekly":
        result = await InterventionRepo.get_weekly_intervention_data(db, inter_type)
    elif req_type == "monthly":
        result = await InterventionRepo.get_monthly_intervention_data(db, inter_type)
    
    if result == False:
        raise HTTPException(status_code=403, detail="Intervention DB error.")
    
    return result
        

@router.get("/admin/intervention/{intervention_id}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Intervention"])
async def get_intervention_by_id(intervention_id: int, db: Session=Depends(get_db)):
    result = await InterventionResponseRepo.get_information_by_request_id(db, intervention_id)
    if result == False:
        raise HTTPException(status_code=403, detail="Database Error.")
    mark_as_read = await InterventionRepo.update_read_status(db, intervention_id, True, True)
    print(mark_as_read)
    return result

@router.post("/admin/intervention/{intervention_id}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Intervention"])
async def post_intervention_response(intervention_id: int, user_request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(user_request)
    res_data = await user_request.json()
    if res_data["response_type"] == 0:
        user_role = check_user_role(user_request)
        
        inter_response_data = {
            "requested_id": intervention_id,
            "response_type": res_data["response_type"],
            "response": res_data["information"],
            "respond_to": 0
        }
        inter_response_create = await InterventionResponseRepo.create(db, inter_response_data)
        
        inter_data = await InterventionRepo.get_inter_by_id(db, intervention_id)
        user_data = await UserRepo.get_user_by_id(db, user_id)
        alert_data = {
            "user_id": inter_data['user_id'],
            "search_id": user_data.avatar_url,
            "title": f"Reeact posez une question sur votre demande de service sur {inter_data['site_url']}",
            "site_url": inter_data['site_url'],
            "label": "Intervention"
        }
        alert_result = await AlertRepo.create(db, alert_data)
        print(alert_result)
        
        await InterventionRepo.request_approved(db, intervention_id)
        return inter_response_create
    
    elif res_data["response_type"] == 1:
        check_quote_sent = await InterventionRepo.check_quote_sent(db, intervention_id)
        if check_quote_sent == True:
            raise HTTPException(status_code=403, detail="Quote already sent.")
        amount = res_data["amount"]
        description = res_data["description"]
        requested_user_id = await InterventionRepo.get_user_id(db, intervention_id)
        subscription_id = await UserRepo.get_subscription_id(db, requested_user_id)
        customer_id = await StripeManager.get_cus_id_from_sub_id(subscription_id)
        invoice_id = await StripeManager.create_invoice(customer_id, amount, description)
        invoice_data = await StripeManager.create_invoice_data_from_invoice_id(invoice_id, requested_user_id)
        new_invoice = await InvoiceRepo.create(db, invoice_data)
        if subscription_id == None or customer_id == None or invoice_id == None or invoice_data == None or new_invoice == False:
            raise HTTPException(status_code=403, detail="Error")
        
        updated_inter = await InterventionRepo.update_status(db, intervention_id, 2)
        inter_response_data = {
            "requested_id": intervention_id,
            "response_type": 1,
            "response": '{"quote":'+ str(new_invoice.id) +'}',
            "respond_to": 0
        }
        inter_res = await InterventionResponseRepo.create(db, inter_response_data)
        
        inter_data = await InterventionRepo.get_inter_by_id(db, intervention_id)
        user_data = await UserRepo.get_user_by_id(db, user_id)
        alert_data = {
            "user_id": inter_data['user_id'],
            "search_id": user_data.avatar_url,
            "title": f"React a envoyé un devis concernant votre demande de service à {inter_data['site_url']}",
            "site_url": inter_data['site_url'],
            "label": "Intervention"
        }
        alert_result = await AlertRepo.create(db, alert_data)
        print(alert_result)
        
        return new_invoice

    elif res_data["response_type"] == 2:
        result = await InterventionRepo.reject_intervention(db, intervention_id)
        
        inter_data = await InterventionRepo.get_inter_by_id(db, intervention_id)
        user_data = await UserRepo.get_user_by_id(db, user_id)
        alert_data = {
            "user_id": inter_data['user_id'],
            "search_id": user_data.avatar_url,
            "title": f"React a rejeté votre demande de service sur {inter_data['site_url']}",
            "site_url": inter_data['site_url'],
            "label": "Intervention"
        }
        alert_result = await AlertRepo.create(db, alert_data)
        print(alert_result)
        
        return result
    mark = await InterventionRepo.update_read_status(db, intervention_id, False, False)
    return mark

@router.get("/intervention_requests", dependencies=[Depends(JWTBearer())], tags=["Intervention"])
async def get_interventions(user_request:Request, db: Session=Depends(get_db)):
    user_id = get_user_id(user_request)
    result = await InterventionRepo.get_daily_intervention_data_by_user_id(db, user_id)
    
    return {
        "intervention_requests": result
    }

@router.get("/intervention_requests/{req_type}", dependencies=[Depends(JWTBearer())], tags=["Intervention"])
async def get_interventions(req_type: str, user_request:Request, db: Session=Depends(get_db)):
    user_id = get_user_id(user_request)
    result = await InterventionRepo.get_by_user_id(db, user_id)
    if req_type == "today":
        result = await InterventionRepo.get_daily_intervention_data_by_user_id(db, user_id)
    elif req_type == "weekly":
        result = await InterventionRepo.get_weekly_intervention_data_by_user_id(db, user_id)
    elif req_type == "monthly":
        result = await InterventionRepo.get_monthly_intervention_data_by_user_id(db, user_id)
    
    return {
        "intervention_requests": result
    }

@router.get("/intervention_requests/information/{intervention_id}", dependencies=[Depends(JWTBearer())], tags=["Intervention"])
async def get_intervention(intervention_id: int, user_request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(user_request)
    is_valid_intervention_request = await InterventionRepo.check_valid_user(db, user_id, intervention_id)
    if not is_valid_intervention_request:
        raise HTTPException(status_code=403, detail="Invaild request!")
    
    result = await InterventionResponseRepo.get_information_by_request_id(db, intervention_id)
    
    mark_as_read = await InterventionRepo.update_read_status(db, intervention_id, False, True)
    print(mark_as_read)
    return result

@router.post("/intervention_requests/information/{intervention_id}", dependencies=[Depends(JWTBearer())], tags=["Intervention"])
async def post_intervention_response(intervention_id: int, user_request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(user_request)
    is_valid_intervention_request = await InterventionRepo.check_valid_user(db, user_id, intervention_id)
    if not is_valid_intervention_request:
        raise HTTPException(status_code=403, detail="Invaild request!")
    
    res_data = await user_request.json()
    
    user_role = check_user_role(user_request)
    inter_response_data = {
        "requested_id": intervention_id,
        "response_type": res_data["response_type"],
        "response": res_data["information"],
        "respond_to": 1
    }
    inter_response_create = await InterventionResponseRepo.create(db, inter_response_data)
    
    inter_data = await InterventionRepo.get_inter_by_id(db, intervention_id)
    user_data = await UserRepo.get_user_by_id(db, user_id)
    alert_data = {
        "user_id": -1,
        "search_id": user_data.avatar_url,
        "title": f"{user_data.full_name} réponds à ta question sur {inter_data['site_url']}",
        "site_url": inter_data['site_url'],
        "label": "Intervention"
    }
    alert_result = await AlertRepo.create(db, alert_data)
    
    await InterventionRepo.update_datetime(db, intervention_id)
    
    mark = await InterventionRepo.update_read_status(db, intervention_id, True, False)
    
    return inter_response_create

@router.get("/intervention_requests/quote/{intervention_id}", dependencies=[Depends(JWTBearer())], tags=["Intervention"])
async def get_intervention(intervention_id: int, user_request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(user_request)
    is_valid_intervention_request = await InterventionRepo.check_valid_user(db, user_id, intervention_id)
    if not is_valid_intervention_request:
        raise HTTPException(status_code=403, detail="Invaild request!")
    
    result = await InterventionResponseRepo.get_quote_by_request_id(db, intervention_id)
    mark_as_read = await InterventionRepo.update_read_status(db, intervention_id, intervention_id, False, True)
    print(mark_as_read)
    return result

@router.post("/intervention_requests", dependencies=[Depends(JWTBearer())], tags=["Intervention"])
async def intervention_request(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    inter_data = await request.json()
    intervention_data = {
        "title": inter_data["title"],
        "information": inter_data["information"],
        "additional_information": inter_data["additional_information"],
        "site_url": inter_data["site_url"],
    }
    check_request_status = await GoogleSearchResult.check_request_status(db, inter_data["id"])
    if check_request_status == False:
        raise HTTPException(status_code=403, detail="Request already sent!")
    result = await InterventionRepo.create(db, intervention_data, user_id)
    
    user_data = await UserRepo.get_user_by_id(db, user_id)
    print(user_data)
    alert_data = {
        "user_id": -1,
        "search_id": user_data.avatar_url,
        "title": f"{user_data.full_name} a envoyé une demande de service concernant {inter_data['site_url']}",
        "site_url": inter_data['site_url'],
        "label": "Intervention"
    }
    alert_result = await AlertRepo.create(db, alert_data)
    print(alert_result)
    if result == False:
        raise HTTPException(status_code=403, detail="InterventionRepo Creation Failed!")
    request_status = await GoogleSearchResult.update_request_status(db, inter_data["id"], True)
    return result