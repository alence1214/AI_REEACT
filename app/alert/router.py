from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from database import get_db
from tools import get_user_id, check_user_role
from .repository import AlertRepo, AlertSettingRepo
from app.auth.auth_bearer import JWTBearer
from app.messaging.repository import MessageRepo


router = APIRouter()

@router.get("/alert", dependencies=[Depends(JWTBearer())], tags=["Alert"])
async def get_alert_data(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    alert_data = await AlertRepo.get_by_user_id(db, user_id)
    await AlertRepo.mark_as_read(db, user_id)
    print(alert_data)
    if alert_data == False:
        raise HTTPException(status_code=403, detail="Alert database error.")
    return {
        "alert_data": alert_data
    }

@router.get("/alert_setting", dependencies=[Depends(JWTBearer())], tags=["Alert"])
async def get_alert_data(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    alert_setting_data = await AlertSettingRepo.get_alert_setting(db, user_id)
    if alert_setting_data == False:
        raise HTTPException(status_code=403, detail="Alert database error.")
    return {
        "alert_setting": alert_setting_data
    }

@router.post("/alert_setting", dependencies=[Depends(JWTBearer())], tags=["Alert"])
async def change_alert_setting(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    req_data = await request.json()
    alert_setting_data = req_data["alert_setting_data"]
    result = await AlertSettingRepo.update_setting(db, user_id, alert_setting_data)
    if result == False:
        raise HTTPException(status_code=403, detail="Alert database error.")
    return result
   
@router.get("/get_unread", dependencies=[Depends(JWTBearer())], tags=["Alert"])
async def get_unread_counts(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    user_role = check_user_role(request)
    msg_unread_count = await MessageRepo.get_unread_count(db, user_id, user_role)
    alert_unread_count = await AlertRepo.get_unread_count(db, user_id) if user_role == "Customer" else 0
    return {
        "msg_unread_count": msg_unread_count,
        "alert_unread_count": alert_unread_count
    }

@router.get("/get_limit_alert", dependencies=[Depends(JWTBearer())], tags=["Alert"])
async def get_three_alert(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    print(user_id)
    result = await AlertRepo.get_limit_alert(db, user_id, 3)
    return {
        "last_three_alert": result
    }