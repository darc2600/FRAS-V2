from fastapi import APIRouter, HTTPException, Depends, status, Body, Request, Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import sqlite3
from services.db import get_connection
import os
import secrets
import importlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import logging
from services.settings_service import get_settings_service
from services.attendance_service import mark_automatic_absents
from services.face_embeddings import ensure_embeddings_table

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

_env_db = os.environ.get('SQLITE_DB_PATH')
if _env_db:
    DB_PATH = _env_db
else:
    # prefer mounted data/attendance.db when available
    candidate = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'attendance.db')
    candidate = os.path.normpath(candidate)
    if os.path.exists(candidate):
        DB_PATH = candidate
    else:
        DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "attendance.db")

router = APIRouter()

LOG = logging.getLogger(__name__)
MANILA_TZ = ZoneInfo("Asia/Manila")

ROLE_TABLE_META = {
    'instructor': {
        'table': 'instructors',
        'id_col': 'instructor_id',
        'number_col': 'instructor_number',
        'number_prefix': 'INS'
    },
    'it_admin': {
        'table': 'it_admins',
        'id_col': 'it_admin_id',
        'number_col': 'employee_number',
        'number_prefix': 'IT'
    },
    'super_admin': {
        'table': 'super_admins',
        'id_col': 'super_admin_id',
        'number_col': 'employee_number',
        'number_prefix': 'SUPER'
    }
}


def _is_postgres_backend() -> bool:
    db_url = (os.environ.get('DATABASE_URL') or '').strip().lower()
    return bool(db_url) and not db_url.startswith('sqlite')


def _ensure_users_is_active_column(cursor):
    if _is_postgres_backend():
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = ? AND column_name = ?
            """,
            ('users', 'is_active')
        )
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
        cursor.execute("UPDATE users SET is_active = TRUE WHERE is_active IS NULL")
    else:
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in (cursor.fetchall() or [])]
        if 'is_active' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
        cursor.execute("UPDATE users SET is_active = 1 WHERE is_active IS NULL")


def _insert_role_profile(cursor, role: str, profile: dict) -> int:
    meta = ROLE_TABLE_META[role]
    number_value = profile.get(meta['number_col']) or f"{meta['number_prefix']}{secrets.token_hex(4).upper()}"
    first_name = profile.get('first_name') or ''
    last_name = profile.get('last_name') or ''
    email = profile.get('email') or ''
    dept_id = profile.get('dept_id') or 1

    is_postgres = _is_postgres_backend()
    if is_postgres:
        cursor.execute(
            f"""
            INSERT INTO {meta['table']} ({meta['number_col']}, last_name, first_name, email, dept_id, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            RETURNING {meta['id_col']}
            """,
            (number_value, last_name, first_name, email, dept_id)
        )
        row = cursor.fetchone()
        return int(row[0])

    cursor.execute(
        f"""
        INSERT INTO {meta['table']} ({meta['number_col']}, last_name, first_name, email, dept_id, created_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (number_value, last_name, first_name, email, dept_id)
    )
    return int(getattr(cursor, 'lastrowid', 0) or 0)


def _to_manila_iso(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return text
        normalized = text
        if normalized.endswith('Z'):
            normalized = normalized[:-1] + '+00:00'
        if ' ' in normalized and 'T' not in normalized:
            normalized = normalized.replace(' ', 'T')
        try:
            parsed = datetime.fromisoformat(normalized)
        except Exception:
            return str(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(MANILA_TZ).isoformat()

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
    can_change_role: Optional[bool] = True
    role_change_block_reason: Optional[str] = None

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


class FaceEmbeddingCoverageResponse(BaseModel):
    total_students: int
    students_with_face_path: int
    students_with_embeddings: int
    students_with_any_face_data: int
    students_missing_all_face_data: int
    embedding_coverage_percent: float

# Dependency to check admin permissions
def require_admin_permission(permission: str):
    def dependency(user_type: str = Depends(get_current_user_type)):
        if user_type == 'super_admin':
            return user_type  # Super admin has all permissions
        permissions = set(get_user_permissions(user_type))

        permission_aliases = {
            "view_all_data": {"view_all_data", "view_analytics"},
            "view_analytics": {"view_analytics", "view_all_data"},
            "reset_passwords": {"reset_passwords", "manage_users"},
            "manage_users": {"manage_users", "reset_passwords"},
        }
        allowed = permission_aliases.get(permission, {permission})

        if permissions.isdisjoint(allowed):
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
        with get_connection() as conn:
            cursor = conn.cursor()
            _ensure_users_is_active_column(cursor)

            # Map database role to frontend user_type for display
            role_to_user_type = {
                'instructor': 'instructor',  # Show as Instructor instead of regular
                'it_admin': 'it_admin',
                'super_admin': 'super_admin'
            }

            # Get users from users table with joined data
            users = []

            def _fmt_dt(v):
                try:
                    if isinstance(v, datetime):
                        return v.isoformat()
                    return str(v) if v is not None else None
                except Exception:
                    return None

            # Instructors
            cursor.execute("""
                SELECT u.user_id, u.email, u.role, i.first_name, i.last_name, u.created_at, u.updated_at, COALESCE(u.is_active, TRUE), u.reference_id
                FROM users u
                JOIN instructors i ON u.reference_id = i.instructor_id
                WHERE u.role = 'instructor'
            """)
            for row in cursor.fetchall():
                instructor_id = row[8]
                cursor.execute("SELECT COUNT(*) FROM classes WHERE instructor_id = ?", (instructor_id,))
                class_count_row = cursor.fetchone()
                class_count = int(class_count_row[0]) if class_count_row else 0
                can_change_role = class_count == 0
                users.append({
                    "id": row[0],
                    "email": row[1],
                    "user_type": role_to_user_type.get(row[2], row[2]),
                    "first_name": row[3],
                    "last_name": row[4],
                    "is_active": bool(row[7]),
                    "created_at": _fmt_dt(row[5]),
                    "updated_at": _fmt_dt(row[6] if row[6] else row[5]),  # Simplified fallback
                    "can_change_role": can_change_role,
                    "role_change_block_reason": None if can_change_role else "Assigned classes"
                })

            # IT Admins
            cursor.execute("""
                SELECT u.user_id, u.email, u.role, ia.first_name, ia.last_name, u.created_at, u.updated_at, COALESCE(u.is_active, TRUE)
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
                    "is_active": bool(row[7]),
                    "created_at": _fmt_dt(row[5]),
                    "updated_at": _fmt_dt(row[6] if row[6] and row[6] != "" else row[5]),  # Use created_at if updated_at is None or empty
                    "can_change_role": True,
                    "role_change_block_reason": None
                })

            # Super Admins
            cursor.execute("""
                SELECT u.user_id, u.email, u.role, sa.first_name, sa.last_name, u.created_at, u.updated_at, COALESCE(u.is_active, TRUE)
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
                    "is_active": bool(row[7]),
                    "created_at": _fmt_dt(row[5]),
                    "updated_at": _fmt_dt(row[6] if row[6] and row[6] != "" else row[5]),  # Use created_at if updated_at is None or empty
                    "can_change_role": True,
                    "role_change_block_reason": None
                })

            # Defensive normalization: ensure all datetime/date values are strings
            for u in users:
                for k in ('created_at', 'updated_at'):
                    v = u.get(k)
                    try:
                        if isinstance(v, datetime):
                            u[k] = v.isoformat()
                        elif v is not None:
                            u[k] = str(v)
                        else:
                            u[k] = None
                    except Exception:
                        u[k] = None

            return users

    except Exception as e:
        LOG.exception('Error in get_face_embedding_coverage')
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/api/admin/face-embedding-coverage", response_model=FaceEmbeddingCoverageResponse)
async def get_face_embedding_coverage(admin_type: str = Depends(require_admin_permission("view_all_data"))):
    """Get migration/coverage stats for DB-stored face embeddings."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            ensure_embeddings_table(cursor)

            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM students WHERE face_data_path IS NOT NULL AND TRIM(face_data_path) != ''")
            students_with_face_path = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT student_id) FROM student_face_embeddings")
            students_with_embeddings = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*)
                FROM students s
                WHERE (s.face_data_path IS NOT NULL AND TRIM(s.face_data_path) != '')
                   OR EXISTS (
                        SELECT 1
                        FROM student_face_embeddings sfe
                        WHERE sfe.student_id = s.student_id
                   )
            ''')
            students_with_any_face_data = cursor.fetchone()[0]

            students_missing_all_face_data = max(total_students - students_with_any_face_data, 0)

            embedding_coverage_percent = 0.0
            if total_students > 0:
                embedding_coverage_percent = round((students_with_embeddings / total_students) * 100.0, 2)

            return FaceEmbeddingCoverageResponse(
                total_students=total_students,
                students_with_face_path=students_with_face_path,
                students_with_embeddings=students_with_embeddings,
                students_with_any_face_data=students_with_any_face_data,
                students_missing_all_face_data=students_missing_all_face_data,
                embedding_coverage_percent=embedding_coverage_percent,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/api/debug/face-embedding-coverage-public", response_model=FaceEmbeddingCoverageResponse)
async def get_face_embedding_coverage_public():
    """Unauthenticated debug endpoint (temporary) returning embedding coverage.
    Use this only for local verification. Remove before production rollout.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            ensure_embeddings_table(cursor)

            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM students WHERE face_data_path IS NOT NULL AND TRIM(face_data_path) != ''")
            students_with_face_path = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT student_id) FROM student_face_embeddings")
            students_with_embeddings = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*)
                FROM students s
                WHERE (s.face_data_path IS NOT NULL AND TRIM(s.face_data_path) != '')
                   OR EXISTS (
                        SELECT 1
                        FROM student_face_embeddings sfe
                        WHERE sfe.student_id = s.student_id
                   )
            ''')
            students_with_any_face_data = cursor.fetchone()[0]

            students_missing_all_face_data = max(total_students - students_with_any_face_data, 0)

            embedding_coverage_percent = 0.0
            if total_students > 0:
                embedding_coverage_percent = round((students_with_embeddings / total_students) * 100.0, 2)

            return FaceEmbeddingCoverageResponse(
                total_students=total_students,
                students_with_face_path=students_with_face_path,
                students_with_embeddings=students_with_embeddings,
                students_with_any_face_data=students_with_any_face_data,
                students_missing_all_face_data=students_missing_all_face_data,
                embedding_coverage_percent=embedding_coverage_percent,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/api/admin/users")
async def create_user(user_data: CreateUserRequest, admin_type: str = Depends(require_admin_permission("manage_users"))):
    """Create a new user (IT Admin and Super Admin only)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            _ensure_users_is_active_column(cursor)

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
                try:
                    hashed_password = bcrypt.hash(user_data.password)
                except Exception:
                    LOG.exception("bcrypt hashing failed during user creation; storing plaintext fallback")
                    hashed_password = user_data.password

            # Create user in appropriate data table
            reference_id = _insert_role_profile(cursor, backend_user_type, {
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "email": user_data.email,
                "dept_id": 1
            })

            # Create entry in users table for authentication
            if _is_postgres_backend():
                cursor.execute("""
                    INSERT INTO users (email, password, role, reference_id, is_active, created_at)
                    VALUES (?, ?, ?, ?, TRUE, CURRENT_TIMESTAMP)
                    RETURNING user_id
                """, (user_data.email, hashed_password, backend_user_type, reference_id))
                row = cursor.fetchone()
                user_id = int(row[0])
            else:
                cursor.execute("""
                    INSERT INTO users (email, password, role, reference_id, is_active, created_at)
                    VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                """, (user_data.email, hashed_password, backend_user_type, reference_id))
                user_id = int(getattr(cursor, 'lastrowid', 0) or 0)
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
        with get_connection() as conn:
            cursor = conn.cursor()
            _ensure_users_is_active_column(cursor)

            user_type_mapping = {
                'instructor': 'instructor',
                'it_admin': 'it_admin',
                'super_admin': 'super_admin'
            }

            cursor.execute(
                "SELECT email, role, reference_id FROM users WHERE user_id = ?",
                (user_id,)
            )
            existing_user = cursor.fetchone()
            if not existing_user:
                raise HTTPException(404, "User not found")

            current_email, current_role, current_reference_id = existing_user
            target_role = user_type_mapping.get(user_data.user_type, current_role) if user_data.user_type else current_role

            if target_role not in ROLE_TABLE_META:
                raise HTTPException(400, "Invalid user type")

            if admin_type != 'super_admin' and (current_role != 'instructor' or target_role != 'instructor'):
                raise HTTPException(403, "Only Super Admin can modify admin accounts or roles")

            role_changed = target_role != current_role
            new_email = user_data.email or current_email

            # Read current profile row
            current_meta = ROLE_TABLE_META[current_role]
            cursor.execute(
                f"""
                SELECT {current_meta['number_col']}, last_name, first_name, email, dept_id
                FROM {current_meta['table']}
                WHERE {current_meta['id_col']} = ?
                """,
                (current_reference_id,)
            )
            profile_row = cursor.fetchone()
            if profile_row:
                profile = {
                    current_meta['number_col']: profile_row[0],
                    'last_name': profile_row[1],
                    'first_name': profile_row[2],
                    'email': profile_row[3] or current_email,
                    'dept_id': profile_row[4] or 1
                }
            else:
                profile = {
                    'last_name': '',
                    'first_name': '',
                    'email': current_email,
                    'dept_id': 1
                }

            profile['email'] = new_email

            if role_changed:
                if current_role == 'instructor':
                    cursor.execute(
                        "SELECT COUNT(*) FROM classes WHERE instructor_id = ?",
                        (current_reference_id,)
                    )
                    class_count_row = cursor.fetchone()
                    class_count = int(class_count_row[0]) if class_count_row else 0
                    if class_count > 0:
                        raise HTTPException(
                            400,
                            "Cannot change role: this instructor is assigned to classes. Reassign or remove class assignments first."
                        )

                new_reference_id = _insert_role_profile(cursor, target_role, profile)
                cursor.execute(
                    """
                    UPDATE users
                    SET role = ?, reference_id = ?, email = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (target_role, new_reference_id, new_email, user_id)
                )
                cursor.execute(
                    f"DELETE FROM {current_meta['table']} WHERE {current_meta['id_col']} = ?",
                    (current_reference_id,)
                )
            else:
                if new_email != current_email:
                    cursor.execute(
                        "UPDATE users SET email = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                        (new_email, user_id)
                    )
                    cursor.execute(
                        f"UPDATE {current_meta['table']} SET email = ?, updated_at = CURRENT_TIMESTAMP WHERE {current_meta['id_col']} = ?",
                        (new_email, current_reference_id)
                    )

            if user_data.is_active is not None:
                active_value = True if bool(user_data.is_active) else False
                cursor.execute(
                    "UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (active_value, user_id)
                )
            conn.commit()
            return {
                "message": "User updated successfully",
                "user_id": user_id,
                "role": target_role,
                "email": new_email,
                "is_active": user_data.is_active
            }

    except HTTPException:
        raise
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

        with get_connection() as conn:
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
                hashed_password = new_password
                if _HAS_PASSLIB and bcrypt:
                    try:
                        hashed_password = bcrypt.hash(new_password)
                    except Exception:
                        LOG.exception("bcrypt hashing failed during password reset; storing plaintext fallback")
                        hashed_password = new_password
            else:
                # Generate temporary password
                temp_password = secrets.token_urlsafe(8)
                hashed_password = temp_password
                if _HAS_PASSLIB and bcrypt:
                    try:
                        hashed_password = bcrypt.hash(temp_password)
                    except Exception:
                        LOG.exception("bcrypt hashing failed during temp password reset; storing plaintext fallback")
                        hashed_password = temp_password

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
        with get_connection() as conn:
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

        with get_connection() as conn:
            cursor = conn.cursor()
            _ensure_users_is_active_column(cursor)

            if admin_type != 'super_admin':
                placeholders = ','.join('?' * len(user_ids))
                cursor.execute(f"SELECT DISTINCT role FROM users WHERE user_id IN ({placeholders})", user_ids)
                roles = {row[0] for row in cursor.fetchall()}
                if any(role in {'it_admin', 'super_admin'} for role in roles):
                    raise HTTPException(403, "Only Super Admin can modify admin accounts")

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
                is_active_value = True if operation == 'activate' else False
                placeholders = ','.join('?' * len(user_ids))
                cursor.execute(
                    f"UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id IN ({placeholders})",
                    [is_active_value, *user_ids]
                )

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
        with get_connection() as conn:
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
                    "type": setting_type,
                    "display_name": setting_key.replace('_', ' ').title()
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
        with get_connection() as conn:
            cursor = conn.cursor()
            if _is_postgres_backend():
                cursor.execute("""
                    INSERT INTO system_settings (setting_key, setting_value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT (setting_key)
                    DO UPDATE SET setting_value = EXCLUDED.setting_value,
                                  updated_at = CURRENT_TIMESTAMP
                """, (setting_key, setting_value))
            else:
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

@router.put("/api/admin/system-settings/bulk")
async def update_system_settings_bulk(
    updates: List[Dict[str, str]] = Body(...),
    admin_type: str = Depends(require_admin_permission("system_config"))
):
    """Update multiple system settings (Super Admin only)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            for update in updates:
                if _is_postgres_backend():
                    cursor.execute("""
                        INSERT INTO system_settings (setting_key, setting_value, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT (setting_key)
                        DO UPDATE SET setting_value = EXCLUDED.setting_value,
                                      updated_at = CURRENT_TIMESTAMP
                    """, (update['key'], update['value']))
                else:
                    cursor.execute("""
                        INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    """, (update['key'], update['value']))
            conn.commit()

            # Invalidate settings cache to ensure changes take effect immediately
            settings_service = get_settings_service()
            settings_service.invalidate_cache()

            return {"message": f"Successfully updated {len(updates)} settings"}

    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@router.get("/api/admin/analytics")
async def get_analytics(admin_type: str = Depends(require_admin_permission("view_all_data"))):
    """Get dashboard analytics for the admin analytics page.

    The response intentionally includes both headline totals and simple
    Jan-Dec chart datasets so the frontend can present panel-friendly
    monthly insights without adding a heavy charting dependency.
    """
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def empty_month_series():
        return [{"month": label, "count": 0} for label in month_labels]

    def rows_to_month_series(rows):
        series = empty_month_series()
        for row in rows:
            try:
                month_number = int(row[0])
                count = int(row[1] or 0)
                if 1 <= month_number <= 12:
                    series[month_number - 1]["count"] = count
            except Exception:
                continue
        return series

    def safe_count(cursor, query, params=()):
        cursor.execute(query, params)
        row = cursor.fetchone()
        return int(row[0] or 0) if row else 0

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            analytics = {}

            db_url = os.environ.get("DATABASE_URL", "")
            is_postgres = bool(db_url and not db_url.startswith("sqlite"))

            # Headline totals
            analytics["total_students"] = safe_count(cursor, "SELECT COUNT(*) FROM students")
            analytics["total_instructors"] = safe_count(cursor, "SELECT COUNT(*) FROM instructors")
            analytics["total_attendance_records"] = safe_count(cursor, "SELECT COUNT(*) FROM attendance_logs")

            # Recent activity
            if is_postgres:
                analytics["recent_attendance"] = safe_count(
                    cursor,
                    "SELECT COUNT(*) FROM attendance_logs WHERE timestamp >= NOW() - INTERVAL '7 days'"
                )
            else:
                analytics["recent_attendance"] = safe_count(
                    cursor,
                    "SELECT COUNT(*) FROM attendance_logs WHERE timestamp >= datetime('now', '-7 days')"
                )

            # Pick the most useful chart year automatically.
            # Demo databases often contain fixed historical data, so using the latest data year
            # is more useful than blindly using the current calendar year.
            if is_postgres:
                cursor.execute("""
                    SELECT MAX(year_value) FROM (
                        SELECT EXTRACT(YEAR FROM created_at)::INT AS year_value FROM students WHERE created_at IS NOT NULL
                        UNION ALL
                        SELECT EXTRACT(YEAR FROM created_at)::INT AS year_value FROM instructors WHERE created_at IS NOT NULL
                        UNION ALL
                        SELECT EXTRACT(YEAR FROM timestamp)::INT AS year_value FROM attendance_logs WHERE timestamp IS NOT NULL
                    ) yearly_data
                """)
            else:
                cursor.execute("""
                    SELECT MAX(year_value) FROM (
                        SELECT CAST(strftime('%Y', created_at) AS INTEGER) AS year_value FROM students WHERE created_at IS NOT NULL
                        UNION ALL
                        SELECT CAST(strftime('%Y', created_at) AS INTEGER) AS year_value FROM instructors WHERE created_at IS NOT NULL
                        UNION ALL
                        SELECT CAST(strftime('%Y', timestamp) AS INTEGER) AS year_value FROM attendance_logs WHERE timestamp IS NOT NULL
                    )
                """)
            selected_year_row = cursor.fetchone()
            selected_year = selected_year_row[0] if selected_year_row and selected_year_row[0] else datetime.now().year
            analytics["chart_year"] = int(selected_year)

            # Monthly student registrations
            if is_postgres:
                cursor.execute("""
                    SELECT EXTRACT(MONTH FROM created_at)::INT AS month_number, COUNT(*) AS total
                    FROM students
                    WHERE EXTRACT(YEAR FROM created_at)::INT = %s
                    GROUP BY month_number
                    ORDER BY month_number
                """, (selected_year,))
            else:
                cursor.execute("""
                    SELECT CAST(strftime('%m', created_at) AS INTEGER) AS month_number, COUNT(*) AS total
                    FROM students
                    WHERE CAST(strftime('%Y', created_at) AS INTEGER) = ?
                    GROUP BY month_number
                    ORDER BY month_number
                """, (selected_year,))
            analytics["monthly_student_registrations"] = rows_to_month_series(cursor.fetchall())

            # Monthly instructor registrations
            if is_postgres:
                cursor.execute("""
                    SELECT EXTRACT(MONTH FROM created_at)::INT AS month_number, COUNT(*) AS total
                    FROM instructors
                    WHERE EXTRACT(YEAR FROM created_at)::INT = %s
                    GROUP BY month_number
                    ORDER BY month_number
                """, (selected_year,))
            else:
                cursor.execute("""
                    SELECT CAST(strftime('%m', created_at) AS INTEGER) AS month_number, COUNT(*) AS total
                    FROM instructors
                    WHERE CAST(strftime('%Y', created_at) AS INTEGER) = ?
                    GROUP BY month_number
                    ORDER BY month_number
                """, (selected_year,))
            analytics["monthly_instructor_registrations"] = rows_to_month_series(cursor.fetchall())

            # Monthly attendance records
            if is_postgres:
                cursor.execute("""
                    SELECT EXTRACT(MONTH FROM timestamp)::INT AS month_number, COUNT(*) AS total
                    FROM attendance_logs
                    WHERE EXTRACT(YEAR FROM timestamp)::INT = %s
                    GROUP BY month_number
                    ORDER BY month_number
                """, (selected_year,))
            else:
                cursor.execute("""
                    SELECT CAST(strftime('%m', timestamp) AS INTEGER) AS month_number, COUNT(*) AS total
                    FROM attendance_logs
                    WHERE CAST(strftime('%Y', timestamp) AS INTEGER) = ?
                    GROUP BY month_number
                    ORDER BY month_number
                """, (selected_year,))
            analytics["monthly_attendance_records"] = rows_to_month_series(cursor.fetchall())

            # Attendance status distribution
            cursor.execute("""
                SELECT COALESCE(ast.status_name, ast.status_code, 'Unknown') AS status_label, COUNT(*) AS total
                FROM attendance_logs al
                LEFT JOIN attendance_status_types ast ON ast.status_id = al.status_id
                GROUP BY status_label
                ORDER BY total DESC, status_label ASC
            """)
            analytics["attendance_status_distribution"] = [
                {"status": str(row[0]), "count": int(row[1] or 0)}
                for row in cursor.fetchall()
            ]

            # Top classes by attendance volume
            cursor.execute("""
                SELECT
                    COALESCE(c.course_code, 'Course') || ' - ' || COALESCE(cls.section, 'Section') AS class_label,
                    COUNT(al.log_id) AS total
                FROM attendance_logs al
                LEFT JOIN classes cls ON cls.class_id = al.class_id
                LEFT JOIN courses c ON c.course_id = cls.course_id
                GROUP BY class_label
                ORDER BY total DESC
                LIMIT 5
            """)
            analytics["top_classes_by_attendance"] = [
                {"class_label": str(row[0]), "count": int(row[1] or 0)}
                for row in cursor.fetchall()
            ]

            return analytics

    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@router.post("/api/admin/mark-automatic-absents")
async def trigger_automatic_absent_marking(admin_type: str = Depends(require_admin_permission("manage_users"))):
    """Manually trigger automatic absent marking for ongoing classes (Super Admin only)"""
    try:
        result = await mark_automatic_absents()
        return {"message": "Automatic absent marking completed", "result": "Success"}

    except Exception as e:
        raise HTTPException(500, f"Error during automatic absent marking: {str(e)}")

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

        with get_connection() as conn:
            cursor = conn.cursor()

            now = datetime.now(timezone.utc).isoformat()

            db_url = (os.environ.get('DATABASE_URL') or '').strip().lower()
            is_postgres = bool(db_url) and not db_url.startswith('sqlite')

            if is_postgres:
                cursor.execute("""
                    INSERT INTO support_tickets (user_id, subject, description, category, priority, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    RETURNING ticket_id
                """, (user_id, ticket.subject, ticket.description, ticket.category, ticket.priority, now))
                row = cursor.fetchone()
                ticket_id = row[0] if row else None
            else:
                cursor.execute("""
                    INSERT INTO support_tickets (user_id, subject, description, category, priority, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, ticket.subject, ticket.description, ticket.category, ticket.priority, now))
                ticket_id = getattr(cursor, 'lastrowid', None)
                if not ticket_id:
                    cursor.execute("SELECT ticket_id FROM support_tickets WHERE user_id = ? ORDER BY ticket_id DESC LIMIT 1", (user_id,))
                    row = cursor.fetchone()
                    ticket_id = row[0] if row else None

            conn.commit()

            if ticket_id is None:
                raise HTTPException(500, "Failed to retrieve created ticket ID")

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
        with get_connection() as conn:
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
                    "created_at": _to_manila_iso(row[8]),
                    "updated_at": _to_manila_iso(row[9]),
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
        with get_connection() as conn:
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

            update_fields.append("updated_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
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
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if ticket exists and user has access
            cursor.execute("SELECT user_id FROM support_tickets WHERE ticket_id = ?", (ticket_id,))
            ticket = cursor.fetchone()
            if not ticket:
                raise HTTPException(404, "Ticket not found")

            # Only ticket owner or admin can reply
            if ticket[0] != user_id and user_type not in ['it_admin', 'super_admin']:
                raise HTTPException(403, "Access denied")

            db_url = (os.environ.get('DATABASE_URL') or '').strip().lower()
            is_postgres = bool(db_url) and not db_url.startswith('sqlite')

            created_at = datetime.now(timezone.utc).isoformat()

            if is_postgres:
                cursor.execute("""
                    INSERT INTO ticket_replies (ticket_id, user_id, message, is_internal, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    RETURNING reply_id
                """, (ticket_id, user_id, reply.message, reply.is_internal, created_at))
                reply_row = cursor.fetchone()
                reply_id = reply_row[0] if reply_row else None
            else:
                cursor.execute("""
                    INSERT INTO ticket_replies (ticket_id, user_id, message, is_internal, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (ticket_id, user_id, reply.message, reply.is_internal, created_at))
                reply_id = getattr(cursor, 'lastrowid', None)
                if not reply_id:
                    cursor.execute("SELECT reply_id FROM ticket_replies WHERE ticket_id = ? ORDER BY reply_id DESC LIMIT 1", (ticket_id,))
                    rr = cursor.fetchone()
                    reply_id = rr[0] if rr else None

            if reply_id is None:
                raise HTTPException(500, "Failed to retrieve created reply ID")

            # Update ticket updated_at
            cursor.execute(
                "UPDATE support_tickets SET updated_at = ? WHERE ticket_id = ?",
                (datetime.now(timezone.utc).isoformat(), ticket_id)
            )

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
        with get_connection() as conn:
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
                "created_at": _to_manila_iso(row[5]),
                "user_email": row[6]
            } for row in replies]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

# Attendance Export Report Endpoints
class AttendanceExportRequest(BaseModel):
    date_from: Optional[str] = Field(None, alias='dateFrom')
    date_to: Optional[str] = Field(None, alias='dateTo')
    class_id: Optional[int] = Field(None, alias='classId')
    student_ids: Optional[List[int]] = Field(None, alias='studentIds')
    status_filter: Optional[List[str]] = Field(None, alias='statusFilter')  # ['Present', 'Absent', 'Late', 'Excused']
    course_code: Optional[str] = Field(None, alias='courseCode')
    section: Optional[str] = None
    instructor_id: Optional[int] = Field(None, alias='instructorId')
    professor_name: Optional[str] = Field(None, alias='professorName')
    export_format: str = Field("json", alias='exportFormat')  # json, csv, excel, pdf

    class Config:
        # Allow sending either snake_case or camelCase from the frontend
        allow_population_by_field_name = True
        # Accept unknown fields gracefully (do not error on extra frontend props)
        extra = 'ignore'

class AttendanceRecord(BaseModel):
    student_id: str
    student_name: str
    date: str
    time_in: Optional[str]
    status: str

class ClassSummary(BaseModel):
    total_students: int
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    attendance_percentage: float
    needs_attention: List[str]  # Students with >3 absences

class AttendanceReport(BaseModel):
    report_title: str
    generated_at: str
    exported_by: str
    date_range: str
    records: List[AttendanceRecord]
    class_summary: ClassSummary

class ProfessorReport(BaseModel):
    professor_name: str
    classes: List[AttendanceReport]
    consolidated_summary: ClassSummary

@router.post("/api/admin/attendance/export")
async def export_attendance_report(
    request: AttendanceExportRequest,
    admin_type: str = Depends(require_admin_permission("view_all_data"))
):
    """Generate attendance export report (Super Admin only)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            db_url = os.environ.get('DATABASE_URL', '')
            is_postgres = bool(db_url and not db_url.lower().startswith('sqlite'))
            if is_postgres:
                date_expr = "(a.timestamp AT TIME ZONE 'Asia/Manila')::date"
                time_expr = "to_char(a.timestamp AT TIME ZONE 'Asia/Manila', 'HH12:MI:SS AM')"
            else:
                date_expr = "strftime('%Y-%m-%d', a.timestamp)"
                time_expr = "strftime('%H:%M:%S', a.timestamp)"

            # Build the main query
            base_query = f"""
                SELECT
                    s.student_number as student_id,
                    (s.last_name || ', ' || s.first_name) as student_name,
                    {date_expr} as date,
                    {time_expr} as time_in,
                    ast.status_name as status,
                    c.course_id,
                    c.section,
                    i.instructor_id,
                    (i.last_name || ', ' || i.first_name) as instructor_name,
                    co.course_code,
                    co.course_name
                FROM attendance_logs a
                JOIN students s ON a.student_id = s.student_id
                JOIN attendance_status_types ast ON a.status_id = ast.status_id
                JOIN classes c ON a.class_id = c.class_id
                JOIN instructors i ON c.instructor_id = i.instructor_id
                JOIN courses co ON c.course_id = co.course_id
                WHERE 1=1
            """

            params = []

            # Apply filters
            if request.date_from:
                base_query += f" AND {date_expr} >= ?"
                params.append(request.date_from)

            if request.date_to:
                base_query += f" AND {date_expr} <= ?"
                params.append(request.date_to)

            if request.student_ids:
                placeholders = ','.join('?' * len(request.student_ids))
                base_query += f" AND s.student_id IN ({placeholders})"
                params.extend(request.student_ids)

            if request.class_id:
                base_query += " AND c.class_id = ?"
                params.append(request.class_id)

            if request.status_filter:
                placeholders = ','.join('?' * len(request.status_filter))
                base_query += f" AND ast.status_name IN ({placeholders})"
                params.extend(request.status_filter)

            if request.course_code:
                base_query += " AND co.course_code = ?"
                params.append(request.course_code)

            if request.section:
                base_query += " AND c.section = ?"
                params.append(request.section)

            if request.instructor_id:
                base_query += " AND i.instructor_id = ?"
                params.append(request.instructor_id)

            base_query += " ORDER BY a.timestamp DESC"

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            # Process results
            records = []
            for row in rows:
                records.append({
                    "student_id": row[0] or "N/A",
                    "student_name": row[1] or "N/A",
                    "date": str(row[2]) if row[2] is not None else "N/A",
                    "time_in": str(row[3]) if row[3] is not None else "N/A",
                    "status": row[4] or "N/A"
                })

            # Generate class summary
            if records:
                # Count by status
                status_counts = {}
                student_absences = {}

                for record in records:
                    status = record["status"]
                    student_id = record["student_id"]

                    if status not in status_counts:
                        status_counts[status] = 0
                    status_counts[status] += 1

                    # Track absences per student
                    if status == "Absent":
                        if student_id not in student_absences:
                            student_absences[student_id] = 0
                        student_absences[student_id] += 1

                # Get unique students count
                unique_students = len(set(r["student_id"] for r in records))

                present_count = status_counts.get("Present", 0)
                absent_count = status_counts.get("Absent", 0)
                late_count = status_counts.get("Late", 0)
                excused_count = status_counts.get("Excused", 0)

                total_records = len(records)
                attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0

                # Flag students with >3 absences
                needs_attention = [student_id for student_id, absences in student_absences.items() if absences > 3]

                class_summary = {
                    "total_students": unique_students,
                    "present_count": present_count,
                    "absent_count": absent_count,
                    "late_count": late_count,
                    "excused_count": excused_count,
                    "attendance_percentage": round(attendance_percentage, 2),
                    "needs_attention": needs_attention
                }
            else:
                class_summary = {
                    "total_students": 0,
                    "present_count": 0,
                    "absent_count": 0,
                    "late_count": 0,
                    "excused_count": 0,
                    "attendance_percentage": 0.0,
                    "needs_attention": []
                }

            # Get professor name for export
            cursor.execute("SELECT (last_name || ', ' || first_name) FROM instructors WHERE instructor_id = ?", (request.instructor_id,))
            professor_row = cursor.fetchone()
            professor_name = professor_row[0] if professor_row else "System Admin"

            # Create report
            from datetime import datetime
            report = {
                "report_title": f"Attendance Report - {request.course_code or 'All Classes'}",
                "generated_at": datetime.now().isoformat(),
                "exported_by": professor_name,
                "date_range": f"{request.date_from or 'N/A'} to {request.date_to or 'N/A'}",
                "records": records,
                "class_summary": class_summary
            }

            # Handle different export formats
            if request.export_format == "csv":
                csv_content = generate_csv_report(report)
                return Response(
                    content=csv_content,
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=attendance_report.csv"}
                )
            elif request.export_format == "excel":
                excel_content = generate_excel_report(report)
                return Response(
                    content=excel_content,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=attendance_report.xlsx"}
                )
            elif request.export_format == "pdf":
                pdf_content = generate_pdf_report(report)
                return Response(
                    content=pdf_content,
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=attendance_report.pdf"}
                )
            else:
                return report

    except Exception as e:
        LOG.exception("Attendance export failed")
        raise HTTPException(500, f"Error generating report: {str(e)}")

# Helper to generate attendance report using an existing DB cursor
def _generate_attendance_report(cursor, request: AttendanceExportRequest) -> dict:
    """Generate attendance report dict using provided DB cursor and request filters."""
    db_url = os.environ.get('DATABASE_URL', '')
    is_postgres = bool(db_url and not db_url.lower().startswith('sqlite'))
    if is_postgres:
        date_expr = "(a.timestamp AT TIME ZONE 'Asia/Manila')::date"
        time_expr = "to_char(a.timestamp AT TIME ZONE 'Asia/Manila', 'HH12:MI:SS AM')"
    else:
        date_expr = "strftime('%Y-%m-%d', a.timestamp)"
        time_expr = "strftime('%H:%M:%S', a.timestamp)"

    # Build the main query
    base_query = f"""
                SELECT
                    s.student_number as student_id,
                    (s.last_name || ', ' || s.first_name) as student_name,
                    {date_expr} as date,
                    {time_expr} as time_in,
                    ast.status_name as status,
                    c.course_id,
                    c.section,
                    i.instructor_id,
                    (i.last_name || ', ' || i.first_name) as instructor_name,
                    co.course_code,
                    co.course_name
                FROM attendance_logs a
                JOIN students s ON a.student_id = s.student_id
                JOIN attendance_status_types ast ON a.status_id = ast.status_id
                JOIN classes c ON a.class_id = c.class_id
                JOIN instructors i ON c.instructor_id = i.instructor_id
                JOIN courses co ON c.course_id = co.course_id
                WHERE 1=1
            """

    params = []

    if request.date_from:
        base_query += f" AND {date_expr} >= ?"
        params.append(request.date_from)

    if request.date_to:
        base_query += f" AND {date_expr} <= ?"
        params.append(request.date_to)

    if request.student_ids:
        placeholders = ','.join('?' * len(request.student_ids))
        base_query += f" AND s.student_id IN ({placeholders})"
        params.extend(request.student_ids)

    if request.class_id:
        base_query += " AND c.class_id = ?"
        params.append(request.class_id)

    if request.status_filter:
        placeholders = ','.join('?' * len(request.status_filter))
        base_query += f" AND ast.status_name IN ({placeholders})"
        params.extend(request.status_filter)

    if request.course_code:
        base_query += " AND co.course_code = ?"
        params.append(request.course_code)

    if request.section:
        base_query += " AND c.section = ?"
        params.append(request.section)

    if request.instructor_id:
        base_query += " AND i.instructor_id = ?"
        params.append(request.instructor_id)

    base_query += " ORDER BY a.timestamp DESC"

    cursor.execute(base_query, params)
    rows = cursor.fetchall()

    # Process results
    records = []
    for row in rows:
        records.append({
            "student_id": row[0] or "N/A",
            "student_name": row[1] or "N/A",
            "date": str(row[2]) if row[2] is not None else "N/A",
            "time_in": str(row[3]) if row[3] is not None else "N/A",
            "status": row[4] or "N/A"
        })

    # Generate class summary
    if records:
        status_counts = {}
        student_absences = {}

        for record in records:
            status = record["status"]
            student_id = record["student_id"]

            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

            if status == "Absent":
                if student_id not in student_absences:
                    student_absences[student_id] = 0
                student_absences[student_id] += 1

        unique_students = len(set(r["student_id"] for r in records))

        present_count = status_counts.get("Present", 0)
        absent_count = status_counts.get("Absent", 0)
        late_count = status_counts.get("Late", 0)
        excused_count = status_counts.get("Excused", 0)

        total_records = len(records)
        attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0

        needs_attention = [student_id for student_id, absences in student_absences.items() if absences > 3]

        class_summary = {
            "total_students": unique_students,
            "present_count": present_count,
            "absent_count": absent_count,
            "late_count": late_count,
            "excused_count": excused_count,
            "attendance_percentage": round(attendance_percentage, 2),
            "needs_attention": needs_attention
        }
    else:
        class_summary = {
            "total_students": 0,
            "present_count": 0,
            "absent_count": 0,
            "late_count": 0,
            "excused_count": 0,
            "attendance_percentage": 0.0,
            "needs_attention": []
        }

    # Determine exported_by
    exported_by = "System Admin"
    if request.instructor_id:
        cursor.execute("SELECT (last_name || ', ' || first_name) FROM instructors WHERE instructor_id = ?", (request.instructor_id,))
        row = cursor.fetchone()
        exported_by = row[0] if row else exported_by

    from datetime import datetime
    report = {
        "report_title": f"Attendance Report - {request.course_code or 'All Classes'}",
        "generated_at": datetime.now().isoformat(),
        "exported_by": exported_by,
        "date_range": f"{request.date_from or 'N/A'} to {request.date_to or 'N/A'}",
        "records": records,
        "class_summary": class_summary
    }

    return report

@router.post("/api/admin/attendance/export/professor")
async def export_professor_attendance_report(
    request: AttendanceExportRequest,
    admin_type: str = Depends(require_admin_permission("view_all_data"))
):
    """Generate consolidated attendance report for all classes handled by a professor"""
    try:
        # Allow identifying professor by `instructor_id` or by `professor_name` search
        if not request.instructor_id and not request.professor_name:
            raise HTTPException(400, "instructor_id or professor_name is required for professor reports. Admins should provide instructor_id or search by professor_name.")

        with get_connection() as conn:
            cursor = conn.cursor()

            # If professor_name provided, resolve to instructor_id (simple LIKE search)
            if not request.instructor_id and request.professor_name:
                name_search = f"%{request.professor_name.strip()}%"
                cursor.execute("SELECT instructor_id, (last_name || ', ' || first_name) FROM instructors WHERE (last_name || ', ' || first_name) LIKE ? OR first_name LIKE ? OR last_name LIKE ?", (name_search, name_search, name_search))
                matches = cursor.fetchall()
                if not matches:
                    raise HTTPException(404, f"No instructor found matching '{request.professor_name}'")
                if len(matches) > 1:
                    # Multiple matches - ask caller to provide explicit instructor_id
                    match_list = [f"{m[0]}: {m[1]}" for m in matches]
                    raise HTTPException(400, f"Multiple instructors match '{request.professor_name}': {match_list}. Please provide instructor_id.")
                # single match
                request.instructor_id = matches[0][0]

            # Get classes for this professor (optionally filtered by selected class/course/section)
            classes_query = """
                SELECT c.class_id, co.course_code, co.course_name, c.section
                FROM classes c
                JOIN courses co ON c.course_id = co.course_id
                WHERE c.instructor_id = ?
            """
            classes_params = [request.instructor_id]

            if request.course_code:
                classes_query += " AND co.course_code = ?"
                classes_params.append(request.course_code)

            if request.section:
                classes_query += " AND c.section = ?"
                classes_params.append(request.section)

            if request.class_id:
                classes_query += " AND c.class_id = ?"
                classes_params.append(request.class_id)

            cursor.execute(classes_query, tuple(classes_params))

            classes = cursor.fetchall()

            if not classes:
                raise HTTPException(404, "No classes found for this professor")

            # Get professor name
            cursor.execute("SELECT (last_name || ', ' || first_name) FROM instructors WHERE instructor_id = ?", (request.instructor_id,))
            professor_row = cursor.fetchone()
            professor_name = professor_row[0] if professor_row else "Unknown Professor"

            # Generate report for each class
            class_reports = []
            consolidated_stats = {
                "total_students": 0,
                "present_count": 0,
                "absent_count": 0,
                "late_count": 0,
                "excused_count": 0,
                "needs_attention": []
            }

            for class_info in classes:
                class_id, course_code, course_name, section = class_info

                # Create request for this specific class
                class_request = AttendanceExportRequest(
                    date_from=request.date_from,
                    date_to=request.date_to,
                    class_id=class_id,
                    student_ids=request.student_ids,
                    status_filter=request.status_filter,
                    course_code=course_code,
                    section=section,
                    instructor_id=request.instructor_id,
                    export_format="json"
                )

                # Get class report using helper (reuse query logic without opening new DB connections)
                class_report = _generate_attendance_report(cursor, class_request)
                class_reports.append(class_report)

                # Accumulate consolidated stats
                summary = class_report["class_summary"]
                consolidated_stats["total_students"] += summary["total_students"]
                consolidated_stats["present_count"] += summary["present_count"]
                consolidated_stats["absent_count"] += summary["absent_count"]
                consolidated_stats["late_count"] += summary["late_count"]
                consolidated_stats["excused_count"] += summary["excused_count"]
                consolidated_stats["needs_attention"].extend(summary["needs_attention"])

            # Calculate consolidated attendance percentage
            total_records = (consolidated_stats["present_count"] + consolidated_stats["absent_count"] +
                           consolidated_stats["late_count"] + consolidated_stats["excused_count"])
            consolidated_stats["attendance_percentage"] = (
                consolidated_stats["present_count"] / total_records * 100
            ) if total_records > 0 else 0.0

            # Remove duplicates from needs_attention
            consolidated_stats["needs_attention"] = list(set(consolidated_stats["needs_attention"]))

            professor_report = {
                "professor_name": professor_name,
                "generated_at": datetime.now().isoformat(),
                "exported_by": "System Admin",
                "date_range": f"{request.date_from or 'N/A'} to {request.date_to or 'N/A'}",
                "classes": class_reports,
                "consolidated_summary": consolidated_stats
            }

            # Handle export formats
            if request.export_format == "csv":
                csv_content = generate_professor_csv_report(professor_report)
                return Response(
                    content=csv_content,
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=professor_attendance_report.csv"}
                )
            elif request.export_format == "excel":
                excel_content = generate_professor_excel_report(professor_report)
                return Response(
                    content=excel_content,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=professor_attendance_report.xlsx"}
                )
            elif request.export_format == "pdf":
                pdf_content = generate_professor_pdf_report(professor_report)
                return Response(
                    content=pdf_content,
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=professor_attendance_report.pdf"}
                )
            else:
                return professor_report

    except HTTPException:
        raise
    except Exception as e:
        LOG.exception("Professor attendance export failed")
        raise HTTPException(500, f"Error generating professor report: {str(e)}")

# Export format helper functions
def generate_csv_report(report: dict) -> str:
    """Generate CSV format report"""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([report["report_title"]])
    writer.writerow([f"Generated: {report['generated_at']}"])
    writer.writerow([f"Exported by: {report['exported_by']}"])
    writer.writerow([f"Date Range: {report['date_range']}"])
    writer.writerow([])

    # Data headers
    writer.writerow(["Student ID", "Student Name", "Date", "Time In", "Status"])

    # Data rows
    for record in report["records"]:
        writer.writerow([
            record["student_id"],
            record["student_name"],
            record["date"],
            record["time_in"],
            record["status"]
        ])

    # Summary
    writer.writerow([])
    writer.writerow(["SUMMARY"])
    summary = report["class_summary"]
    writer.writerow([f"Total Students: {summary['total_students']}"])
    writer.writerow([f"Present: {summary['present_count']}"])
    writer.writerow([f"Absent: {summary['absent_count']}"])
    writer.writerow([f"Late: {summary['late_count']}"])
    writer.writerow([f"Excused: {summary['excused_count']}"])
    writer.writerow([f"Attendance Percentage: {summary['attendance_percentage']}%"])

    if summary["needs_attention"]:
        writer.writerow([])
        writer.writerow(["Students Needing Attention (>3 absences):"])
        for student in summary["needs_attention"]:
            writer.writerow([student])

    return output.getvalue()

def generate_excel_report(report: dict):
    """Generate Excel format report using openpyxl"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    import io

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance Report"

    # Header
    ws['A1'] = report["report_title"]
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = f"Generated: {report['generated_at']}"
    ws['A3'] = f"Exported by: {report['exported_by']}"
    ws['A4'] = f"Date Range: {report['date_range']}"

    # Data headers
    ws['A6'] = "Student ID"
    ws['B6'] = "Student Name"
    ws['C6'] = "Date"
    ws['D6'] = "Time In"
    ws['E6'] = "Status"

    # Style headers
    for col in ['A', 'B', 'C', 'D', 'E']:
        ws[f'{col}6'].font = Font(bold=True)

    # Data rows
    row = 7
    for record in report["records"]:
        ws[f'A{row}'] = record["student_id"]
        ws[f'B{row}'] = record["student_name"]
        ws[f'C{row}'] = record["date"]
        ws[f'D{row}'] = record["time_in"]
        ws[f'E{row}'] = record["status"]
        row += 1

    # Summary section
    summary_row = row + 2
    ws[f'A{summary_row}'] = "SUMMARY"
    ws[f'A{summary_row}'].font = Font(bold=True)

    summary = report["class_summary"]
    ws[f'A{summary_row + 1}'] = f"Total Students: {summary['total_students']}"
    ws[f'A{summary_row + 2}'] = f"Present: {summary['present_count']}"
    ws[f'A{summary_row + 3}'] = f"Absent: {summary['absent_count']}"
    ws[f'A{summary_row + 4}'] = f"Late: {summary['late_count']}"
    ws[f'A{summary_row + 5}'] = f"Excused: {summary['excused_count']}"
    ws[f'A{summary_row + 6}'] = f"Attendance Percentage: {summary['attendance_percentage']}%"

    if summary["needs_attention"]:
        attention_row = summary_row + 8
        ws[f'A{attention_row}'] = "Students Needing Attention (>3 absences):"
        ws[f'A{attention_row}'].font = Font(bold=True)
        for i, student in enumerate(summary["needs_attention"]):
            ws[f'A{attention_row + i + 1}'] = student

    # Auto-adjust column widths
    for col in ['A', 'B', 'C', 'D', 'E']:
        ws.column_dimensions[col].width = 15

    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

def generate_pdf_report(report: dict):
    """Generate PDF format report using reportlab"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import io

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title = Paragraph(report["report_title"], styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Metadata
    meta_text = f"""
    Generated: {report['generated_at']}<br/>
    Exported by: {report['exported_by']}<br/>
    Date Range: {report['date_range']}
    """
    meta = Paragraph(meta_text, styles['Normal'])
    elements.append(meta)
    elements.append(Spacer(1, 12))

    # Data table
    if report["records"]:
        data = [["Student ID", "Student Name", "Date", "Time In", "Status"]]
        for record in report["records"]:
            data.append([
                record["student_id"],
                record["student_name"],
                record["date"],
                record["time_in"],
                record["status"]
            ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    # Summary
    summary = report["class_summary"]
    summary_title = Paragraph("SUMMARY", styles['Heading2'])
    elements.append(summary_title)
    elements.append(Spacer(1, 6))

    summary_text = f"""
    Total Students: {summary['total_students']}<br/>
    Present: {summary['present_count']}<br/>
    Absent: {summary['absent_count']}<br/>
    Late: {summary['late_count']}<br/>
    Excused: {summary['excused_count']}<br/>
    Attendance Percentage: {summary['attendance_percentage']}%
    """
    summary_para = Paragraph(summary_text, styles['Normal'])
    elements.append(summary_para)

    if summary["needs_attention"]:
        elements.append(Spacer(1, 12))
        attention_title = Paragraph("Students Needing Attention (>3 absences):", styles['Heading3'])
        elements.append(attention_title)
        for student in summary["needs_attention"]:
            elements.append(Paragraph(f"• {student}", styles['Normal']))

    doc.build(elements)
    output.seek(0)
    return output.getvalue()

def generate_professor_csv_report(professor_report: dict) -> str:
    """Generate CSV format professor report"""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([f"Professor: {professor_report['professor_name']}"])
    writer.writerow([])

    for class_report in professor_report["classes"]:
        writer.writerow([f"Class: {class_report['report_title']}"])
        writer.writerow(["Student ID", "Student Name", "Date", "Time In", "Status"])

        for record in class_report["records"]:
            writer.writerow([
                record["student_id"],
                record["student_name"],
                record["date"],
                record["time_in"],
                record["status"]
            ])

        writer.writerow([])

    # Consolidated summary
    writer.writerow(["CONSOLIDATED SUMMARY"])
    summary = professor_report["consolidated_summary"]
    writer.writerow([f"Total Students: {summary['total_students']}"])
    writer.writerow([f"Present: {summary['present_count']}"])
    writer.writerow([f"Absent: {summary['absent_count']}"])
    writer.writerow([f"Late: {summary['late_count']}"])
    writer.writerow([f"Excused: {summary['excused_count']}"])
    writer.writerow([f"Attendance Percentage: {summary['attendance_percentage']}%"])

    return output.getvalue()

def generate_professor_excel_report(professor_report: dict):
    """Generate Excel format professor report using openpyxl"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    import io

    wb = Workbook()
    ws = wb.active
    ws.title = "Professor Attendance Report"

    # Header
    ws['A1'] = f"Professor: {professor_report['professor_name']}"
    ws['A1'].font = Font(bold=True, size=14)

    row = 3
    for class_report in professor_report["classes"]:
        ws[f'A{row}'] = f"Class: {class_report['report_title']}"
        ws[f'A{row}'].font = Font(bold=True)
        row += 1

        # Data headers
        ws[f'A{row}'] = "Student ID"
        ws[f'B{row}'] = "Student Name"
        ws[f'C{row}'] = "Date"
        ws[f'D{row}'] = "Time In"
        ws[f'E{row}'] = "Status"

        # Style headers
        for col in ['A', 'B', 'C', 'D', 'E']:
            ws[f'{col}{row}'].font = Font(bold=True)
        row += 1

        # Data rows
        for record in class_report["records"]:
            ws[f'A{row}'] = record["student_id"]
            ws[f'B{row}'] = record["student_name"]
            ws[f'C{row}'] = record["date"]
            ws[f'D{row}'] = record["time_in"]
            ws[f'E{row}'] = record["status"]
            row += 1

        row += 2  # Space between classes

    # Consolidated summary
    summary_row = row + 1
    ws[f'A{summary_row}'] = "CONSOLIDATED SUMMARY"
    ws[f'A{summary_row}'].font = Font(bold=True, size=12)

    summary = professor_report["consolidated_summary"]
    ws[f'A{summary_row + 1}'] = f"Total Students: {summary['total_students']}"
    ws[f'A{summary_row + 2}'] = f"Present: {summary['present_count']}"
    ws[f'A{summary_row + 3}'] = f"Absent: {summary['absent_count']}"
    ws[f'A{summary_row + 4}'] = f"Late: {summary['late_count']}"
    ws[f'A{summary_row + 5}'] = f"Excused: {summary['excused_count']}"
    ws[f'A{summary_row + 6}'] = f"Attendance Percentage: {summary['attendance_percentage']}%"

    # Auto-adjust column widths
    for col in ['A', 'B', 'C', 'D', 'E']:
        ws.column_dimensions[col].width = 15

    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

def generate_professor_pdf_report(professor_report: dict):
    """Generate PDF format professor report using reportlab"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    import io

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title = Paragraph(f"PROFESSOR ATTENDANCE REPORT<br/>Professor: {professor_report['professor_name']}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    for class_report in professor_report["classes"]:
        # Class header
        class_title = Paragraph(f"Class: {class_report['report_title']}", styles['Heading2'])
        elements.append(class_title)
        elements.append(Spacer(1, 6))

        date_range = Paragraph(f"Date Range: {class_report['date_range']}", styles['Normal'])
        elements.append(date_range)
        elements.append(Spacer(1, 12))

        # Data table
        if class_report["records"]:
            data = [["Student ID", "Student Name", "Date", "Time In", "Status"]]
            for record in class_report["records"]:
                data.append([
                    record["student_id"],
                    record["student_name"],
                    record["date"],
                    record["time_in"],
                    record["status"]
                ])

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            elements.append(table)

        # Class summary
        summary = class_report["class_summary"]
        summary_text = f"Class Summary - Students: {summary['total_students']}, Attendance: {summary['attendance_percentage']}%"
        summary_para = Paragraph(summary_text, styles['Italic'])
        elements.append(summary_para)
        elements.append(Spacer(1, 12))

    # Consolidated summary
    elements.append(PageBreak())
    consolidated_title = Paragraph("CONSOLIDATED SUMMARY", styles['Heading1'])
    elements.append(consolidated_title)
    elements.append(Spacer(1, 12))

    summary = professor_report["consolidated_summary"]
    summary_text = f"""
    Total Students: {summary['total_students']}<br/>
    Present: {summary['present_count']}, Absent: {summary['absent_count']}<br/>
    Late: {summary['late_count']}, Excused: {summary['excused_count']}<br/>
    Overall Attendance: {summary['attendance_percentage']}%
    """
    summary_para = Paragraph(summary_text, styles['Normal'])
    elements.append(summary_para)

    doc.build(elements)
    output.seek(0)
    return output.getvalue()


def generate_csv_report(report: dict) -> str:
    """Generate CSV report from attendance data"""
    import io
    output = io.StringIO()

    # Write report header
    output.write(f"Attendance Report: {report['report_title']}\n")
    output.write(f"Generated: {report['generated_at']}\n")
    output.write(f"Exported by: {report['exported_by']}\n")
    output.write(f"Date Range: {report['date_range']}\n")
    output.write("\n")

    # Write class summary
    summary = report['class_summary']
    output.write("CLASS SUMMARY\n")
    output.write(f"Total Students: {summary['total_students']}\n")
    output.write(f"Present: {summary['present_count']}, Absent: {summary['absent_count']}\n")
    output.write(f"Late: {summary['late_count']}, Excused: {summary['excused_count']}\n")
    output.write(f"Attendance Percentage: {summary['attendance_percentage']}%\n")
    if summary['needs_attention']:
        output.write(f"Students Needing Attention: {', '.join(summary['needs_attention'])}\n")
    output.write("\n")

    # Group records by date
    from collections import defaultdict
    records_by_date = defaultdict(list)
    for record in report['records']:
        records_by_date[record['date']].append(record)

    # Sort dates
    sorted_dates = sorted(records_by_date.keys(), reverse=True)

    # Write records header
    output.write("ATTENDANCE RECORDS\n")
    output.write("Student ID,Student Name,Date,Time In,Status\n")

    # Write records grouped by date
    for date in sorted_dates:
        # Date separator
        from datetime import datetime
        try:
            formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%A, %B %d, %Y')
        except:
            formatted_date = date
        output.write(f"\n--- {formatted_date} ({len(records_by_date[date])} records) ---\n")

        # Records for this date
        for record in records_by_date[date]:
            output.write(f"{record['student_id']},{record['student_name']},{record['date']},{record['time_in']},{record['status']}\n")

    return output.getvalue()


def generate_excel_report(report: dict) -> bytes:
    """Generate Excel report from attendance data"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        from io import BytesIO

        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance Report"

        # Report header
        ws['A1'] = f"Attendance Report: {report['report_title']}"
        ws['A2'] = f"Generated: {report['generated_at']}"
        ws['A3'] = f"Exported by: {report['exported_by']}"
        ws['A4'] = f"Date Range: {report['date_range']}"
        ws['A5'] = ""

        # Class summary
        ws['A7'] = "CLASS SUMMARY"
        ws['A8'] = f"Total Students: {report['class_summary']['total_students']}"
        ws['A9'] = f"Present: {report['class_summary']['present_count']}"
        ws['A10'] = f"Absent: {report['class_summary']['absent_count']}"
        ws['A11'] = f"Late: {report['class_summary']['late_count']}"
        ws['A12'] = f"Excused: {report['class_summary']['excused_count']}"
        ws['A13'] = f"Attendance Percentage: {report['class_summary']['attendance_percentage']}%"
        ws['A14'] = ""

        # Group records by date
        from collections import defaultdict
        records_by_date = defaultdict(list)
        for record in report['records']:
            records_by_date[record['date']].append(record)

        # Sort dates
        sorted_dates = sorted(records_by_date.keys(), reverse=True)

        # Records header
        current_row = 16
        ws[f'A{current_row}'] = "Student ID"
        ws[f'B{current_row}'] = "Student Name"
        ws[f'C{current_row}'] = "Date"
        ws[f'D{current_row}'] = "Time In"
        ws[f'E{current_row}'] = "Status"

        # Make header bold
        for col in ['A', 'B', 'C', 'D', 'E']:
            ws[f'{col}{current_row}'].font = Font(bold=True)

        current_row += 1

        # Write records grouped by date
        for date in sorted_dates:
            # Date separator
            from datetime import datetime
            try:
                formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%A, %B %d, %Y')
            except:
                formatted_date = date

            # Date header row
            ws[f'A{current_row}'] = f"--- {formatted_date} ({len(records_by_date[date])} records) ---"
            ws[f'A{current_row}'].font = Font(bold=True)
            ws[f'A{current_row}'].fill = PatternFill(start_color="FFE6E6FA", end_color="FFE6E6FA", fill_type="solid")
            current_row += 1

            # Records for this date
            for record in records_by_date[date]:
                ws[f'A{current_row}'] = record['student_id']
                ws[f'B{current_row}'] = record['student_name']
                ws[f'C{current_row}'] = record['date']
                ws[f'D{current_row}'] = record['time_in']
                ws[f'E{current_row}'] = record['status']
                current_row += 1

        # Auto-adjust column widths
        for col in ['A', 'B', 'C', 'D', 'E']:
            max_length = 0
            for row in range(1, current_row):
                cell_value = str(ws[f'{col}{row}'].value or '')
                max_length = max(max_length, len(cell_value))
            ws.column_dimensions[col].width = min(max_length + 2, 30)

        # Save to bytes
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    except ImportError:
        # Fallback if openpyxl is not available
        return generate_csv_report(report).encode('utf-8')


def generate_pdf_report(report: dict) -> bytes:
    """Generate PDF report from attendance data"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO

        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title = Paragraph(f"<b>Attendance Report: {report['report_title']}</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Report info
        info_text = f"""
        <b>Generated:</b> {report['generated_at']}<br/>
        <b>Exported by:</b> {report['exported_by']}<br/>
        <b>Date Range:</b> {report['date_range']}
        """
        info = Paragraph(info_text, styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 12))

        # Class summary
        summary_title = Paragraph("<b>Class Summary</b>", styles['Heading2'])
        elements.append(summary_title)
        elements.append(Spacer(1, 6))

        summary = report['class_summary']
        summary_data = [
            ['Total Students', summary['total_students']],
            ['Present', summary['present_count']],
            ['Absent', summary['absent_count']],
            ['Late', summary['late_count']],
            ['Excused', summary['excused_count']],
            ['Attendance Rate', f"{summary['attendance_percentage']}%"]
        ]

        summary_table = Table(summary_data, colWidths=[200, 100])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 12))

        # Records
        records_title = Paragraph("<b>Attendance Records</b>", styles['Heading2'])
        elements.append(records_title)
        elements.append(Spacer(1, 6))

        # Group records by date
        from collections import defaultdict
        records_by_date = defaultdict(list)
        for record in report['records']:
            records_by_date[record['date']].append(record)

        # Sort dates
        sorted_dates = sorted(records_by_date.keys(), reverse=True)

        # Table headers
        headers = ['Student ID', 'Student Name', 'Time In', 'Status']
        records_data = [headers]

        # Add records grouped by date
        for date in sorted_dates:
            # Date separator
            from datetime import datetime
            try:
                formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%A, %B %d, %Y')
            except:
                formatted_date = date

            # Add date header row
            date_header = [f"--- {formatted_date} ({len(records_by_date[date])} records) ---", "", "", ""]
            records_data.append(date_header)

            # Records for this date
            for record in records_by_date[date]:
                records_data.append([
                    record['student_id'],
                    record['student_name'],
                    record['time_in'],
                    record['status']
                ])

        records_table = Table(records_data, colWidths=[80, 150, 80, 80])
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]

        for row_index in range(1, len(records_data)):
            first_cell = records_data[row_index][0]
            if isinstance(first_cell, str) and first_cell.startswith('---'):
                table_style.extend([
                    ('BACKGROUND', (0, row_index), (-1, row_index), colors.lightgrey),
                    ('FONTNAME', (0, row_index), (-1, row_index), 'Helvetica-Bold'),
                    ('SPAN', (0, row_index), (-1, row_index)),
                ])

        records_table.setStyle(TableStyle(table_style))
        elements.append(records_table)

        doc.build(elements)
        output.seek(0)
        return output.getvalue()

    except ImportError:
        # Fallback if reportlab is not available
        return generate_csv_report(report).encode('utf-8')
