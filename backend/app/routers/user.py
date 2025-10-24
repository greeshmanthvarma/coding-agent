from app.database import db_dependency
from fastapi import APIRouter
from pydantic import BaseModel
from app.models import User as UserModel
user_router=APIRouter(prefix="/user",tags=["user"])

class User(BaseModel):
    username:str
    github_id:int
    avatar_url:str

@user_router.post('/create')
def create_user(user:User,db:db_dependency):
    new_user=UserModel(username=user.username,email=user.email,avatar_url=user.avatar_url)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user