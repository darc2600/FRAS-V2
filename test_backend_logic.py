import sqlite3
import os
import jwt
from datetime import datetime, timedelta

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

# JWT settings
JWT_SECRET = "dev-secret-change-me"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_user_auth(email: str):
    """Get user authentication data from database"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT password, role, user_id, reference_id
            FROM users
            WHERE email = ?
        """, (email,))
        result = cursor.fetchone()
        return result

def test_login(email: str, password: str):
    """Test login functionality"""
    print(f"Testing login for: {email}")

    # Get user data
    user_data = get_user_auth(email)
    if not user_data:
        print("❌ User not found")
        return False

    stored_password, user_type, user_id, reference_id = user_data
    print(f"✅ Found user: {user_type}, ID: {user_id}")

    # Verify password
    valid = False
    if stored_password.startswith('$'):
        # Hashed password
        try:
            import importlib
            _pb = importlib.import_module("passlib.hash")
            bcrypt = getattr(_pb, "bcrypt")
            pbkdf2_sha256 = getattr(_pb, "pbkdf2_sha256")
            if pbkdf2_sha256 and stored_password.startswith('$pbkdf2-sha256$'):
                valid = pbkdf2_sha256.verify(password, stored_password)
            elif bcrypt and stored_password.startswith('$2b$'):
                valid = bcrypt.verify(password, stored_password)
            else:
                valid = False
        except Exception:
            valid = False
    else:
        # Plaintext password (fallback)
        valid = (password == stored_password)

    if not valid:
        print("❌ Invalid password")
        return False

    access_token = create_access_token({
        "sub": email,
        "user_type": user_type,
        "user_id": user_id,
        "permissions": ["read"] if user_type == "student" else ["read", "write", "admin"]
    })

    print("✅ Login successful!")
    print(f"Token: {access_token[:50]}...")
    print(f"User Type: {user_type}")
    print(f"Permissions: {['read'] if user_type == 'student' else ['read', 'write', 'admin']}")
    return True

def test_admin_endpoints():
    """Test admin functionality"""
    print("\n--- Testing Admin Endpoints ---")

    with sqlite3.connect(DB_PATH) as conn:
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

        print(f"Students: {student_count}")
        print(f"Instructors: {instructor_count}")
        print(f"Admins: {admin_count}")
        print(f"Attendance Records: {attendance_count}")

        # Get all users
        cursor.execute("""
            SELECT user_id, email, role, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()

        print(f"\nUsers in system ({len(users)}):")
        for user in users:
            print(f"  - {user[1]} ({user[2]})")

if __name__ == "__main__":
    print("=== FRAS Backend Test ===")

    # Test admin login
    print("\n--- Testing Admin Login ---")
    test_login("testadmin@fras.com", "admin123")

    # Test instructor login (if exists)
    print("\n--- Testing Instructor Login ---")
    test_login("instructor@mapua.edu.ph", "password")

    # Test admin endpoints
    test_admin_endpoints()

    print("\n=== Test Complete ===")