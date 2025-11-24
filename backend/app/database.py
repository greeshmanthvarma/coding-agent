from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends
import redis

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
from app.models import User, Session as SessionModel, Message as MessageModel, Review as ReviewModel
Base.metadata.create_all(bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    try:
        yield r
    finally:
        r.close()

redis_dependency = Annotated[redis.Redis, Depends(get_redis)]
db_dependency = Annotated[Session, Depends(get_db)]
