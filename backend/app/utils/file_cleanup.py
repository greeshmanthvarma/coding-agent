import os
import shutil
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Session as SessionModel

load_dotenv()

def cleanup_expired_sessions(db: Session = None):
    """
    Clean up all expired sessions and their clone directories.
    Returns count of cleaned sessions.
    """
    if db is None:
        db = SessionLocal()
        try:
            result = cleanup_expired_sessions(db)
            return result
        finally:
            db.close()
    
    try:
        now = datetime.now(timezone.utc)
        expired_sessions = db.query(SessionModel).filter(
            SessionModel.expires_at < now
        ).all()
        
        cleaned_count = 0
        for session in expired_sessions:
            if session.clone_path and os.path.exists(session.clone_path):
                try:
                    shutil.rmtree(session.clone_path)
                except Exception as e:
                    print(f"Warning: Failed to remove {session.clone_path}: {e}")
            

            db.delete(session)
            cleaned_count += 1
        
        db.commit()
        return {"message": f"Cleaned up {cleaned_count} expired session(s)", "count": cleaned_count}
    except Exception as e:
        db.rollback()
        return {"error": f"Error cleaning up expired sessions: {str(e)}"}

def cleanup_session(session_id: str, db: Session = None):
    """
    Clean up a specific session and its clone directory.
    """
    if db is None:
        db = SessionLocal()
        try:
            result = cleanup_session(session_id, db)
            return result
        finally:
            db.close()
    
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        
        if not session:
            return {"error": f"Session {session_id} not found"}
        
        if session.clone_path and os.path.exists(session.clone_path):
            try:
                shutil.rmtree(session.clone_path)
            except Exception as e:
                return {"error": f"Failed to remove clone directory: {str(e)}"}
        
        db.delete(session)
        db.commit()
        
        return {"message": f"Session {session_id} and clone directory cleaned up"}
    except Exception as e:
        db.rollback()
        return {"error": f"Error cleaning up session: {str(e)}"}
