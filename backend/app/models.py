from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    github_id = Column(Integer, unique=True)
    username = Column(String, unique=True)
    avatar_url = Column(String)
    github_token = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    sessions = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"
    id= Column(String, primary_key=True)
    user_id= Column(Integer, ForeignKey("users.id"))
    repo_id= Column(Integer)
    repo_name= Column(String)
    repo_url= Column(String)
    clone_path= Column(String)
    created_at= Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at= Column(DateTime)
    user= relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")
    reviews = relationship("Review", back_populates="session")

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    message = Column(String)
    sender = Column(String)
    sequence= Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session = relationship("Session", back_populates="messages")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    prompt = Column(Text)  # User's original prompt
    changes = Column(Text)  # JSON string of file changes made by agent
    checkpoint_commit_hash = Column(String)  # Git commit hash before agent made changes (for revert)
    status = Column(String, default="pending_review")  # pending_review, approved, rejected
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    commit_message = Column(String, nullable=True)  # User's commit message if approved
    branch_name = Column(String, nullable=True)  # Branch name if approved
    session = relationship("Session", back_populates="reviews")
