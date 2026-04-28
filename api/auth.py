
import os
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from services.db import get_connection
import secrets
from typing import Optional
import importlib
import jwt
from datetime import datetime, timedelta

# Optional imports for secure password hashing / verification
try:
	from passlib.hash import bcrypt, pbkdf2_sha256
	_HAS_PASSLIB = True
except ImportError:
	try:
		# Fallback to bcrypt package directly
		import bcrypt as bcrypt_pkg
		bcrypt = None  # We'll handle this in verification
		pbkdf2_sha256 = None
		_HAS_PASSLIB = False
		_HAS_BCRYPT = True
	except ImportError:
		bcrypt = None
		pbkdf2_sha256 = None
		_HAS_PASSLIB = False
		_HAS_BCRYPT = False

# DB access is handled via `get_connection()` which supports sqlite and Postgres

# JWT settings - moved to environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")  # Use env var with fallback
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440

# Security scheme for JWT
security = HTTPBearer()


def _normalize_permission_name(permission_name: str) -> str:
    """Normalize legacy or human-readable permission names to canonical keys."""
    if not permission_name:
        return ""

    raw = str(permission_name).strip().lower()
    if not raw:
        return ""

    aliases = {
        "view own attendance": "view_own_schedule",
        "view_own_attendance": "view_own_schedule",
        "view own schedule": "view_own_schedule",
        "view personal schedule": "view_own_schedule",
        "view attendance logs": "view_attendance_logs",
        "mark attendance using facial recognition": "mark_attendance",
        "register new students": "register_students",
        "create and manage user accounts": "manage_users",
        "edit room and schedule configurations": "manage_rooms_schedule",
        "view system analytics and reports": "view_analytics",
        "view all data": "view_all_data",
        "view analytics": "view_analytics",
        "reset user passwords": "reset_passwords",
        "reset passwords": "reset_passwords",
        "system admin": "system_config",
        "manage content": "content_management",
    }

    if raw in aliases:
        return aliases[raw]

    return raw.replace(" ", "_").replace("-", "_")

def get_current_user_type(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user type from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user_type", "regular")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user ID from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        return int(user_id)  # Ensure it's an integer
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID in token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_user_permissions(user_type: str) -> list:
    """Get permissions for a user type"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.permission_name
                FROM permissions p
                JOIN role_permissions rp ON p.permission_id = rp.permission_id
                WHERE rp.user_type = ?
            """, (user_type,))
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching permissions for {user_type}: {e}")
        return []

def get_user_type_from_email(email: str) -> str:
    """Get user type from email by checking users table"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            if result:
                return result[0]
    except Exception as e:
        print(f"Error getting user type from email {email}: {e}")
    return 'regular'

router = APIRouter()


class LoginRequest(BaseModel):
	email: str
	password: str


def create_access_token(data: dict):
	to_encode = data.copy()
	expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
	return encoded_jwt

def get_user_permissions(user_type: str) -> list:
    """Get permissions for a user type from the database using canonical permission keys."""
    raw_permissions = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.permission_name
                FROM permissions p
                JOIN role_permissions rp ON p.permission_id = rp.permission_id
                WHERE rp.user_type = ?
            """, (user_type,))
            raw_permissions = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting permissions for {user_type}: {e}")

    permissions = {_normalize_permission_name(name) for name in raw_permissions if name}

    if user_type == 'super_admin':
        permissions.update({
            'view_own_attendance', 'mark_attendance', 'manage_users', 'reset_passwords',
            'view_system_logs', 'system_config', 'view_all_data', 'view_analytics', 'manage_admins',
            'content_management', 'audit_logs', 'submit_support', 'manage_support'
        })
    elif user_type == 'it_admin':
        permissions.update({
            'view_own_attendance', 'mark_attendance', 'manage_users', 'reset_passwords',
            'view_system_logs', 'submit_support', 'manage_support', 'view_analytics'
        })
    elif user_type == 'instructor':
        permissions.update({
            'view_own_schedule', 'view_attendance_logs', 'mark_attendance', 'register_students', 'submit_support'
        })

    if 'view_analytics' in permissions:
        permissions.add('view_all_data')
    if 'view_all_data' in permissions:
        permissions.add('view_analytics')
    if 'manage_users' in permissions:
        permissions.add('reset_passwords')

    return sorted(permissions)


def _get_user_auth(email: str):
    """Get user authentication data from users table."""
    # Try multiple schemas: prefer `users` table if present, otherwise search
    # `students`, `instructors`, `admins`, `super_admins` tables for legacy data.
    try:
        with get_connection() as conn:
            cur = conn.cursor()

            # 1) users table (newer consolidated schema)
            try:
                cur.execute("""
                    SELECT u.password, u.role, u.user_id, u.reference_id,
                           COALESCE(u.is_active, TRUE)
                    FROM users u
                    WHERE u.email = ?
                """, (email,))
                result = cur.fetchone()
                if result:
                    password, role, user_id, reference_id, is_active = result
                    user_type_map = {
                        'student': 'regular',
                        'instructor': 'instructor',
                        'admin': 'it_admin',
                        'it_admin': 'it_admin',
                        'super_admin': 'super_admin'
                    }
                    user_type = user_type_map.get(role, 'regular')
                    return (password, user_type, user_id, reference_id, bool(is_active))
            except Exception:
                # users table may not exist in migrated schema
                pass

            # 2) students table
            try:
                cur.execute("SELECT password, student_id FROM students WHERE email = ?", (email,))
                row = cur.fetchone()
                if row:
                    password, student_id = row
                    return (password, 'regular', student_id, student_id, True)
            except Exception:
                pass

            # 3) instructors table
            try:
                cur.execute("SELECT password, instructor_id FROM instructors WHERE email = ?", (email,))
                row = cur.fetchone()
                if row:
                    password, instructor_id = row
                    return (password, 'instructor', instructor_id, instructor_id, True)
            except Exception:
                pass

            # 4) admins table
            try:
                cur.execute("SELECT password, admin_id FROM admins WHERE email = ?", (email,))
                row = cur.fetchone()
                if row:
                    password, admin_id = row
                    return (password, 'it_admin', admin_id, admin_id, True)
            except Exception:
                pass

            # 5) super_admins table
            try:
                cur.execute("SELECT password, super_admin_id FROM super_admins WHERE email = ?", (email,))
                row = cur.fetchone()
                if row:
                    password, super_admin_id = row
                    return (password, 'super_admin', super_admin_id, super_admin_id, True)
            except Exception:
                pass

    except Exception as e:
        print(f"Error fetching auth for {email}: {e}")

    return None



def _update_last_login(user_id: int, user_type: str):
    """Update the last login timestamp for a user in the appropriate table."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            # No-op for current FRAS schema; placeholder for future last_login updates
    except Exception as e:
        print(f"Error updating last login for user {user_id}: {e}")


# Removed _ensure_users_table and _seed_test_user as they're not needed for our FRAS schema




def _get_user_password(email: str) -> Optional[str]:
    """Get user password from our FRAS database schema."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            # Check students table
            cur.execute("SELECT password FROM students WHERE email = ?", (email,))
            row = cur.fetchone()
            if row:
                return row[0]
            # Check instructors table
            cur.execute("SELECT password FROM instructors WHERE email = ?", (email,))
            row = cur.fetchone()
            if row:
                return row[0]
            # Check admins table
            cur.execute("SELECT password FROM admins WHERE email = ?", (email,))
            row = cur.fetchone()
            if row:
                return row[0]
    except Exception as e:
        print(f"Error getting password for {email}: {e}")
    return None


@router.post("/api/login")
async def login(payload: LoginRequest):
    """Login endpoint that returns JWT token.

    Request JSON: { "email": "...", "password": "..." }
    Response on success: { "access_token": "...", "token_type": "bearer", "user_type": "...", "permissions": [...], "user_id": ... }
    """
    user_data = _get_user_auth(payload.email)
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    stored_password, user_type, user_id, reference_id, is_active = user_data

    if not is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    valid = False
    if stored_password.startswith('$'):
        try:
            if pbkdf2_sha256 is not None and stored_password.startswith('$pbkdf2-sha256$'):
                valid = pbkdf2_sha256.verify(payload.password, stored_password)
            elif bcrypt is not None and stored_password.startswith('$2b$'):
                valid = bcrypt.verify(payload.password, stored_password)
            elif _HAS_BCRYPT and stored_password.startswith('$2b$'):
                valid = bcrypt_pkg.checkpw(payload.password.encode('utf-8'), stored_password.encode('utf-8'))
            else:
                valid = False
        except Exception as e:
            print(f"Password verification error: {e}")
            valid = False
    else:
        valid = (payload.password == stored_password)

    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    permissions = get_user_permissions(user_type)
    _update_last_login(user_id, user_type)

    token = create_access_token(data={
        "sub": payload.email,
        "user_type": user_type,
        "permissions": permissions,
        "user_id": user_id
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": user_type,
        "permissions": permissions,
        "user_id": user_id
    }
