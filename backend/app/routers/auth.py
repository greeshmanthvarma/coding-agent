from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import os
import requests
auth_router=APIRouter(prefix="/auth",tags=["auth"])
load_dotenv()


@auth_router.get("/github")
async def github_login():
    client_id = os.getenv("GITHUB_CLIENT_ID")
    redirect_uri = "http://localhost:8000/auth/callback"
    github_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=repo"
    return RedirectResponse(github_url)

@auth_router.get("/callback")
async def github_callback(code: str):
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
        response = requests.post("https://github.com/login/oauth/access_token", data=data,headers={"Accept": "application/json"})
        token_data = response.json()
        if "access_token" in token_data:
            print(token_data)
            return {"message":"Login Successful","token_data":token_data}
        else:
            return {"error":"Login Failed","token_data":token_data}
    except Exception as e:
        return {"error":"Login Failed","error":e}
    