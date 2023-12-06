import datetime
import os

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from tools import get_user_id, zip_files

from .repository import InvoiceRepo
from app.auth.auth_bearer import JWTBearer, UserRoleBearer, SubscriptionBearer
from app.userpayment.repository import UserPaymentRepo

router = APIRouter()

@router.get("/admin/invoices", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Invoice"])
async def get_all_invoices(db: Session=Depends(get_db)):
    result = await InvoiceRepo.get_all_invoices(db)
    invoice_count = await InvoiceRepo.get_all_count(db)
    paid_invoice_count = await InvoiceRepo.get_paid_count(db)
    return {
        "invoice_count": invoice_count,
        "paid_invoice_count": paid_invoice_count,
        "invoices": result
    }
    
@router.get("/admin/invoices/{req_type}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Invoice"])
async def get_selected_invoices(req_type: str, db: Session=Depends(get_db)):
    result = None
    if req_type == "total_invoices":
        result = await InvoiceRepo.get_all_invoices(db)
    elif req_type == "paid_invoices":
        result = await InvoiceRepo.get_all_paid_invoices(db)
    elif req_type == "invoices_sent":
        result = await InvoiceRepo.get_all_sent_invoices(db)

    return {
        "invoices": result
    }

@router.get("/admin/invoice/{invoice_id}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Invoice"])
async def get_invoice_by_id(invoice_id: int, db: Session=Depends(get_db)):
    result = await InvoiceRepo.get_quote(db, invoice_id)
    if result == False:
        raise HTTPException(status_code=403, detail="Database Error.")
    return result

@router.post("/admin/invoices/download", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Invoice"])
async def admin_download_invoices(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    invoice_ids = req_data["invoice_ids"]
    
    cur_data = int(datetime.datetime.now().timestamp())
    zipfile_path = f"static/invoices/zipfiles/{len(invoice_ids)}_invoices_{str(cur_data)}.zip"
    
    invoice_paths = []
    for invoice_id in invoice_ids:
        invoice_path = await InvoiceRepo.get_invoice_pdf_path(db, invoice_id)
        if invoice_path != False and os.path.exists(invoice_path):
            invoice_paths.append(invoice_path)
            
    zip_files(invoice_paths, zipfile_path)
    return zipfile_path

@router.get("/invoices", dependencies=[Depends(JWTBearer()), Depends(SubscriptionBearer())], tags=["Invoice"])
async def get_invoices(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    result = await InvoiceRepo.get_invoices(db, user_id)
    
    return {
        "invoices": result
    }
    
@router.get("/invoice/{invoice_id}", dependencies=[Depends(JWTBearer()), Depends(SubscriptionBearer())], tags=["Invoice"])
async def get_invoice_quote(invoice_id: int, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    is_valid_invoice_request = await InvoiceRepo.check_right_request(db, invoice_id, user_id)
    if not is_valid_invoice_request:
        raise HTTPException(status_code=403, detail="Invaild request!")
    
    quote = await InvoiceRepo.get_quote(db, invoice_id)
    if quote == False:
        raise HTTPException(status_code=403, detail="Cannot Get Invoice data.")
    card_data = await UserPaymentRepo.get_default_card(db, user_id)
    if not card_data:
        raise HTTPException(status_code=403, detail="Cannot Get Payment data.")
    return {
        "quote": quote,
        "card_data": card_data
    }
    
@router.get("/invoices/{req_type}", dependencies=[Depends(JWTBearer()), Depends(SubscriptionBearer())], tags=["Invoice"])
async def get_specific_invoice(req_type: str, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    result = None
    if req_type == "total_invoices":
        result = await InvoiceRepo.get_total_invoices(db, user_id)
    elif req_type == "paid_invoices":
        result = await InvoiceRepo.get_paid_invoices(db, user_id)
    elif req_type == "unpaid_invoices":
        result = await InvoiceRepo.get_unpaid_invoices(db, user_id)
    elif req_type == "invoices_sent":
        result = await InvoiceRepo.get_sent_invoices(db, user_id)
    return {
        "invoices": result
    }

@router.post("/invoices/download", dependencies=[Depends(JWTBearer()), Depends(SubscriptionBearer())], tags=["Invoice"])
async def user_download_invoices(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    invoice_ids = req_data["invoice_ids"]
    if len(invoice_ids) == 0:
        raise HTTPException(status_code=403, detail="Please select Invoices!")
    cur_data = int(datetime.datetime.now().timestamp())
    zipfile_path = f"static/invoices/zipfiles/{len(invoice_ids)}_invoices_{str(cur_data)}.zip"
    
    invoice_paths = []
    for invoice_id in invoice_ids:
        invoice_path = await InvoiceRepo.get_invoice_pdf_path(db, invoice_id)
        if invoice_path != False:
            invoice_paths.append(invoice_path)
    
    if len(invoice_paths) == 0:
        raise HTTPException(status_code=403, detail="No Invoice Found!")
    zip_files(invoice_paths, zipfile_path)
    return zipfile_path

@router.post("/invoices/delete", dependencies=[Depends(JWTBearer()), Depends(SubscriptionBearer())], tags=["Invoice"])
async def delete_invoices(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    req_data = await request.json()
    invoice_ids = req_data["invoice_ids"]
    
    deleted_ids = []
    for invoice_id in invoice_ids:
        check_status = await InvoiceRepo.check_right_request(db, invoice_id, user_id)
        if check_status:
            result = await InvoiceRepo.delete_invoice(db, invoice_id)
            if result:
                deleted_ids.append(invoice_id)
    
    return {
        "deleted_ids": deleted_ids
    }