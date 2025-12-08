from fastapi import APIRouter, HTTPException, Depends, status, Body, Request
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
import secrets
import importlib
from datetime import datetime
from services.settings_service import get_settings_service

# Support ticket models
class SupportTicketCreate(BaseModel):
    subject: str
    description: str
    category: str = "other"
    priority: str = "medium"

class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None

class TicketReplyCreate(BaseModel):
    message: str
    is_internal: bool = False

class SupportTicketResponse(BaseModel):
    ticket_id: int
    user_id: int
    subject: str
    description: str
    category: str
    priority: str
    status: str
    assigned_to: Optional[int]
    created_at: str
    updated_at: str
    user_email: Optional[str] = None
    assigned_email: Optional[str] = None

class TicketReplyResponse(BaseModel):
    reply_id: int
    ticket_id: int
    user_id: int
    message: str
    is_internal: bool
    created_at: str
    user_email: Optional[str] = None

# Import passlib for password hashing
try:
	_pb = importlib.import_module("passlib.hash")
	bcrypt = getattr(_pb, "bcrypt")
	_HAS_PASSLIB = True
except Exception:
	bcrypt = None
	_HAS_PASSLIB = False

# Import auth functions and JWT utilities
from .auth import get_current_user_type, get_current_user_id, get_user_permissions

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
    updated_at: Optional[str] = None  # Explicit None default

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
        if user_type == 'super_admin':
            return user_type  # Super admin has all permissions
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

            # Map database role to frontend user_type for display
            role_to_user_type = {
                'instructor': 'instructor',  # Show as Instructor instead of regular
                'it_admin': 'it_admin',
                'super_admin': 'super_admin'
            }

            # Get users from users table with joined data
            users = []

            # Instructors
            cursor.execute("""
                SELECT u.user_id, u.email, u.role, i.first_name, i.last_name, u.created_at, u.updated_at
                FROM users u
                JOIN instructors i ON u.reference_id = i.instructor_id
                WHERE u.role = 'instructor'
            """)
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "email": row[1],
                    "user_type": role_to_user_type.get(row[2], row[2]),
                    "first_name": row[3],
                    "last_name": row[4],
                    "is_active": True,
                    "created_at": row[5],
                    "updated_at": row[6] if row[6] else row[5]  # Simplified fallback
                })

            # IT Admins
            cursor.execute("""
                SELECT u.user_id, u.email, u.role, ia.first_name, ia.last_name, u.created_at, u.updated_at
                FROM users u
                JOIN it_admins ia ON u.reference_id = ia.it_admin_id
                WHERE u.role = 'it_admin'
            """)
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "email": row[1],
                    "user_type": role_to_user_type.get(row[2], row[2]),
                    "first_name": row[3],
                    "last_name": row[4],
                    "is_active": True,
                    "created_at": row[5],
                    "updated_at": row[6] if row[6] and row[6] != "" else row[5]  # Use created_at if updated_at is None or empty
                })

            # Super Admins
            cursor.execute("""
                SELECT u.user_id, u.email, u.role, sa.first_name, sa.last_name, u.created_at, u.updated_at
                FROM users u
                JOIN super_admins sa ON u.reference_id = sa.super_admin_id
                WHERE u.role = 'super_admin'
            """)
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "email": row[1],
                    "user_type": role_to_user_type.get(row[2], row[2]),
                    "first_name": row[3],
                    "last_name": row[4],
                    "is_active": True,
                    "created_at": row[5],
                    "updated_at": row[6] if row[6] and row[6] != "" else row[5]  # Use created_at if updated_at is None or empty
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

            # Map frontend user_type to backend user_type
            user_type_mapping = {
                'instructor': 'instructor',
                'it_admin': 'it_admin',
                'super_admin': 'super_admin'
            }
            backend_user_type = user_type_mapping.get(user_data.user_type, user_data.user_type)

            # Basic validation
            if backend_user_type not in ['instructor', 'it_admin', 'super_admin']:
                raise HTTPException(status_code=400, detail="Invalid user type")

            # Check permissions
            if backend_user_type == 'super_admin' and admin_type != 'super_admin':
                raise HTTPException(status_code=403, detail="Only Super Admin can create super admin accounts")
            if backend_user_type == 'it_admin' and admin_type not in ['it_admin', 'super_admin']:
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
            if backend_user_type == 'instructor':
                # Create instructor account
                cursor.execute("""
                    INSERT INTO instructors (instructor_number, last_name, first_name, email, dept_id, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (f"INS{secrets.token_hex(4).upper()}", user_data.last_name, user_data.first_name, user_data.email, 1))  # Default dept
                reference_id = cursor.lastrowid

            elif backend_user_type == 'it_admin':
                # Create IT admin account
                cursor.execute("""
                    INSERT INTO it_admins (employee_number, last_name, first_name, email, dept_id, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (f"IT{secrets.token_hex(4).upper()}", user_data.last_name, user_data.first_name, user_data.email, 1))  # Default dept
                reference_id = cursor.lastrowid

            elif backend_user_type == 'super_admin':
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
            """, (user_data.email, hashed_password, backend_user_type, reference_id))

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
    request: dict = Body(),
    admin_type: str = Depends(require_admin_permission("reset_passwords"))
):
    """Reset user password (IT Admin and Super Admin only)"""
    print("DEBUG: reset_password called")
    try:
        print(f"DEBUG: Received request: {request}")
        email = request.get('email')
        new_password = request.get('new_password')
        print(f"DEBUG: email={email}, new_password={new_password}")

        if not email:
            raise HTTPException(400, "Email is required")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Check if user exists
            cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            print(f"DEBUG: User found: {user}")
            if not user:
                raise HTTPException(404, "User not found")

            # Hash new password if provided, otherwise generate a temporary one
            if new_password:
                if len(new_password) < 6:
                    raise HTTPException(400, "Password must be at least 6 characters long")
                hashed_password = new_password  # Store plain text for now
                # if _HAS_PASSLIB and bcrypt:
                #     hashed_password = bcrypt.hash(new_password)
            else:
                # Generate temporary password
                temp_password = secrets.token_urlsafe(8)
                hashed_password = temp_password
                # if _HAS_PASSLIB and bcrypt:
                #     hashed_password = bcrypt.hash(temp_password)

            print(f"DEBUG: Updating password for {email} to {hashed_password}")
            # Update password
            cursor.execute("UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
                         (hashed_password, email))
            conn.commit()
            print(f"DEBUG: Password updated successfully")

            return {"message": f"Password reset successfully for {email}"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Exception: {str(e)}")
        raise HTTPException(500, f"Error: {str(e)}")

@router.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_type: str = Depends(require_admin_permission("manage_users"))
):
    """Delete a user (IT Admin and Super Admin only)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Get user info first
            cursor.execute("SELECT role, reference_id FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(404, "User not found")

            role, reference_id = user

            # Prevent deleting super admins unless you're a super admin
            if role == 'super_admin' and admin_type != 'super_admin':
                raise HTTPException(403, "Cannot delete super admin accounts")

            # Delete from role-specific table first
            if role == 'instructor':
                cursor.execute("DELETE FROM instructors WHERE instructor_id = ?", (reference_id,))
            elif role == 'it_admin':
                cursor.execute("DELETE FROM it_admins WHERE it_admin_id = ?", (reference_id,))
            elif role == 'super_admin':
                cursor.execute("DELETE FROM super_admins WHERE super_admin_id = ?", (reference_id,))

            # Delete from users table
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()

            return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@router.post("/api/admin/users/bulk")
async def bulk_user_operation(
    request: dict,
    admin_type: str = Depends(require_admin_permission("manage_users"))
):
    """Perform bulk operations on users (IT Admin and Super Admin only)"""
    try:
        operation = request.get('operation')
        user_ids = request.get('user_ids', [])

        if not operation or not user_ids:
            raise HTTPException(400, "Operation and user_ids are required")

        if operation not in ['activate', 'deactivate', 'delete']:
            raise HTTPException(400, "Invalid operation")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            if operation == 'delete':
                # Check for super admin restrictions
                if admin_type != 'super_admin':
                    placeholders = ','.join('?' * len(user_ids))
                    cursor.execute(f"SELECT role FROM users WHERE user_id IN ({placeholders})", user_ids)
                    roles = [row[0] for row in cursor.fetchall()]
                    if 'super_admin' in roles:
                        raise HTTPException(403, "Cannot delete super admin accounts")

                # Delete from role-specific tables first
                for user_id in user_ids:
                    cursor.execute("SELECT role, reference_id FROM users WHERE user_id = ?", (user_id,))
                    user = cursor.fetchone()
                    if user:
                        role, reference_id = user
                        if role == 'instructor':
                            cursor.execute("DELETE FROM instructors WHERE instructor_id = ?", (reference_id,))
                        elif role == 'it_admin':
                            cursor.execute("DELETE FROM it_admins WHERE it_admin_id = ?", (reference_id,))
                        elif role == 'super_admin':
                            cursor.execute("DELETE FROM super_admins WHERE super_admin_id = ?", (reference_id,))

                # Delete from users table
                placeholders = ','.join('?' * len(user_ids))
                cursor.execute(f"DELETE FROM users WHERE user_id IN ({placeholders})", user_ids)

            elif operation in ['activate', 'deactivate']:
                # For now, we'll assume all users are active
                # In a real implementation, you'd have an is_active column
                pass

            conn.commit()

            return {"message": f"Bulk {operation} completed for {len(user_ids)} users"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@router.get("/api/admin/system-settings")
async def get_system_settings(admin_type: str = Depends(require_admin_permission("system_config"))):
    """Get system settings (Super Admin only)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT setting_key, setting_value, setting_type, category, options,
                       min_value, max_value, step_value
                FROM system_settings
            """)
            settings = cursor.fetchall()

            result = {}
            for row in settings:
                setting_key, setting_value, setting_type, category, options, min_value, max_value, step_value = row

                setting_data = {
                    "value": setting_value,
                    "type": setting_type
                }

                if category:
                    setting_data["category"] = category

                if options:
                    setting_data["options"] = options.split(',')

                if min_value is not None:
                    setting_data["min"] = min_value

                if max_value is not None:
                    setting_data["max"] = max_value

                if step_value is not None:
                    setting_data["step"] = step_value

                result[setting_key] = setting_data

            return result

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

            # Invalidate settings cache to ensure changes take effect immediately
            settings_service = get_settings_service()
            settings_service.invalidate_cache()

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

# User endpoint for creating support tickets
@router.post("/api/support/tickets")
async def create_user_support_ticket(
    ticket: SupportTicketCreate,
    request: Request
):
    """Create a new support ticket (any authenticated user)"""
    print("Endpoint called!")  # Debug print
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(401, "Missing or invalid authorization header")

        token = auth_header.split(' ')[1]

        # Decode token manually
        import jwt
        JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
        JWT_ALGORITHM = "HS256"
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(400, "User ID not found in token")

        print(f"Creating ticket for user_id: {user_id}, type: {type(user_id)}")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            from datetime import datetime
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO support_tickets (user_id, subject, description, category, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, ticket.subject, ticket.description, ticket.category, ticket.priority, now))

            ticket_id = cursor.lastrowid
            conn.commit()

            return {"message": "Support ticket created successfully", "ticket_id": ticket_id}

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    except Exception as e:
        print(f"Error creating ticket: {str(e)}")
        raise HTTPException(500, f"Database error: {str(e)}")

@router.get("/api/admin/support/tickets", response_model=List[SupportTicketResponse])
async def get_support_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    user_type: str = Depends(get_current_user_type),
    current_user_id: int = Depends(get_current_user_id)
):
    """Get support tickets (users see their own, admins see all)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            query = """
                SELECT t.ticket_id, t.user_id, t.subject, t.description, t.category, t.priority, t.status,
                       t.assigned_to, t.created_at, t.updated_at, u.email as user_email,
                       a.email as assigned_email
                FROM support_tickets t
                JOIN users u ON t.user_id = u.user_id
                LEFT JOIN users a ON t.assigned_to = a.user_id
            """

            params = []

            # If not admin, only show user's own tickets
            if user_type not in ['it_admin', 'super_admin']:
                query += " WHERE t.user_id = ?"
                params.append(current_user_id)
            else:
                # Admins can filter
                conditions = []
                if status:
                    conditions.append("t.status = ?")
                    params.append(status)
                if priority:
                    conditions.append("t.priority = ?")
                    params.append(priority)

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY t.created_at DESC"

            cursor.execute(query, params)
            tickets = cursor.fetchall()

            result = []
            for row in tickets:
                result.append({
                    "ticket_id": row[0],
                    "user_id": row[1],
                    "subject": row[2],
                    "description": row[3],
                    "category": row[4],
                    "priority": row[5],
                    "status": row[6],
                    "assigned_to": row[7],
                    "created_at": str(row[8]),
                    "updated_at": str(row[9]),
                    "user_email": row[10],
                    "assigned_email": row[11]
                })

            return result

    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@router.put("/api/admin/support/tickets/{ticket_id}")
async def update_support_ticket(
    ticket_id: int,
    update: SupportTicketUpdate,
    user_type: str = Depends(require_admin_permission("manage_support"))
):
    """Update support ticket (admin only)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Build update query
            update_fields = []
            params = []

            if update.status:
                update_fields.append("status = ?")
                params.append(update.status)
            if update.priority:
                update_fields.append("priority = ?")
                params.append(update.priority)
            if update.assigned_to is not None:
                update_fields.append("assigned_to = ?")
                params.append(update.assigned_to)

            if not update_fields:
                raise HTTPException(400, "No fields to update")

            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(ticket_id)

            query = f"UPDATE support_tickets SET {', '.join(update_fields)} WHERE ticket_id = ?"
            cursor.execute(query, params)
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(404, "Ticket not found")

            return {"message": "Ticket updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@router.post("/api/admin/support/tickets/{ticket_id}/replies")
async def create_ticket_reply(
    ticket_id: int,
    reply: TicketReplyCreate,
    user_type: str = Depends(get_current_user_type),
    user_id: int = Depends(get_current_user_id)
):
    """Add reply to support ticket"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Check if ticket exists and user has access
            cursor.execute("SELECT user_id FROM support_tickets WHERE ticket_id = ?", (ticket_id,))
            ticket = cursor.fetchone()
            if not ticket:
                raise HTTPException(404, "Ticket not found")

            # Only ticket owner or admin can reply
            if ticket[0] != user_id and user_type not in ['it_admin', 'super_admin']:
                raise HTTPException(403, "Access denied")

            cursor.execute("""
                INSERT INTO ticket_replies (ticket_id, user_id, message, is_internal, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (ticket_id, user_id, reply.message, reply.is_internal))

            reply_id = cursor.lastrowid

            # Update ticket updated_at
            cursor.execute("UPDATE support_tickets SET updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?", (ticket_id,))

            conn.commit()

            return {"message": "Reply added successfully", "reply_id": reply_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@router.get("/api/admin/support/tickets/{ticket_id}/replies", response_model=List[TicketReplyResponse])
async def get_ticket_replies(
    ticket_id: int,
    user_type: str = Depends(get_current_user_type),
    current_user_id: int = Depends(get_current_user_id)
):
    """Get replies for a support ticket"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Check if user has access to this ticket
            cursor.execute("SELECT user_id FROM support_tickets WHERE ticket_id = ?", (ticket_id,))
            ticket = cursor.fetchone()
            if not ticket:
                raise HTTPException(404, "Ticket not found")

            # Only ticket owner or admin can view replies
            if ticket[0] != current_user_id and user_type not in ['it_admin', 'super_admin']:
                raise HTTPException(403, "Access denied")

            cursor.execute("""
                SELECT r.reply_id, r.ticket_id, r.user_id, r.message, r.is_internal, r.created_at, u.email
                FROM ticket_replies r
                JOIN users u ON r.user_id = u.user_id
                WHERE r.ticket_id = ?
                ORDER BY r.created_at ASC
            """, (ticket_id,))

            replies = cursor.fetchall()

            return [{
                "reply_id": row[0],
                "ticket_id": row[1],
                "user_id": row[2],
                "message": row[3],
                "is_internal": bool(row[4]),
                "created_at": row[5],
                "user_email": row[6]
            } for row in replies]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")