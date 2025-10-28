from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import auth_router
from app.routers.user import user_router
from app.routers.agent import agent_router

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

@app.get("/")
async def root():
    return{"message": "Hello World"}