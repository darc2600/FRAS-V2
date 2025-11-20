from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
from datetime import datetime

# Import auth functions
from .auth import get_user_type_from_email, get_user_permissions

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "attendance.db")

router = APIRouter()

# Pydantic models
class UserResponse(BaseModel):
    id: int
    email: str
    user_type: str
    is_active: bool
    created_at: Optional[str]

class CreateUserRequest(BaseModel):
    email: str
    password: str
    user_type: str = "regular"

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

def get_current_user_type():
    """Placeholder - in real implementation, this would extract from JWT token"""
    # For now, return super_admin for testing
    return "super_admin"

@router.get("/api/admin/users")
async def get_users():
    """Get all users (simplified for testing)"""
    return [{"id": 1, "email": "test@example.com", "user_type": "regular", "is_active": True}]

@router.post("/api/admin/users")
async def create_user(user_data: CreateUserRequest, admin_type: str = Depends(require_admin_permission("manage_users"))):
    """Create a new user (IT Admin and Super Admin only)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Basic validation
            if user_data.user_type not in ['regular', 'it_admin', 'super_admin']:
                raise HTTPException(400, "Invalid user type")

            # Check if Super Admin permission is required for creating admins
            if user_data.user_type in ['it_admin', 'super_admin'] and admin_type != 'super_admin':
                raise HTTPException(403, "Only Super Admin can create admin accounts")

            # For now, add to users table (you may want to add to specific tables)
            cursor.execute("""
                INSERT INTO users (email, password, user_type, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_data.email, user_data.password, user_data.user_type))

            user_id = cursor.lastrowid
            conn.commit()

            return {"message": "User created successfully", "user_id": user_id}

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