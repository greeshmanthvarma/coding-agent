from fastapi import APIRouter, Depends, HTTPException
from app.models import User as UserModel, Session as SessionModel
import requests
from pydantic import BaseModel
from app.middleware.auth import get_current_user
import uuid
import git
from datetime import datetime, timezone, timedelta
from app.database import db_dependency
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
    except git.exc.GitCommandError as e:
        raise HTTPException(status_code=500, detail=f"Failed to clone repo: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")