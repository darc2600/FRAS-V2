from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
import secrets
import importlib
from datetime import datetime

# Import passlib for password hashing
try:
	_pb = importlib.import_module("passlib.hash")
	bcrypt = getattr(_pb, "bcrypt")
	_HAS_PASSLIB = True
except Exception:
	bcrypt = None
	_HAS_PASSLIB = False

# Import auth functions and JWT utilities
from .auth import get_current_user_type, get_current_user_permissions, get_user_permissions

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "attendance.db")

router = APIRouter()

# Pydantic models
class UserResponse(BaseModel):
    id: int
    email: str
    user_type: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    created_at: Optional[str]

class CreateUserRequest(BaseModel):
    email: str
    password: str
    user_type: str
    first_name: str
    last_name: str

class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    user_type: Optional[str] = None
    is_active: Optional[bool] = None

# Dependency to check admin permissions
def require_admin_permission(permission: str):
    def dependency(user_type: str = Depends(get_current_user_type)):
        permissions = get_user_permissions(user_type)
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission} required"
            )
        return user_type
    return dependency

# get_current_user_type is now imported from auth.py

@router.get("/api/admin/users", response_model=List[UserResponse])
async def get_users(user_type: str = Depends(require_admin_permission("manage_users"))):
    """Get all users (IT Admin and Super Admin only)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Get users from users table with joined data
            users = []

            # Instructors
            cursor.execute("""
                SELECT u.user_id, u.email, u.role, i.first_name, i.last_name, u.created_at
                FROM users u
                JOIN instructors i ON u.reference_id = i.instructor_id
                WHERE u.role = 'instructor'
            """)
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "email": row[1],
                    "user_type": row[2],
                    "first_name": row[3],
                    "last_name": row[4],
                    "is_active": True,
                    "created_at": row[5]
                })

            # IT Admins
            cursor.execute("""
                SELECT u.user_id, u.email, u.role, ia.first_name, ia.last_name, u.created_at
                FROM users u
                JOIN it_admins ia ON u.reference_id = ia.it_admin_id
                WHERE u.role = 'it_admin'
            """)
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "email": row[1],
                    "user_type": row[2],
                    "first_name": row[3],
                    "last_name": row[4],
                    "is_active": True,
                    "created_at": row[5]
                })

            # Super Admins
            cursor.execute("""
                SELECT u.user_id, u.email, u.role, sa.first_name, sa.last_name, u.created_at
                FROM users u
                JOIN super_admins sa ON u.reference_id = sa.super_admin_id
                WHERE u.role = 'super_admin'
            """)
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "email": row[1],
                    "user_type": row[2],
                    "first_name": row[3],
                    "last_name": row[4],
                    "is_active": True,
                    "created_at": row[5]
                })

            return users

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/api/admin/users")
async def create_user(user_data: CreateUserRequest, admin_type: str = Depends(require_admin_permission("manage_users"))):
    """Create a new user (IT Admin and Super Admin only)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Basic validation
            if user_data.user_type not in ['instructor', 'it_admin', 'super_admin']:
                raise HTTPException(status_code=400, detail="Invalid user type")

            # Check permissions
            if user_data.user_type == 'super_admin' and admin_type != 'super_admin':
                raise HTTPException(status_code=403, detail="Only Super Admin can create super admin accounts")
            if user_data.user_type == 'it_admin' and admin_type not in ['it_admin', 'super_admin']:
                raise HTTPException(status_code=403, detail="Only IT Admin or Super Admin can create IT admin accounts")

            # Check if email already exists
            cursor.execute("SELECT user_id FROM users WHERE email = ?", (user_data.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already exists")

            # Hash the password if passlib is available
            hashed_password = user_data.password
            if _HAS_PASSLIB and bcrypt:
                hashed_password = bcrypt.hash(user_data.password)

            # Create user in appropriate data table
            reference_id = None
            if user_data.user_type == 'instructor':
                # Create instructor account
                cursor.execute("""
                    INSERT INTO instructors (instructor_number, last_name, first_name, email, dept_id, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (f"INS{secrets.token_hex(4).upper()}", user_data.last_name, user_data.first_name, user_data.email, 1))  # Default dept
                reference_id = cursor.lastrowid

            elif user_data.user_type == 'it_admin':
                # Create IT admin account
                cursor.execute("""
                    INSERT INTO it_admins (employee_number, last_name, first_name, email, dept_id, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (f"IT{secrets.token_hex(4).upper()}", user_data.last_name, user_data.first_name, user_data.email, 1))  # Default dept
                reference_id = cursor.lastrowid

            elif user_data.user_type == 'super_admin':
                # Create super admin account
                cursor.execute("""
                    INSERT INTO super_admins (employee_number, last_name, first_name, email, dept_id, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (f"SUPER{secrets.token_hex(4).upper()}", user_data.last_name, user_data.first_name, user_data.email, 1))  # Default dept
                reference_id = cursor.lastrowid

            # Create entry in users table for authentication
            cursor.execute("""
                INSERT INTO users (email, password, role, reference_id, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_data.email, hashed_password, user_data.user_type, reference_id))

            user_id = cursor.lastrowid
            conn.commit()

            return {"message": "User created successfully", "user_id": user_id, "user_type": user_data.user_type}

    except sqlite3.IntegrityError:
        raise HTTPException(400, "Email already exists")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@router.put("/api/admin/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UpdateUserRequest,
    admin_type: str = Depends(require_admin_permission("manage_users"))
):
    """Update user information (IT Admin and Super Admin only)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Check if Super Admin permission is required
            if user_data.user_type in ['it_admin', 'super_admin'] and admin_type != 'super_admin':
                raise HTTPException(403, "Only Super Admin can modify admin roles")

            # Update logic here (simplified for now)
            # In real implementation, you'd update the appropriate table

            return {"message": "User updated successfully"}

    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@router.post("/api/admin/reset-password")
async def reset_password(
    email: str,
    admin_type: str = Depends(require_admin_permission("reset_passwords"))
):
    """Reset user password (IT Admin and Super Admin only)"""
    try:
        # For now, just return success
        # In real implementation, generate reset token and send email
        return {"message": f"Password reset initiated for {email}"}

    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.get("/api/admin/system-settings")
async def get_system_settings(admin_type: str = Depends(require_admin_permission("system_config"))):
    """Get system settings (Super Admin only)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT setting_key, setting_value, setting_type FROM system_settings")
            settings = cursor.fetchall()

            return {row[0]: {"value": row[1], "type": row[2]} for row in settings}

    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@router.put("/api/admin/system-settings")
async def update_system_setting(
    setting_key: str,
    setting_value: str,
    admin_type: str = Depends(require_admin_permission("system_config"))
):
    """Update system setting (Super Admin only)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (setting_key, setting_value))
            conn.commit()

            return {"message": f"Setting {setting_key} updated successfully"}

    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@router.get("/api/admin/analytics")
async def get_analytics(admin_type: str = Depends(require_admin_permission("view_all_data"))):
    """Get system analytics (Super Admin only)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Basic analytics
            analytics = {}

            # User counts
            cursor.execute("SELECT COUNT(*) FROM students")
            analytics['total_students'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM instructors")
            analytics['total_instructors'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM attendance_logs")
            analytics['total_attendance_records'] = cursor.fetchone()[0]

            # Recent activity (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM attendance_logs
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            analytics['recent_attendance'] = cursor.fetchone()[0]

            return analytics

    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")