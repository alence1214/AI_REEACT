from sqlalchemy.orm import Session
from sqlalchemy import and_
from .model import Alert, AlertSetting
import datetime

class AlertRepo:
    async def create(db: Session, alert_data: dict):
        try:
            created_at = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
            db_alert = Alert(user_id=alert_data["user_id"],
                            search_id=alert_data["search_id"],
                            title=alert_data["title"],
                            site_url=alert_data["site_url"],
                            label=alert_data["label"],
                            read_status=False,
                            created_at=created_at)
            db.add(db_alert)
            db.commit()
            db.refresh(db_alert)
            return db_alert
        except Exception as e:
            print("Alert Exception", e)
            return False
        
    async def get_by_user_id(db: Session, user_id: int):
        try:
            alert_setting = await AlertSettingRepo.get_alert_setting(db, user_id)
            print(alert_setting.positive, alert_setting.netural, alert_setting.negative)
            result = None
            if alert_setting.positive == True:
                result = db.query(Alert).filter(and_(Alert.user_id == user_id, Alert.label == "positive"))
            if alert_setting.negative == True:
                negative_result = db.query(Alert).filter(and_(Alert.user_id == user_id, Alert.label == "negative"))
                if result == None:
                    result = negative_result
                else:
                    result = result.union_all(negative_result)
            if alert_setting.netural == True:
                netural_result = db.query(Alert).filter(and_(Alert.user_id == user_id, Alert.label == "neutral"))
                if result == None:
                    result = netural_result
                else:
                    result = result.union_all(netural_result)
            other_result = db.query(Alert).filter(and_(Alert.user_id == user_id, Alert.label not in ["positive", "negative", "neutral"]))
            if result != None:
                result = result.union_all(other_result).order_by(Alert.created_at.desc()).all()
            return result
        except Exception as e:
            print("Alert Exception", e)
            return False
    
    async def mark_as_read(db: Session, user_id: int):
        try:
            result = db.query(Alert).filter(and_(Alert.user_id == user_id, Alert.read_status == False)).\
                update({Alert.read_status: True})
            db.commit()
            return result
        except Exception as e:
            print("Alert Exception", e)
            return False
        
    async def get_unread_count(db: Session, user_id: int):
        try:
            alert_setting = await AlertSettingRepo.get_alert_setting(db, user_id)
            result = None
            unread_count = 0
            if alert_setting.positive == True:
                result = db.query(Alert).filter(and_(Alert.user_id == user_id,
                                                     Alert.label == "positive",
                                                     Alert.read_status == False))
            if alert_setting.negative == True:
                negative_result = db.query(Alert).filter(and_(Alert.user_id == user_id,
                                                              Alert.label == "negative",
                                                              Alert.read_status == False))
                if result == None:
                    result = negative_result
                else:
                    result = result.union_all(negative_result)
            if alert_setting.netural == True:
                netural_result = db.query(Alert).filter(and_(Alert.user_id == user_id,
                                                             Alert.label == "neutral",
                                                             Alert.read_status == False))
                if result == None:
                    result = netural_result
                else:
                    result = result.union_all(netural_result)
            if result != None:
                unread_count = result.count()
            return unread_count
        except Exception as e:
            print("Alert Exception", e)
            return False
        
    async def get_limit_alert(db: Session, user_id: int, limit_cnt: int):
        try:
            alert_setting = await AlertSettingRepo.get_alert_setting(db, user_id)
            result = None
            if alert_setting.positive == True:
                result = db.query(Alert).filter(and_(Alert.user_id == user_id, Alert.label == "positive"))
            if alert_setting.negative == True:
                negative_result = db.query(Alert).filter(and_(Alert.user_id == user_id, Alert.label == "negative"))
                if result == None:
                    result = negative_result
                else:
                    result = result.union_all(negative_result)
            if alert_setting.netural == True:
                netural_result = db.query(Alert).filter(and_(Alert.user_id == user_id, Alert.label == "neutral"))
                if result == None:
                    result = netural_result
                else:
                    result = result.union_all(netural_result)
            other_result = db.query(Alert).filter(and_(Alert.user_id == user_id, Alert.label not in ["positive", "negative", "neutral"]))
            if result != None:
                result = result.union_all(other_result).order_by(Alert.created_at.desc()).all()
            return result[:3]
        except Exception as e:
            print("Alert Exception", e)
            return False
            


class AlertSettingRepo:
    async def create(db: Session, alert_setting: dict):
        try:
            db_alert_setting = AlertSetting(user_id=alert_setting['user_id'],
                                            positive=True,
                                            netural=True,
                                            negative=True,
                                            search_engine=False,
                                            blog=False,
                                            social_networks=False,
                                            email=True,
                                            sms=True,
                                            contact_frequency=0)
            db.add(db_alert_setting)
            db.commit()
            db.refresh(db_alert_setting)
            return db_alert_setting
        except Exception as e:
            print("Alert Setting Exception:", e)
            return False
        
    async def get_alert_setting(db: Session, user_id: int):
        try:
            result = db.query(AlertSetting).filter(AlertSetting.user_id == user_id).first()
            return result
        except Exception as e:
            print("Alert Setting Exception:", e)
            return False
        
    async def update_setting(db: Session, user_id: int, alert_setting_data: dict):
        try:
            result = db.query(AlertSetting).filter(AlertSetting.user_id == user_id).\
                update({AlertSetting.positive: alert_setting_data["positive"],
                        AlertSetting.negative: alert_setting_data["negative"],
                        AlertSetting.netural: alert_setting_data["netural"],
                        AlertSetting.search_engine: alert_setting_data["search_engine"],
                        AlertSetting.blog: alert_setting_data["blog"],
                        AlertSetting.social_networks: alert_setting_data["social_networks"],
                        AlertSetting.email: alert_setting_data["email"],
                        AlertSetting.sms: alert_setting_data["sms"],
                        AlertSetting.contact_frequency: alert_setting_data["contact_frequency"]})
            db.commit()
            return result
        except Exception as e:
            print("Alert Setting Exception:", e)
            return False