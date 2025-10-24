from sqlalchemy import Column, Integer, String, Boolean, Sequence
from app.database import Base



class User(Base):
    __tablename__ = "users"
    id= Column(Integer,primary_key=True,autoincrement=True)
    github_id=Column(Integer,unique=True)
    username=Column(String,unique=True)
    avatar_url=Column(String)
    
