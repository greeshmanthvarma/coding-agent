from fastapi import APIRouter
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv
import os
import requests
from app.database import db_dependency
from app.models import User as UserModel
import jwt
from fastapi import HTTPException

auth_router=APIRouter(prefix="/auth",tags=["auth"])

load_dotenv()


@auth_router.get("/github")
async def github_login():
    client_id = os.getenv("GITHUB_CLIENT_ID")
    redirect_uri = "http://localhost:8000/auth/callback"
    github_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=repo"
    return RedirectResponse(github_url)

@auth_router.get("/callback")
async def github_callback(code: str, db: db_dependency):
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    redirect_uri = "http://localhost:8000/auth/callback"
    data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
    }
    try:
        response = requests.post(
            "https://github.com/login/oauth/access_token", 
            data=data,
            headers={"Accept": "application/json"
            })
        token_data = response.json()
        if "access_token" not in token_data:
           return {"error":"Failed to get access token","token_data":token_data}
        access_token=token_data["access_token"]
        user_data=requests.get(
            "https://api.github.com/user",
            headers={"Authorization":f"Bearer {access_token}"}
        )
        user_data=user_data.json()
        user = db.query(UserModel).filter(UserModel.github_id == user_data["id"]).first()
        if not user:
            user = UserModel(
                username=user_data["login"],
                github_id=user_data["id"],
                avatar_url=user_data["avatar_url"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.username = user_data["login"]
            user.avatar_url = user_data["avatar_url"]
            db.commit()
        
        jwt_token = jwt.encode({"user_id": user.id}, os.getenv("JWT_SECRET"), algorithm="HS256")
        
        response = JSONResponse({
            "message": "Login Successful", 
            "user": {
                "id": user.id,
                "username": user.username,
                "avatar_url": user.avatar_url,
                "github_id": user.github_id
            }
        })
        
        response.set_cookie(
            key="token",
            value=jwt_token,
            httponly=True,
            secure=False,
            max_age=3600,
            samesite="lax"
        )
        
        return response
    except Exception as e:
        return {"error": f"Login Failed: {str(e)}"}