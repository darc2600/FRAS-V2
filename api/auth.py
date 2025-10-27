
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import sqlite3
import secrets
from typing import Optional

# Optional imports for secure password hashing / verification
try:
	from passlib.hash import bcrypt
	_HAS_BCRYPT = True
except Exception:
	_HAS_BCRYPT = False

DB_PATH = "attendance.db"

router = APIRouter()


class LoginRequest(BaseModel):
	username: str
	password: str


def _ensure_users_table():
	"""Create a minimal users table if it doesn't exist."""
	with sqlite3.connect(DB_PATH) as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				user_id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT UNIQUE NOT NULL,
				password TEXT NOT NULL,
				created_at TEXT DEFAULT (datetime('now'))
			)
			"""
		)
		conn.commit()


def _seed_test_user(username: str = "admin", password: str = "admin"):
	"""Insert a test user if it doesn't already exist.

	This stores the password in plaintext unless passlib/bcrypt is available,
	in which case it stores a bcrypt hash. This keeps the dependency optional
	for quick local testing while recommending a hashed password for real use.
	"""
	_ensure_users_table()
	with sqlite3.connect(DB_PATH) as conn:
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
		if cur.fetchone()[0] == 0:
			if _HAS_BCRYPT:
				stored = bcrypt.hash(password)
			else:
				stored = password
			cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, stored))
			conn.commit()


def _get_user_password(username: str) -> Optional[str]:
	_ensure_users_table()
	with sqlite3.connect(DB_PATH) as conn:
		cur = conn.cursor()
		cur.execute("SELECT password FROM users WHERE username = ?", (username,))
		row = cur.fetchone()
		return row[0] if row else None


@router.post("/api/login")
async def login(payload: LoginRequest):
	"""Simple login endpoint for development/testing.

	Request JSON: { "username": "...", "password": "..." }

	Response on success: { "status": "ok", "username": "...", "token": "..." }
	"""
	# Ensure table and a test user exist (safe no-op if already present)
	_seed_test_user()

	stored = _get_user_password(payload.username)
	if stored is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

	valid = False
	# If passlib bcrypt is available we expect the stored value to be a bcrypt hash
	if _HAS_BCRYPT:
		try:
			valid = bcrypt.verify(payload.password, stored)
		except Exception:
			valid = False
	else:
		# Plaintext comparison (development only)
		valid = (payload.password == stored)

	if not valid:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

	# Issue a short-lived random token for the frontend to use as a placeholder.
	# For production replace this with a signed JWT and proper session handling.
	token = secrets.token_urlsafe(24)

	# Return username key (frontend expects `username`) — username field is used as the username/identifier
	return {"status": "ok", "username": payload.username, "token": token}
