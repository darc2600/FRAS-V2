
import os
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import sqlite3
import secrets
from typing import Optional
import importlib
import jwt
from datetime import datetime, timedelta

# Optional imports for secure password hashing / verification
# not sure how this works but bot suggested it
try:
	_pb = importlib.import_module("passlib.hash")
	bcrypt = getattr(_pb, "bcrypt")
	pbkdf2_sha256 = getattr(_pb, "pbkdf2_sha256")
	_HAS_PASSLIB = True
except Exception:
	bcrypt = None
	pbkdf2_sha256 = None
	_HAS_PASSLIB = False

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "attendance.db")

# JWT settings - moved to environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")  # Use env var with fallback
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440

# Security scheme for JWT
security = HTTPBearer()

def get_current_user_type(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user type from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user_type", "regular")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user_permissions(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user permissions from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("permissions", [])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_user_permissions(user_type: str) -> list:
    """Get permissions for a user type"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.permission_name
            FROM permissions p
            JOIN role_permissions rp ON p.permission_id = rp.permission_id
            WHERE rp.user_type = ?
        """, (user_type,))
        return [row[0] for row in cursor.fetchall()]

def get_user_type_from_email(email: str) -> str:
    """Get user type from email by checking users table"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Check users table
        cursor.execute("SELECT role FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return result[0]  # Return the role directly (instructor, it_admin, super_admin)

        # Default to regular if not found
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


def _get_user_auth(email: str):
	"""Get user authentication data from users table."""
	with sqlite3.connect(DB_PATH) as conn:
		cur = conn.cursor()

		# Check users table
		cur.execute("""
			SELECT u.password, u.role, u.user_id, u.reference_id
			FROM users u
			WHERE u.email = ?
		""", (email,))
		result = cur.fetchone()
		if result:
			password, role, user_id, reference_id = result
			# Map role to user_type
			user_type_map = {
				'student': 'regular',
				'instructor': 'it_admin', 
				'admin': 'super_admin'
			}
			user_type = user_type_map.get(role, 'regular')
			return (password, user_type, user_id, reference_id)

		return None


def _update_last_login(user_id: int, user_type: str):
	"""Update the last login timestamp for a user in the appropriate table."""
	with sqlite3.connect(DB_PATH) as conn:
		cur = conn.cursor()

		if user_type == 'regular':
			# For regular users (students), we don't have a last_login field
			# Could add one later if needed
			pass
		elif user_type == 'it_admin':
			# For IT admins (instructors), we don't have a last_login field
			pass
		elif user_type == 'super_admin':
			# For super admins, we don't have a last_login field
			pass

		conn.commit()


# Removed _ensure_users_table and _seed_test_user as they're not needed for our FRAS schema


def _get_user_password(email: str) -> Optional[str]:
	"""Get user password from our FRAS database schema."""
	with sqlite3.connect(DB_PATH) as conn:
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

		return None


@router.post("/api/login")
async def login(payload: LoginRequest):
	"""Login endpoint that returns JWT token.

	Request JSON: { "email": "...", "password": "..." }
	Response on success: { "access_token": "...", "token_type": "bearer", "user_type": "...", "permissions": [...], "user_id": ... }
	"""
	# Get user authentication data
	user_data = _get_user_auth(payload.email)
	if user_data is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

	stored_password, user_type, user_id, reference_id = user_data

	valid = False
	if stored_password.startswith('$'):
		# Hashed password
		try:
			if pbkdf2_sha256 is not None and stored_password.startswith('$pbkdf2-sha256$'):
				valid = pbkdf2_sha256.verify(payload.password, stored_password)
			elif bcrypt is not None and stored_password.startswith('$2b$'):
				valid = bcrypt.verify(payload.password, stored_password)
			else:
				valid = False
		except Exception:
			valid = False
	else:
		# Plaintext password (fallback for existing users)
		valid = (payload.password == stored_password)

	if not valid:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

	# Get permissions for the user type
	permissions = get_user_permissions(user_type)

	# Update last login
	_update_last_login(user_id, user_type)

	# Create JWT token with user_type and permissions
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
