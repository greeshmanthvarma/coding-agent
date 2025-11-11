from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.services.agent_service import GeminiAgentService
from app.database import db_dependency, redis_dependency
from app.models import Session as SessionModel
from app.models import Message as MessageModel
from app.middleware.auth import get_current_user
from fastapi.responses import StreamingResponse
import json
import os
from app.models import Review as ReviewModel
from app.models import User as UserModel
from app.utils.git_utils import revert_to_checkpoint, commit_changes, push_changes
from pydantic import BaseModel
from datetime import datetime, timezone

class ApproveReviewRequest(BaseModel):
    commit_message: str
    branch_name: str = None


agent_router=APIRouter(prefix="/agent",tags=["agent"])

@agent_router.websocket("/stream/{session_id}")
async def stream_agent_output(websocket: WebSocket, session_id: str):
    """
    Stream agent output to the client.
    Requires JWT token in query parameter: ?token=...
    """
    await websocket.accept()
    
    from app.database import get_db, get_redis
    
    db = next(get_db())
    redis = next(get_redis())
    
    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Authentication token required")
            return
        
        try:
            from app.middleware.auth import get_user_from_token
            current_user = get_user_from_token(token, db)
        except HTTPException as e:
            await websocket.close(code=1008, reason=e.detail)
            return
        
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id, 
            SessionModel.user_id == current_user.id
        ).first()
        if not session:
            await websocket.close(code=1008, reason="Session not found or access denied")
            return
        
        data=await websocket.receive_text()
        request_data=json.loads(data)
        prompt=request_data.get("prompt")

        if not prompt:
            await websocket.close(code=1008, reason="Prompt is required")
            return
        
        agent_service=GeminiAgentService()
        async for update in agent_service.execute(prompt, session_id, db=db, redis=redis):
            await websocket.send_json(update)
        
    except WebSocketDisconnect:
        await websocket.close(code=1000, reason="WebSocket disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"An error occurred: {str(e)}"
        })
        await websocket.close(code=1000, reason="WebSocket disconnected")
    finally:
        db.close()
        redis.close()

@agent_router.get("/{session_id}/messages")
async def get_past_messages(
    session_id: str,
    db: db_dependency,
    redis: redis_dependency,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all messages for a session (cache-first, then DB).
    Works for both active and deleted sessions (preserves chat history).
    Returns messages in chronological order.
    """
    from app.models import Message as MessageModel
    
    # Check if session exists and belongs to user, or if messages exist for this session_id
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    # If session doesn't exist, verify ownership through messages
    if not session:
        # Check if any messages exist for this session_id and belong to the user
        message_check = db.query(MessageModel).filter(
            MessageModel.session_id == session_id,
            MessageModel.user_id == current_user.id
        ).first()
        
        if not message_check:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    agent_service = GeminiAgentService()
    messages = agent_service.get_messages_for_api(session_id, redis, db)
    
    return {
        "session_id": session_id,
        "messages": messages,
        "total": len(messages)
    }

@agent_router.get("/review/{review_id}")
async def get_review_details(
    review_id: str, 
    db: db_dependency,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get details of a review including changes made by agent.
    """
    review = db.query(ReviewModel).filter(
        ReviewModel.id == review_id, 
        ReviewModel.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found or access denied")
    
    changes = None
    if review.changes:
        try:
            changes = json.loads(review.changes)
        except json.JSONDecodeError:
            changes = {"error": "Failed to parse changes"}
    
    review = {
        "id": review.id,
        "session_id": review.session_id,
        "prompt": review.prompt,
        "changes": changes,
        "checkpoint_commit_hash": review.checkpoint_commit_hash,
        "status": review.status,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "approved_at": review.approved_at.isoformat() if review.approved_at else None,
        "rejected_at": review.rejected_at.isoformat() if review.rejected_at else None,
        "commit_message": review.commit_message,
        "branch_name": review.branch_name
    }
    return review

@agent_router.post("/review/{review_id}/approve")
async def approve_review(
    review_id: str, 
    request: ApproveReviewRequest, 
    db: db_dependency,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Approve a review and commit changes to the repository.
    """

    try:
        review_result=db.query(ReviewModel).filter(ReviewModel.id == review_id, ReviewModel.user_id == current_user.id).first()
        if not review_result:
            raise HTTPException(status_code=404, detail="Review not found")
        session=db.query(SessionModel).filter(SessionModel.id == review_result.session_id, SessionModel.user_id == current_user.id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        working_directory=session.clone_path
        if not os.path.exists(working_directory):
            raise HTTPException(status_code=404, detail="Cloned repository not found")
        if review_result.status != "pending_review":
            raise HTTPException(status_code=400, detail="Review is not pending review")

        result = commit_changes(working_directory, request.commit_message, request.branch_name)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result.get("error"))

        review_result.status = "approved"
        review_result.approved_at = datetime.now(timezone.utc)
        review_result.commit_message = request.commit_message
        review_result.branch_name = result.get("branch_name")
        db.commit()
        return {
        "message": "Review approved and changes committed",
        "review_id": review_id,
        "commit_hash": result.get("commit_hash"),
        "branch_name": result.get("branch_name")
        }
    except HTTPException: #To catch the HTTPException raised in the try block
        raise 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving review: {str(e)}")

@agent_router.post("/review/{review_id}/reject")
async def reject_review(
    review_id: str,
    db: db_dependency,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Reject a review and revert changes to the repository.
    """
    try:
        review_result=db.query(ReviewModel).filter(ReviewModel.id == review_id, ReviewModel.user_id == current_user.id).first()
        if not review_result:
            raise HTTPException(status_code=404, detail="Review not found")
        
        session=db.query(SessionModel).filter(SessionModel.id == review_result.session_id, SessionModel.user_id == current_user.id).first()
        
        if review_result.status != "pending_review":
            raise HTTPException(status_code=400, detail="Review is not pending review")
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        working_directory=session.clone_path
        checkpoint_commit_hash=review_result.checkpoint_commit_hash
        
        if not os.path.exists(working_directory):
            raise HTTPException(status_code=404, detail="Cloned repository not found")
        

        result = revert_to_checkpoint(working_directory, checkpoint_commit_hash)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        review_result.status = "rejected"
        review_result.rejected_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return {
        "message": "Review rejected and changes reverted",
        "review_id": review_id
        }
    except HTTPException: #To catch the HTTPException raised in the try block
        raise 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rejecting review: {str(e)}")

@agent_router.post("/review/{review_id}/push")
async def push_review(
    review_id: str,
    db: db_dependency,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Push changes to the remote repository.
    Only works if review is approved.
    """
    try:
        review_result = db.query(ReviewModel).filter(
            ReviewModel.id == review_id, 
            ReviewModel.user_id == current_user.id
        ).first()
        
        if not review_result:
            raise HTTPException(status_code=404, detail="Review not found or access denied")
        
        if review_result.status != "approved":
            raise HTTPException(status_code=400, detail="Review must be approved before pushing")
        
        session = db.query(SessionModel).filter(
            SessionModel.id == review_result.session_id, 
            SessionModel.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or access denied")

        working_directory = session.clone_path
        if not os.path.exists(working_directory):
            raise HTTPException(status_code=404, detail="Cloned repository not found")
        
        if not review_result.branch_name:
            raise HTTPException(status_code=400, detail="No branch name found. Review must be approved first.")
        
        if not current_user.github_token:
            raise HTTPException(status_code=400, detail="GitHub token not found. Please re-authenticate.")
        
        result = push_changes(
            working_directory, 
            review_result.branch_name, 
            current_user.github_token, 
            session.repo_url
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        review_result.status = "pushed"
        db.commit()
        
        return {
            "message": "Review pushed to the repository",
            "review_id": review_id,
            "branch_name": result.get("branch_name"),
            "repo_url": result.get("repo_url")
        }
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pushing review: {str(e)}")