from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import auth_router
from app.routers.user import user_router
from app.routers.agent import agent_router
from app.database import get_redis
from app.redis_schema import create_messages_index

app=FastAPI()
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

@app.on_event("startup")
async def startup_event():
    """Initialize Redis index on application startup."""
    try:
        redis_client = next(get_redis())
        result = create_messages_index(redis_client)
        print(f"Redis index initialization: {result.get('message', 'Unknown')}")
        redis_client.close()
    except Exception as e:
        print(f"Warning: Failed to initialize Redis index: {e}")

@app.get("/")
async def root():
    return{"message": "Hello World"}