from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.dirname(__file__))
from api.admin import router as admin_router

app = FastAPI()

# Enable CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:53547", "http://127.0.0.1:4200", "http://127.0.0.1:53547"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin_router)

@app.get("/test")
async def test_endpoint():
    return {"message": "Minimal server is running!"}

@app.post("/api/login")
async def login():
    return {"message": "Login endpoint works!"}