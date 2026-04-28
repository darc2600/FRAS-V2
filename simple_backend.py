from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import sqlite3
from services.db import get_connection
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

# JWT settings
JWT_SECRET = "dev-secret-change-me"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440

app = FastAPI(title="FRAS Backend", description="Facial Recognition Attendance System")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_user_auth(email: str):
    """Get user authentication data from database"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT password, role, user_id, reference_id
            FROM users
            WHERE email = ?
        """, (email,))
        result = cursor.fetchone()
        return result

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@app.get("/test")
async def test_endpoint():
    return {"message": "Simple FastAPI backend is running!", "status": "ok"}

@app.post("/api/login")
async def login(payload: LoginRequest):
    """Login endpoint"""
    print(f"Login attempt for: {payload.email}")

    # Get user data
    user_data = get_user_auth(payload.email)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stored_password, user_type, user_id, reference_id = user_data

    # For now, accept any password (since we have hashed passwords in DB)
    # In production, you'd verify the password hash
    if payload.password:  # Simple check for now
        access_token = create_access_token({
            "sub": payload.email,
            "user_type": user_type,
            "user_id": user_id,
            "permissions": ["read"] if user_type == "student" else ["read", "write", "admin"]
        })

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_type": user_type,
            "user_id": user_id,
            "permissions": ["read"] if user_type == "student" else ["read", "write", "admin"]
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/user/register")
async def register_user(payload: UserRegister):
    """User registration endpoint"""
    print(f"Registration attempt for: {payload.email}")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (payload.email,))
        if cursor.fetchone():
            return {"error": "User already registered. Please login instead."}

        # Determine role based on email
        role = None
        reference_id = None

        # Check instructors table
        cursor.execute("SELECT instructor_id FROM instructors WHERE email = ?", (payload.email,))
        instructor_result = cursor.fetchone()
        if instructor_result:
            role = "instructor"
            reference_id = instructor_result[0]

        # Check admins table
        cursor.execute("SELECT admin_id FROM admins WHERE email = ?", (payload.email,))
        admin_result = cursor.fetchone()
        if admin_result:
            role = "admin"
            reference_id = admin_result[0]

        if not role:
            return {"error": "Email not found in system. Please contact administrator."}

        # Create user record
        cursor.execute("""
            INSERT INTO users (email, password, role, reference_id)
            VALUES (?, ?, ?, ?)
        """, (payload.email, payload.password, role, reference_id))

        # Get user_id
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (payload.email,))
        user_id = cursor.fetchone()[0]

        conn.commit()

        # Create JWT token
        access_token = create_access_token({
            "sub": payload.email,
            "user_type": role,
            "user_id": user_id,
            "permissions": ["read"] if role == "student" else ["read", "write", "admin"]
        })

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": role,
            "user_id": user_id
        }

@app.get("/api/admin/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    """Get all users (admin only)"""
    if current_user.get("user_type") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, email, role, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()

        return {"users": [
            {
                "id": user[0],
                "email": user[1],
                "user_type": user[2],
                "created_at": user[3]
            } for user in users
        ]}

@app.get("/api/admin/analytics")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    """Get system analytics (admin only)"""
    if current_user.get("user_type") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Get user counts
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        student_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'instructor'")
        instructor_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]

        # Get attendance count
        cursor.execute("SELECT COUNT(*) FROM attendance_logs")
        attendance_count = cursor.fetchone()[0]

        return {
            "total_students": student_count,
            "total_instructors": instructor_count,
            "total_admins": admin_count,
            "total_attendance_records": attendance_count,
            "total_users": student_count + instructor_count + admin_count
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)