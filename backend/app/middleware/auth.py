from fastapi import HTTPException, Cookie, Depends
from fastapi.security import HTTPBearer
from app.database import db_dependency
from app.models import User as UserModel
from sqlalchemy.orm import Session
import jwt
import os


def get_user_from_token(token: str, db: Session):
    """
    Helper function to get user from JWT token.
    Can be used by both HTTP endpoints and WebSocket endpoints.
    """
    if not token:
        raise HTTPException(status_code=401, detail="No token found")
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        user_id = payload["user_id"]
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")


async def get_current_user(token: str = Cookie(None), db: db_dependency = None):
    """
    Get current user from JWT token in cookie (for HTTP endpoints).
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database dependency not injected")
    return get_user_from_token(token, db)