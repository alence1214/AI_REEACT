from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, extract
from .model import Invoice
import datetime
from app.user.model import User
import json

class InvoiceRepo:
    async def create(db: Session, invoice_data: dict):
        try:
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            db_invoice = Invoice(service_detail=invoice_data["service_detail"],
                                invoice_detail=invoice_data["invoice_detail"],
                                payment_method=invoice_data["payment_method"],
                                bill_from=invoice_data["bill_from"],
                                bill_to=invoice_data["bill_to"],
                                status=invoice_data["status"],
                                total_amount=invoice_data["total_amount"],
                                stripe_id=invoice_data["stripe_id"],
                                pdf_url=invoice_data["pdf_url"],
                                created_at=created_at,
                                updated_at=created_at)
            db.add(db_invoice)
            db.commit()
            db.refresh(db_invoice)
            return db_invoice
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            db.rollback()
            return False
        
    async def delete_invoice(db: Session, invoice_id: int):
        try:
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).delete()
            db.commit()
            return invoice
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            db.rollback()
            return False
    
    async def get_all_invoices(db: Session):
        try:
            result = db.query(Invoice.id,
                            Invoice.created_at,
                            Invoice.total_amount,
                            Invoice.status,
                            Invoice.service_detail).\
                            order_by(Invoice.created_at.desc()).all()
            return result
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
    
    async def get_all_paid_invoices(db: Session):
        try:
            result = db.query(Invoice.id,
                            Invoice.created_at,
                            Invoice.total_amount,
                            Invoice.status,
                            Invoice.service_detail).\
                            filter(Invoice.status == "Completed").\
                            order_by(Invoice.created_at.desc()).all()
            return result
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
    
    async def get_all_sent_invoices(db: Session):
        try:
            result = db.query(Invoice.id,
                            Invoice.created_at,
                            Invoice.total_amount,
                            Invoice.status,
                            Invoice.service_detail).\
                            order_by(Invoice.created_at.desc()).all()
            return result
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
    
    async def get_stripe_id(db: Session, invoice_id: int, user_id: int):
        try:
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if invoice.bill_to != user_id or invoice.status != "On Hold":
                return None
            return invoice.stripe_id
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return None
    
    async def get_invoices(db: Session, user_id: int):
        try:
            invoice_res = db.query(Invoice.id,
                                   Invoice.created_at,
                                   Invoice.total_amount,
                                   Invoice.status,
                                   Invoice.service_detail).\
                            filter(or_(Invoice.bill_to == user_id, Invoice.bill_from == user_id)).\
                            order_by(Invoice.updated_at.desc())
            
            paid_invoices_count = invoice_res.filter(Invoice.status=='Completed').count()
            unpaid_invoices_count = invoice_res.filter(or_(Invoice.status=='Canceled', Invoice.status=='On Hold')).count()
            sent_invoices_count = invoice_res.filter(Invoice.bill_from == user_id).count()
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
        return {
            "paid_invoices_count": paid_invoices_count,
            "unpaid_invoices_count": unpaid_invoices_count,
            "sent_invoices_count": sent_invoices_count,
            "invoices": invoice_res.all()
        }
        
    async def get_total_invoices(db: Session, user_id: int):
        try:
            invoice_res = db.query(Invoice.id,
                                   Invoice.created_at,
                                   Invoice.total_amount,
                                   Invoice.status,
                                   Invoice.service_detail).\
                            filter(or_(Invoice.bill_to == user_id, Invoice.bill_from == user_id)).\
                            order_by(Invoice.updated_at.desc()).all()
            return invoice_res
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
    
    async def check_right_request(db: Session, invoice_id: int, user_id: int) -> bool:
        try:
            requested_invoice = db.query(Invoice).\
                filter(Invoice.id == invoice_id).first()
            if requested_invoice != None:
                if requested_invoice.bill_from == user_id or requested_invoice.bill_to == user_id:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
        
    async def get_quote(db: Session, invoice_id: int):
        try:
            requested_invoice = db.query(Invoice).\
                filter(Invoice.id == invoice_id).first()
            
            bill_to = db.query(User).filter(User.id == requested_invoice.bill_to).first()
            return {
                "service_detail": requested_invoice.service_detail,
                "date": requested_invoice.created_at,
                "bill_from": {
                    "name": "Reeact",
                    "address": "",
                    "phone_number": ""
                },
                "bill_to": {
                    "name": bill_to.full_name,
                    "address": bill_to.address,
                    "phone_number": bill_to.phone
                },
                "invoice_detail": requested_invoice.invoice_detail,
                "payment_method": requested_invoice.payment_method,
                "pdf_url": requested_invoice.pdf_url
            }
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
        
    async def get_all_count(db: Session):
        try:
            count = db.query(Invoice).count()
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
        return count
    
    async def get_paid_count(db: Session):
        try:
            count = db.query(Invoice).filter(Invoice.status == "Completed").count()
            return count
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
    
    async def get_paid_invoices(db: Session, user_id: int):
        try:
            result = db.query(Invoice.id,
                            Invoice.created_at,
                            Invoice.total_amount,
                            Invoice.status,
                            Invoice.service_detail).\
                    filter(and_(or_(Invoice.bill_to == user_id,
                                    Invoice.bill_from == user_id),
                                Invoice.status == "Completed")).\
                    order_by(Invoice.updated_at.desc()).all()
            return result
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
    
    async def get_unpaid_invoices(db: Session, user_id: int):
        try:
            result = db.query(Invoice.id,
                            Invoice.created_at,
                            Invoice.total_amount,
                            Invoice.status,
                            Invoice.service_detail).\
                    filter(and_(or_(Invoice.bill_to == user_id,
                                    Invoice.bill_from == user_id),
                                Invoice.status != "Completed")).\
                    order_by(Invoice.updated_at.desc()).all()
            return result
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
    
    async def get_sent_invoices(db: Session, user_id: int):
        try:
            result = db.query(Invoice.id,
                            Invoice.created_at,
                            Invoice.total_amount,
                            Invoice.status,
                            Invoice.service_detail).\
                    filter(Invoice.bill_from == user_id).\
                    order_by(Invoice.updated_at.desc()).all()
            return result
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
    
    async def get_invoice_pdf_path(db: Session, invoice_id):
        try:
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if invoice.pdf_url != None:
                return invoice.pdf_url
            else:
                return False
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
    
    async def complete_invoice(db: Session, invoice_id: int):
        try:
            updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            result = db.query(Invoice).filter(Invoice.id == invoice_id).\
                update({Invoice.status: "Completed",
                        Invoice.updated_at: updated_at})
            db.commit()
            return result
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
        
    async def get_daily_turnover_data(db: Session):
        try:
            cur_time = datetime.datetime.now()
            cur_weekday = cur_time.weekday()
            cur_day = cur_time.day
            cur_month = cur_time.month
            cur_year = cur_time.year
            daily_turnover_data = []
            for i in range(cur_day-cur_weekday, cur_day-cur_weekday+7):
                inscription = db.query(func.sum(Invoice.total_amount)).\
                                filter(and_(extract("day", Invoice.created_at) == i,
                                            extract("month", Invoice.created_at) == cur_month,
                                            extract("year", Invoice.created_at) == cur_year,
                                            Invoice.status == "Completed")).scalar()
                unscription = db.query(func.sum(Invoice.total_amount)).\
                                filter(and_(extract("day", Invoice.created_at) == i,
                                            extract("month", Invoice.created_at) == cur_month,
                                            extract("year", Invoice.created_at) == cur_year,
                                            Invoice.status != "Completed")).scalar()
                daily_turnover_data.append({
                    "inscription": round(inscription, 2) if inscription is not None else 0.00,
                    # "unscription": round(unscription, 2) if unscription is not None else 0.00
                })
            return daily_turnover_data
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
        
    async def get_weekly_turnover_data(db: Session):
        try:
            cur_date = datetime.date.today()
            cur_month = cur_date.month
            cur_year = cur_date.year
            cur_week = cur_date.weekday()
            first_day_of_month = datetime.date(cur_date.year, cur_date.month, 1)
            week_first_day = first_day_of_month.weekday()
            days = (cur_date - first_day_of_month).days
            weeks = days // 7
            
            weekly_turnover_data = []
            for i in range(5):
                start_date = first_day_of_month + datetime.timedelta(days=0 if i == 0 else 7 * i - week_first_day)
                start_day = start_date.day
                end_date = start_date + datetime.timedelta(days=6-week_first_day if i == 0 else 6)
                end_date = end_date if end_date <= cur_date else end_date - datetime.timedelta(days=6-cur_week)
                end_day = end_date.day
                inscription = db.query(func.sum(Invoice.total_amount)).\
                                filter(and_(extract("day", Invoice.created_at) >= start_day,
                                            extract("day", Invoice.created_at) <= end_day,
                                            extract("month", Invoice.created_at) == cur_month,
                                            extract("year", Invoice.created_at) == cur_year,
                                            Invoice.status == "Completed")).scalar()
                unscription = db.query(func.sum(Invoice.total_amount)).\
                                filter(and_(extract("day", Invoice.created_at) >= start_day,
                                            extract("day", Invoice.created_at) <= end_day,
                                            extract("month", Invoice.created_at) == cur_month,
                                            extract("year", Invoice.created_at) == cur_year,
                                            Invoice.status != "Completed")).scalar()
                weekly_turnover_data.append({
                    "inscription": round(inscription, 2) if inscription is not None else 0.00,
                    # "unscription": round(unscription, 2) if unscription is not None else 0.00
                })
            return weekly_turnover_data
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
    
    async def get_monthly_turnover_data(db: Session):
        try:
            cur_time = datetime.datetime.now()
            cur_month = cur_time.month
            cur_year = cur_time.year
            monthly_turnover_data = []
            for i in range(1, 13):
                inscription = db.query(func.sum(Invoice.total_amount)).\
                                filter(and_(extract("month", Invoice.created_at) == i,
                                            extract("year", Invoice.created_at) == cur_year,
                                            Invoice.status == "Completed")).scalar()
                unscription = db.query(func.sum(Invoice.total_amount)).\
                                filter(and_(extract("month", Invoice.created_at) == i,
                                            extract("year", Invoice.created_at) == cur_year,
                                            Invoice.status != "Completed")).scalar()
                monthly_turnover_data.append({
                    "inscription": round(inscription, 2) if inscription is not None else 0.00,
                    # "unscription": round(unscription, 2) if unscription is not None else 0.00
                })
            return monthly_turnover_data
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False
        
    async def get_weekly_wallet_useage(db: Session, user_id: int, month: int=None, year: int=None):
        try:
            cur_date = datetime.date.today() if month == None and year == None else datetime.date(year if month<12 else year+1, month+1 if month<12 else 1, 1) - datetime.timedelta(days=1)
            cur_month = month if month else cur_date.month
            cur_year = year if year else cur_date.year
            cur_week = cur_date.weekday()
            first_day_of_month = datetime.date(cur_date.year, cur_date.month, 1)
            week_first_day = first_day_of_month.weekday()
            days = (cur_date - first_day_of_month).days
            weeks = days // 7
            
            weekly_wallet_useage_data = []
            for i in range(5):
                start_date = first_day_of_month + datetime.timedelta(days=0 if i == 0 else 7 * i - week_first_day)
                start_day = start_date.day
                end_date = start_date + datetime.timedelta(days=6-week_first_day if i == 0 else 6)
                end_date = end_date if end_date <= cur_date else end_date - datetime.timedelta(days=6-cur_week)
                end_day = end_date.day
                inscription = db.query(func.sum(Invoice.total_amount)).\
                                filter(and_(extract("day", Invoice.created_at) >= start_day,
                                            extract("day", Invoice.created_at) <= end_day,
                                            extract("month", Invoice.created_at) == cur_month,
                                            extract("year", Invoice.created_at) == cur_year,
                                            Invoice.status == "Completed",
                                            Invoice.bill_to == user_id)).scalar()
                weekly_wallet_useage_data.append(round(inscription, 2) if inscription is not None else 0.00)
            return weekly_wallet_useage_data
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False

    async def get_daily_wallet_useage(db: Session, user_id: int):
        try:
            cur_time = datetime.datetime.now()
            cur_weekday = cur_time.weekday()
            cur_day = cur_time.day
            cur_month = cur_time.month
            cur_year = cur_time.year
            daily_turnover_data = []
            for i in range(cur_day-cur_weekday, cur_day+1):
                inscription = db.query(func.sum(Invoice.total_amount)).\
                                filter(and_(extract("day", Invoice.created_at) == i,
                                            extract("month", Invoice.created_at) == cur_month,
                                            extract("year", Invoice.created_at) == cur_year,
                                            Invoice.status == "Completed",
                                            Invoice.bill_to == user_id)).scalar()
                unscription = db.query(func.sum(Invoice.total_amount)).\
                                filter(and_(extract("day", Invoice.created_at) == i,
                                            extract("month", Invoice.created_at) == cur_month,
                                            extract("year", Invoice.created_at) == cur_year,
                                            Invoice.status != "Completed",
                                            Invoice.bill_to == user_id)).scalar()
                daily_turnover_data.append({
                    "inscription": round(inscription, 2) if inscription is not None else 0.00,
                    "unscription": round(unscription, 2) if unscription is not None else 0.00
                })
            return daily_turnover_data
        except Exception as e:
            print("InvoiceRepo Exception:", e)
            return False