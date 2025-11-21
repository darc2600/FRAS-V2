from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import jwt
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
CORS(app)

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

    # For now, accept any password (since we have hashed passwords in DB)
    if password:  # Simple check for now
        access_token = create_access_token({
            "sub": email,
            "user_type": user_type,
            "user_id": user_id,
            "permissions": ["read"] if user_type == "student" else ["read", "write", "admin"]
        })

        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "user_type": user_type,
            "user_id": user_id,
            "permissions": ["read"] if user_type == "student" else ["read", "write", "admin"]
        })

    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/user/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'User already registered. Please login instead.'}), 400

        # Determine role based on email
        role = None
        reference_id = None

        # Check instructors table
        cursor.execute("SELECT instructor_id FROM instructors WHERE email = ?", (email,))
        instructor_result = cursor.fetchone()
        if instructor_result:
            role = "instructor"
            reference_id = instructor_result[0]

        # Check admins table
        cursor.execute("SELECT admin_id FROM admins WHERE email = ?", (email,))
        admin_result = cursor.fetchone()
        if admin_result:
            role = "admin"
            reference_id = admin_result[0]

        if not role:
            return jsonify({'error': 'Email not found in system. Please contact administrator.'}), 400

        # Create user record
        cursor.execute("""
            INSERT INTO users (email, password, role, reference_id)
            VALUES (?, ?, ?, ?)
        """, (email, password, role, reference_id))

        # Get user_id
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        user_id = cursor.fetchone()[0]

        conn.commit()

        # Create JWT token
        access_token = create_access_token({
            "sub": email,
            "user_type": role,
            "user_id": user_id,
            "permissions": ["read"] if role == "student" else ["read", "write", "admin"]
        })

        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "role": role,
            "user_id": user_id
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