from fastapi import HTTPException, Cookie, Depends
from fastapi.security import HTTPBearer
from app.database import db_dependency
from app.models import User as UserModel
import jwt
import os


async def get_current_user(token: str= Cookie(None), db: db_dependency = None):
    
    if not token:
        raise HTTPException(status_code=401, detail="No token found")
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        user_id = payload["user_id"]
        user=db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")