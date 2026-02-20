import subprocess
import time
import requests
import json
import sys

def test_flask_server():
    """Test the Flask server by starting it and making requests"""
    print("Starting Flask server...")

    # Start Flask server as subprocess
    server_process = subprocess.Popen(
        [sys.executable, 'flask_server.py'],
        cwd='.',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    time.sleep(3)

    try:
        # Test basic endpoint
        print("Testing /test endpoint...")
        response = requests.get('http://127.0.0.1:8000/test', timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        # Test login endpoint
        print("\nTesting /api/login endpoint...")
        login_data = {
            "email": "admin@mapua.edu.ph",
            "password": "admin123"
        }
        response = requests.post(
            'http://127.0.0.1:8000/api/login',
            json=login_data,
            timeout=5
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"User Type: {data.get('user_type')}")
            print(f"Token: {data.get('access_token')[:50]}...")
        else:
            print(f"❌ Login failed: {response.text}")

        # Test admin analytics
        print("\nTesting /api/admin/analytics endpoint...")
        response = requests.get('http://127.0.0.1:8000/api/admin/analytics', timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Analytics retrieved!")
            print(f"Total Users: {data.get('total_users')}")
            print(f"Students: {data.get('total_students')}")
            print(f"Instructors: {data.get('total_instructors')}")
            print(f"Admins: {data.get('total_admins')}")

        # Test admin users
        print("\nTesting /api/admin/users endpoint...")
        response = requests.get('http://127.0.0.1:8000/api/admin/users', timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Users retrieved!")
            print(f"Number of users: {len(data.get('users', []))}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    finally:
        # Clean up
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    test_flask_server()