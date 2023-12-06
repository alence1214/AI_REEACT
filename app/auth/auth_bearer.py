from database import get_db
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth_handler import decodeJWT

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        isTokenValid: bool = False

        try:
            payload = decodeJWT(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid

class UserRoleBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(UserRoleBearer, self).__init__(auto_error=auto_error)
        
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(UserRoleBearer, self).__call__(request)
        if credentials:
            is_admin: bool = await self.check_user_role(credentials.credentials)
            if not is_admin:
                raise HTTPException(403, detail="You are not Administrator!")
            return True
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
            
    async def check_user_role(self, jwttoken: str) -> bool:
        is_admin: bool = False
        
        try:
            payload = decodeJWT(jwttoken)
        except:
            payload = None
        
        if payload:
            user_role = payload["user_role"]
            if user_role == 0 or user_role == 1:
                is_admin = True
        return is_admin
    
class SubscriptionBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(SubscriptionBearer, self).__init__(auto_error=auto_error)
        
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(SubscriptionBearer, self).__call__(request)
        if credentials:
            is_admin: bool = await self.check_subscription(credentials.credentials)
            if not is_admin:
                raise HTTPException(403, detail="You are not Subscripbed!")
            return True
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
            
    async def check_subscription(self, jwttoken: str) -> bool:
        is_subscribed: bool = False
        
        try:
            payload = decodeJWT(jwttoken)
        except:
            payload = None
        
        if payload:
            subscription_at = payload["subscription_at"]
            if subscription_at != None:
                is_subscribed = True
        return is_subscribed