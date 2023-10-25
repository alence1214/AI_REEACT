import datetime, os

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from tools import get_user_id

from .repository import MessageRepo
from app.websocket.ws import connected_clients
from app.auth.auth_bearer import JWTBearer, UserRoleBearer

router = APIRouter()

@router.get("/admin/messaging", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Messaging"])
async def get_all_messages(db: Session=Depends(get_db)):
    result = await MessageRepo.get_all_messages(db)
    if result == False:
        raise HTTPException(status_code=403, detail="Database Error.")
    return result

@router.get("/admin/messaging/{msg_id}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Messaging"])
async def get_message_by_id(msg_id: int, db: Session=Depends(get_db)):
    result = await MessageRepo.get_message_history(db, msg_id)
    if result != False:
        read_status = await MessageRepo.mark_as_read(db, msg_id, True)
    print(result)
    return result

@router.post("/admin/messaging", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Messaging"])
async def post_new_message(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    message_data = await request.json()
    creation_data = {
        "analysis_selection": message_data["analysis_selection"],
        "object_for": message_data["object_for"],
        "messaging": message_data["messaging"],
        "attachments": message_data["upload_files"],
        "parent_id": -1,
        "user_id": user_id,
        "message_to": 1
    }
    res = await MessageRepo.create(db, creation_data)
    if res != False:
        await MessageRepo.mark_as_read(db, res.id, False)
    if res != False:
        for id, ws_conn in connected_clients:
            if id != user_id:
                await ws_conn.send_text("Admin send you message!")
    return res

@router.post("/admin/messaging/delete", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Messaging"])
async def post_new_message(request: Request, db: Session=Depends(get_db)):
    req_data = await request.json()
    msg_id = req_data["message_id"]
    result = await MessageRepo.delete_message(db, msg_id)
    if result == False:
        raise HTTPException(status_code=403, detail="Message is not deleted.")
    return result

@router.post("/admin/messaging/{message_id}", dependencies=[Depends(JWTBearer()), Depends(UserRoleBearer())], tags=["Admin", "Messaging"])
async def post_message(message_id: int, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    message_data = await request.json()
    creation_data = {
        "analysis_selection": message_data["analysis_selection"],
        "object_for": message_data["object_for"],
        "messaging": message_data["messaging"],
        "attachments": [],
        "parent_id": message_id,
        "user_id": user_id,
        "message_to": message_data["message_to"]
    }
    res = await MessageRepo.create(db, creation_data)
    if res != False:
        await MessageRepo.mark_as_read(db, message_id, True)
    if res != False:
        for id, ws_conn in connected_clients:
            if id == message_data["message_to"]:
                await ws_conn.send_text("Admin send you message!")
                break
    return res

@router.get("/messaging", dependencies=[Depends(JWTBearer())], tags=["Messaging"])
async def handle_message(request: Request, db: Session = Depends(get_db)):
    """
        Handle Messaging
    """
    user_id = get_user_id(request)
    res = await MessageRepo.get_parent_by_id(db, user_id)
    return res

@router.post("/upload_avatar", tags=["Upload"])
async def upload_files(request: Request):
    form_data = await request.form()
    upload_files = []
    cur_datatime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    
    for file in form_data:
        file = form_data[file]
        file_contents = await file.read()
        file_path = f"static/avatar/{cur_datatime}"
        os.makedirs(file_path, exist_ok=True)
        
        with open(f"{file_path}/{file.filename}", "wb") as f:
            f.write(file_contents)

        upload_files.append({
            "filename": file.filename,
            "filesize": file.size,
            "filepath": f"{file_path}/{file.filename}"
        })
    return upload_files

@router.post("/upload", dependencies=[Depends(JWTBearer())], tags=["Upload"])
async def upload_files(request: Request):
    user_id = get_user_id(request)
    form_data = await request.form()
    upload_files = []
    cur_datatime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    
    for file in form_data:
        file = form_data[file]
        file_contents = await file.read()
        file_path = f"static/upload_files/{user_id}/{cur_datatime}"
        os.makedirs(file_path, exist_ok=True)
        
        with open(f"{file_path}/{file.filename}", "wb") as f:
            f.write(file_contents)

        upload_files.append({
            "filename": file.filename,
            "filesize": file.size,
            "filepath": f"{file_path}/{file.filename}"
        })
    return upload_files

@router.post("/messaging", dependencies=[Depends(JWTBearer())], tags=["Messaging"])
async def post_new_message(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    message_data = await request.json()
    creation_data = {
        "analysis_selection": message_data["analysis_selection"],
        "object_for": message_data["object_for"],
        "messaging": message_data["messaging"],
        "attachments": message_data["upload_files"],
        "parent_id": -1,
        "user_id": user_id,
        "message_to": -1
    }
    res = await MessageRepo.create(db, creation_data)
    if res != False:
        await MessageRepo.mark_as_read(db, res.id, False)
    return res

@router.get("/messaging/{message_id}", dependencies=[Depends(JWTBearer())], tags=["Messaging"])
async def get_message_history(message_id: int, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    is_valid = await MessageRepo.check_valid_call(db, user_id, message_id)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid Request!")
    res = await MessageRepo.get_message_history(db, message_id)
    if res != False:
        read_status = await MessageRepo.mark_as_read(db, message_id, False)
    print(res)
    return res

@router.post("/messaging/{message_id}", dependencies=[Depends(JWTBearer())], tags=["Messaging"])
async def post_message(message_id: int, request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    is_valid = await MessageRepo.check_valid_call(db, user_id, message_id)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid Request!")
    message_data = await request.json()
    creation_data = {
        "analysis_selection": message_data["analysis_selection"],
        "object_for": message_data["object_for"],
        "messaging": message_data["messaging"],
        "attachments": [],
        "parent_id": message_id,
        "user_id": user_id,
        "message_to": -1
    }
    res = await MessageRepo.create(db, creation_data)
    if res != False:
        await MessageRepo.mark_as_read(db, message_id, False)
    return res

@router.delete("/messaging", tags=["Messaging"])
async def delete_messages(request: Request, db: Session=Depends(get_db)):
    user_id = get_user_id(request)
    req_data = await request.json()
    msg_ids = req_data["msg_ids"]
    res = await MessageRepo.delete_messages(db, user_id, msg_ids)
    return res

@router.post("/message/delete", dependencies=[Depends(JWTBearer())], tags=["Messaging"])
async def delete_one_message(request: Request, db: Session=Depends(get_db)):
    print("/messaging/delete")
    user_id = get_user_id(request)
    print(user_id)
    req_data = await request.json()
    print(req_data)
    msg_id = req_data["msg_id"]
    print(msg_id, type(msg_id))
    res = await MessageRepo.delete_one_message(db, user_id, msg_id)
    return res