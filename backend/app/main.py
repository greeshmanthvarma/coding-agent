from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import auth_router
from app.routers.user import user_router
from app.routers.agent import agent_router
from app.database import get_redis
from app.redis_schema import create_messages_index
from app.utils.file_cleanup import cleanup_expired_sessions
import asyncio
from contextlib import asynccontextmanager

async def periodic_cleanup():
    """Background task to clean up expired sessions every 15 minutes."""
    while True:
        try:
            await asyncio.sleep(900)  # 15 minutes
            result = cleanup_expired_sessions()
            if "error" not in result:
                print(f"Cleanup: {result.get('message', 'Completed')}")
        except Exception as e:
            print(f"Error in periodic cleanup: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    try:
        redis_client = next(get_redis())
        result = create_messages_index(redis_client)
        print(f"Redis index initialization: {result.get('message', 'Unknown')}")
        redis_client.close()
    except Exception as e:
        print(f"Warning: Failed to initialize Redis index: {e}")
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield  # App runs here
    
    # Shutdown (optional - cleanup if needed)
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins="http://localhost:5174",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(agent_router)

@app.get("/")
async def root():
    return{"message": "Hello World"}