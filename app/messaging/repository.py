from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from .model import Messaging
import datetime
from app.user.model import User

class MessageRepo:
    
    async def create(db:Session, message: dict):
        try:
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(message["attachments"])
            db_message = Messaging(analysis_selection=message["analysis_selection"],
                                object_for=message["object_for"],
                                messaging=message["messaging"],
                                attachments=message["attachments"],
                                parent_id=message["parent_id"],
                                user_id=message["user_id"],
                                message_to=message["message_to"],
                                created_at=created_at,
                                updated_at=created_at,
                                admin_read_status=False,
                                user_read_status=False)
            if db_message.parent_id != -1:
                db.query(Messaging).\
                    filter(Messaging.id == db_message.parent_id).\
                    update({Messaging.admin_read_status: False,
                            Messaging.user_read_status: False})            
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            return db_message
        except Exception as e:
            print(e)
            db.rollback()
            return False
    
    async def get_all_messages(db: Session):
        try:
            result = db.query(Messaging.id,
                              User.full_name,
                              Messaging.analysis_selection,
                              Messaging.updated_at,
                              Messaging.user_read_status,
                                Messaging.admin_read_status).\
                            join(User, User.id == Messaging.user_id).\
                        filter(Messaging.parent_id == -1).\
                        order_by(Messaging.updated_at.desc()).all()
            return result
        except Exception as e:
            print(e)
            return False
    
    async def get_parent_by_id(db: Session, user_id: int):
        try:
            result = db.query(Messaging.id,
                              User.full_name,
                              Messaging.analysis_selection,
                              Messaging.object_for,
                              Messaging.updated_at,
                              Messaging.user_read_status,
                              Messaging.admin_read_status).\
                        join(User, User.id == Messaging.user_id).\
                        filter(and_(Messaging.parent_id == -1,
                                    or_(Messaging.user_id == user_id,
                                        Messaging.message_to == user_id))).\
                        order_by(Messaging.updated_at.desc()).all()
            return result
        except Exception as e:
            print(e)
            return False
    
    async def get_message_history(db: Session, message_id: int):
        try:
            original = db.query(Messaging.id,
                                Messaging.user_id,
                                User.id,
                                User.full_name,
                                Messaging.analysis_selection,
                                Messaging.object_for,
                                Messaging.messaging,
                                Messaging.message_to,
                                Messaging.parent_id,
                                Messaging.updated_at,
                                Messaging.attachments,
                                Messaging.user_read_status,
                                Messaging.admin_read_status).\
                            join(User, User.id == Messaging.user_id).\
                            filter(Messaging.id == message_id).first()
            
            history = db.query(Messaging.id,
                               Messaging.user_id,
                                User.full_name,
                                Messaging.analysis_selection,
                                Messaging.object_for,
                                Messaging.messaging,
                                Messaging.message_to,
                                Messaging.parent_id,
                                Messaging.updated_at,
                                Messaging.attachments,
                                Messaging.user_read_status,
                                Messaging.admin_read_status).\
                        join(User, User.id == Messaging.user_id).\
                        filter(Messaging.parent_id == message_id).\
                        order_by(Messaging.updated_at.desc()).all()
            res = {
                "original": original,
                "history": history
            }
            return res
        except Exception as e:
            print(e)
            return False
    
    async def check_valid_call(db: Session, user_id: int, message_id: int):
        try:
            called_message = db.query(Messaging).filter(Messaging.id == message_id).first()
            if called_message.user_id == user_id or called_message.message_to == user_id:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False
        
    async def delete_message(db: Session, msg_id: int):
        try:
            selected_msg = db.query(Messaging).filter(or_(Messaging.id == msg_id,
                                                          Messaging.parent_id == msg_id)).delete()
            db.commit()
            return selected_msg
        except Exception as e:
            print(e)
            db.rollback()
            return False
    
    async def delete_messages(db: Session, user_id: int, msg_ids: list):
        try:
            for id in msg_ids:
                selection = db.query(Messaging).\
                    filter(and_(Messaging.id == id, 
                            or_(Messaging.user_id == user_id, 
                                Messaging.message_to == user_id)))
                selection.delete()
                db.query(Messaging).filter(Messaging.parent_id == id).delete()
                db.commit()
            return True
        except Exception as e:
            print(e)
            db.rollback()
            return False
    
    async def delete_one_message(db: Session, user_id: int, msg_id: int):
        try:
            selected_msg = db.query(Messaging).\
                filter(Messaging.id == msg_id).first()
            if not selected_msg.user_id == user_id and not selected_msg.message_to == user_id:
                return False
            db.query(Messaging).filter(or_(Messaging.id == msg_id,
                                           Messaging.parent_id == msg_id)).delete()
            db.commit()
        except Exception as e:
            print(e)
            db.rollback()
            return False
        
    async def mark_as_read(db: Session, msg_id: int, read_by: bool):
        try:
            message_parent = db.query(Messaging).filter(Messaging.id == msg_id).first().parent_id
            message = db.query(Messaging).\
                filter(Messaging.id == msg_id).\
                update({Messaging.admin_read_status: 1})\
                if read_by else\
                    db.query(Messaging).\
                        filter(Messaging.id == msg_id).\
                        update({Messaging.user_read_status: 1})
            if message_parent == -1:
                db.query(Messaging).\
                filter(Messaging.parent_id == msg_id).\
                update({Messaging.admin_read_status: 1})\
                if read_by else\
                    db.query(Messaging).\
                        filter(Messaging.parent_id == msg_id).\
                        update({Messaging.user_read_status: 1})
            else:
                db.query(Messaging).\
                filter(Messaging.id == message_parent).\
                update({Messaging.admin_read_status: 1})\
                if read_by else\
                    db.query(Messaging).\
                        filter(Messaging.id == message_parent).\
                        update({Messaging.user_read_status: 1})
            db.commit()
            return message
        except Exception as e:
            print(e)
            db.rollback()
            return False
            
    async def get_unread_count(db: Session, user_id: int, user_role: str):
        try:
            res = db.query(Messaging).filter(and_(or_(Messaging.user_id == user_id,
                                                    Messaging.message_to == user_id),
                                                  Messaging.user_read_status == False)).count()\
                                                      if user_role == "Customer" else \
                db.query(Messaging).filter(Messaging.admin_read_status == False).count()
            return res
        except Exception as e:
            print(e)
            return False