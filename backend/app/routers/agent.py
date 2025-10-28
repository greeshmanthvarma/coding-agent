from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.services.agent_service import GeminiAgentService
from app.database import db_dependency
from app.models import Session as SessionModel
from app.middleware.auth import get_current_user
from fastapi.responses import StreamingResponse
import json
agent_router=APIRouter(prefix="/agent",tags=["agent"])

@agent_router.websocket("/stream/{session_id}")
async def stream_agent_output( websocket: WebSocket,session_id: str, db: db_dependency = None):
    await websocket.accept()
    try:
        user_id=websocket.query_params.get("user_id")
        if not user_id:
            await websocket.close(code=1008, reason="User ID is required")
            return
        session=db.query(SessionModel).filter(SessionModel.id == session_id, SessionModel.user_id == user_id).first()
        if not session:
            await websocket.close(code=1008, reason="User not found")
            return
        
        data=await websocket.receive_text()
        request_data=json.loads(data)
        prompt=request_data.get("prompt")

        if not prompt:
            await websocket.close(code=1008, reason="Prompt is required")
            return
        
        agent_service=GeminiAgentService()
        async for update in agent_service.execute(prompt,session_id):
            await websocket.send_json(update)
        
    except WebSocketDisconnect:
        await websocket.close(code=1000, reason="WebSocket disconnected")
        return

    except Exception as e:
        await websocket.send_json({
            type: "error",
            "message": f"An error occurred: {str(e)}"
        })
        await websocket.close(code=1000, reason="WebSocket disconnected") 
        return