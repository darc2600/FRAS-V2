from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import jwt
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
CORS(app, origins=["http://localhost:4200", "http://127.0.0.1:4200"], supports_credentials=True)

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

@app.route('/test')
def test():
    return jsonify({'message': 'Flask server with database is running!'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    # Get user data
    user_data = get_user_auth(email)
    if not user_data:
        return jsonify({'error': 'Invalid credentials'}), 401

    stored_password, user_type, user_id, reference_id = user_data

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
        return jsonify({'error': 'Invalid credentials'}), 401

    # Get user permissions based on role
    permissions = []
    try:
        with sqlite3.connect(DB_PATH) as perm_conn:
            perm_cursor = perm_conn.cursor()
            perm_cursor.execute("""
                SELECT p.permission_name
                FROM permissions p
                JOIN role_permissions rp ON p.permission_id = rp.permission_id
                WHERE rp.user_type = ?
            """, (user_type,))
            permission_rows = perm_cursor.fetchall()
            permissions = [row[0] for row in permission_rows]
            print(f"DEBUG: Fetched {len(permissions)} permissions for {user_type}: {permissions}")
    except Exception as e:
        print(f"Error fetching permissions: {e}")
        # Fallback to basic permissions
        permissions = ["read", "write"]
        print(f"DEBUG: Using fallback permissions: {permissions}")

    print(f"DEBUG: Final permissions for {user_type}: {permissions}")

    access_token = create_access_token({
        "sub": email,
        "user_type": user_type,
        "user_id": user_id,
        "permissions": permissions
    })

    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": user_type,
        "user_id": user_id,
        "permissions": permissions
    })

@app.route('/api/user/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200

    print("Registration request received")
    print("Headers:", dict(request.headers))
    data = request.get_json()
    print("Request data:", data)

    email = data.get('email')
    password = data.get('password')

    print(f"Extracted: email={email}, password={'*' * len(password) if password else None}")

    if not email or not password:
        print("Missing email or password")
        return jsonify({'error': 'Email and password are required'}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Check if user already exists in users table
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        user_exists = cursor.fetchone()
        print(f"User exists in users table: {user_exists is not None}")
        if user_exists:
            print("Returning 400: User already registered")
            return jsonify({'error': 'User already registered. Please login instead.'}), 400

        # Check which table the email exists in to determine role
        role = None
        reference_id = None

        # Check instructors table
        cursor.execute("SELECT instructor_id, first_name, last_name FROM instructors WHERE email = ?", (email,))
        instructor_data = cursor.fetchone()
        if instructor_data:
            role = 'instructor'
            reference_id = instructor_data[0]
            print(f"Found in instructors table: ID={reference_id}, Name={instructor_data[1]} {instructor_data[2]}")

        # Check it_admins table
        if not role:
            cursor.execute("SELECT it_admin_id, first_name, last_name FROM it_admins WHERE email = ?", (email,))
            admin_data = cursor.fetchone()
            if admin_data:
                role = 'it_admin'
                reference_id = admin_data[0]
                print(f"Found in it_admins table: ID={reference_id}, Name={admin_data[1]} {admin_data[2]}")

        # Check super_admins table
        if not role:
            cursor.execute("SELECT super_admin_id, first_name, last_name FROM super_admins WHERE email = ?", (email,))
            super_admin_data = cursor.fetchone()
            if super_admin_data:
                role = 'super_admin'
                reference_id = super_admin_data[0]
                print(f"Found in super_admins table: ID={reference_id}, Name={super_admin_data[1]} {super_admin_data[2]}")

        if not role:
            print("Email not found in any user tables")
            return jsonify({'error': 'Email not found in system. Please contact administrator for registration.'}), 400

        print(f"Proceeding with registration: role={role}, reference_id={reference_id}")

        # Create user record
        cursor.execute("""
            INSERT INTO users (email, password, role, reference_id, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (email, password, role, reference_id))

        user_id = cursor.lastrowid
        conn.commit()

        print(f"Registration successful: user_id={user_id}, role={role}")

        return jsonify({
            'message': 'Registration successful! You can now login.',
            'user_type': role,
            'email': email
        })

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    # For now, skip authentication check
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, email, role, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()

        return jsonify({"users": [
            {
                "id": user[0],
                "email": user[1],
                "user_type": user[2],
                "created_at": user[3]
            } for user in users
        ]})

@app.route('/api/admin/analytics', methods=['GET'])
def get_analytics():
    # For now, skip authentication check
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

        return jsonify({
            "total_students": student_count,
            "total_instructors": instructor_count,
            "total_admins": admin_count,
            "total_attendance_records": attendance_count,
            "total_users": student_count + instructor_count + admin_count
        })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=False)