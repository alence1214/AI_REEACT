from typing import Any
from sqlalchemy.orm import Session
from .model import InterventionResponse
import datetime
import json
from app.intervention.model import InterventionRequest

class InterventionResponseRepo:
    async def create(db: Session, inter_response: dict):
        try:
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            db_inter_response = InterventionResponse(request_id=inter_response["requested_id"],
                                                    response_type=inter_response["response_type"],
                                                    response=inter_response["response"],
                                                    created_at=created_at,
                                                    updated_at=created_at,
                                                    status=False,
                                                    respond_to=inter_response["respond_to"])
            db.add(db_inter_response)
            db.commit()
            db.refresh(db_inter_response)
        except Exception as e:
            print(e)
            db.rollback()
            return False
        return db_inter_response
    
    async def get_information_by_request_id(db: Session, request_id: int):
        try:
            res = db.query(InterventionResponse.id,
                           InterventionResponse.request_id,
                           InterventionResponse.response,
                           InterventionResponse.respond_to,
                           InterventionResponse.response_type,
                           InterventionResponse.status,
                           InterventionResponse.created_at).\
                filter(InterventionResponse.request_id == request_id).\
                order_by(InterventionResponse.created_at).all()
            return res
        except Exception as e:
            print(e)
            return False
    
    async def get_quote_by_request_id(db: Session, request_id: int):
        try:
            res = db.query(InterventionResponse).filter(InterventionResponse.request_id == request_id, InterventionResponse.response_type == 1).first()
            quote_id = json.loads(res.response)
        except Exception as e:
            print(e)
            return False
        return quote_id
    
    async def mark_as_read(db: Session, request_id: int):
        try:
            result = db.query(InterventionResponse).filter(InterventionResponse.request_id == request_id).\
                        update({InterventionResponse.status: True})
            db.commit()
            return result
        except Exception as e:
            print(e)
            db.rollback()
            return False