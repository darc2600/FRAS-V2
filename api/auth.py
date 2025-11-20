
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import sqlite3
import os
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

DB_PATH = os.path.join(os.getcwd(), "attendance.db")

# JWT settings
JWT_SECRET = "dev-secret-change-me"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440

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
    """Get user type from email by checking all user tables"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Check students table
        cursor.execute("SELECT user_type FROM students WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return result[0]

        # Check instructors table
        cursor.execute("SELECT user_type FROM instructors WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return result[0]

        # Check admins table
        cursor.execute("SELECT user_type FROM admins WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return result[0]

        # Default to regular if not found
        return 'regular'

router = APIRouter()

# Hardcoded test credential (development only)
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpass"


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
	"""Get user authentication data including role."""
	with sqlite3.connect(DB_PATH) as conn:
		cur = conn.cursor()
		cur.execute("""
			SELECT u.password, u.role, u.user_id, u.reference_id 
			FROM users u 
			WHERE u.email = ?
		""", (email,))
		result = cur.fetchone()
		return result


def _update_last_login(user_id: int):
	"""Update the last login timestamp for a user."""
	with sqlite3.connect(DB_PATH) as conn:
		cur = conn.cursor()
		cur.execute("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
		conn.commit()


def _ensure_users_table():
	"""Create a minimal users table if it doesn't exist."""
	with sqlite3.connect(DB_PATH) as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				user_id INTEGER PRIMARY KEY AUTOINCREMENT,
				email TEXT UNIQUE NOT NULL,
				password TEXT NOT NULL,
				created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
				updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)
		conn.commit()


def _seed_test_user(email: str = "testuser@example.com", password: str = "testpass"):
	"""Insert a test user if it doesn't already exist.

	This stores the password in plaintext unless passlib/bcrypt is available,
	in which case it stores a bcrypt hash. This keeps the dependency optional
	for quick local testing while recommending a hashed password for real use.
	"""
	_ensure_users_table()
	with sqlite3.connect(DB_PATH) as conn:
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
		if cur.fetchone()[0] == 0:
			if _HAS_BCRYPT:
				stored = bcrypt.hash(password)
			else:
				stored = password
			cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, stored))
			conn.commit()


def _get_user_password(email: str) -> Optional[str]:
	_ensure_users_table()
	with sqlite3.connect(DB_PATH) as conn:
		cur = conn.cursor()
		cur.execute("SELECT password FROM users WHERE email = ?", (email,))
		row = cur.fetchone()
		return row[0] if row else None


@router.post("/api/login")
async def login(payload: LoginRequest):
	"""Login endpoint that returns JWT token.

	Request JSON: { "email": "...", "password": "..." }
	Response on success: { "access_token": "...", "token_type": "bearer", "user_type": "...", "permissions": [...], "user_id": ... }
	"""
	# Quick dev path: accept a hardcoded test credential
	if payload.email == TEST_EMAIL and payload.password == TEST_PASSWORD:
		user_type = "super_admin"
		permissions = get_user_permissions(user_type)
		token = create_access_token(data={
			"sub": payload.email, 
			"user_type": user_type,
			"permissions": permissions,
			"user_id": 0
		})
		return {
			"access_token": token, 
			"token_type": "bearer", 
			"user_type": user_type,
			"permissions": permissions,
			"user_id": 0
		}

	# Get user authentication data
	user_data = _get_user_auth(payload.email)
	if user_data is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

	stored_password, role, user_id, reference_id = user_data

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

	# Get user type and permissions
	user_type = get_user_type_from_email(payload.email)
	permissions = get_user_permissions(user_type)

	# Update last login
	_update_last_login(user_id)

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
