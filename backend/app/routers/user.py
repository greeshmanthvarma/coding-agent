from fastapi import APIRouter, Depends, HTTPException
from app.models import User as UserModel, Session as SessionModel
import requests
from pydantic import BaseModel
from app.middleware.auth import get_current_user
import uuid
import git
from datetime import datetime, timezone, timedelta
from app.database import db_dependency
from app.utils.file_cleanup import cleanup_expired_sessions, cleanup_session
user_router=APIRouter(prefix="/user",tags=["user"])

class Repo(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool

@user_router.get("/repos")
async def get_user_repos(current_user: UserModel = Depends(get_current_user)):
    try:
        repos=requests.get(
            "https://api.github.com/user/repos",
            headers={"Authorization":f"Bearer {current_user.github_token}"}
        )
        repos.raise_for_status()  # Raise exception for bad status codes
        repos=repos.json()
        repos_list=[
            Repo(
                id=repo["id"], 
                name=repo["name"],
                full_name=repo["full_name"],
                private=repo["private"]
            )for repo in repos
        ]
        return {"repos":repos_list}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user repos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@user_router.post("/repos/clone")
async def clone_repo(repo: Repo, current_user: UserModel = Depends(get_current_user), db: db_dependency = None):
    try:
        
        cleanup_expired_sessions(db)
        
        
        MAX_ACTIVE_SESSIONS = 5
        active_sessions = db.query(SessionModel).filter(
            SessionModel.user_id == current_user.id,
            SessionModel.expires_at > datetime.now(timezone.utc)
        ).count()
        
        if active_sessions >= MAX_ACTIVE_SESSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum number of active repositories ({MAX_ACTIVE_SESSIONS}) reached. Please close a repository to clone another."
            )
        
        session_id=str(uuid.uuid4())
        clone_path=f"/tmp/repo_{session_id}"
        repo_url=f"https://github.com/{repo.full_name}.git"
        git.Repo.clone_from(repo_url, clone_path)
        session=SessionModel(
            id=session_id,
            user_id=current_user.id,
            repo_id=repo.id,
            repo_name=repo.name,
            repo_url=repo_url,
            clone_path=clone_path,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return {"message": "Repo cloned successfully", "session_id": session_id}
    except HTTPException:
        # Re-raise HTTPExceptions (like the 400 for max sessions) as-is
        raise
    except git.exc.GitCommandError as e:
        import traceback
        print(f"Git clone error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to clone repo: {str(e)}")
    except Exception as e:
        import traceback
        print(f"Unexpected error in clone_repo: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@user_router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: db_dependency = None
):
    """
    Delete a specific session and its cloned repository.
    Only allows users to delete their own sessions.
    """
    try:
        # Verify session exists and belongs to user
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=404, 
                detail="Session not found or access denied"
            )
        
        # Clean up session and clone directory
        result = cleanup_session(session_id, db)
        
        if "error" in result:
            raise HTTPException(
                status_code=500, 
                detail=result.get("error")
            )
        
        return {
            "message": "Session deleted successfully",
            "session_id": session_id,
            "repo_name": session.repo_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(e)}"
        )