import subprocess
import time
import requests
import json
import sys
import threading
import signal
import os

class ServerManager:
    def __init__(self):
        self.flask_process = None
        self.angular_process = None
        self.running = True

    def start_flask_server(self):
        """Start Flask server"""
        print("Starting Flask backend server...")
        self.flask_process = subprocess.Popen(
            [sys.executable, 'flask_server.py'],
            cwd='.',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)  # Wait for server to start

    def start_angular_server(self):
        """Start Angular server"""
        print("Starting Angular frontend server...")
        self.angular_process = subprocess.Popen(
            ['ng', 'serve', '--host', '127.0.0.1', '--port', '4200'],
            cwd='facial-attendance',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(10)  # Wait for Angular to compile and start

    def test_backend_api(self):
        """Test backend API endpoints"""
        print("\n=== Testing Backend API ===")

        try:
            # Test basic endpoint
            response = requests.get('http://127.0.0.1:8000/test', timeout=5)
            print(f"✅ /test: {response.status_code} - {response.json()}")

            # Test admin login
            login_data = {"email": "admin@mapua.edu.ph", "password": "admin123"}
            response = requests.post('http://127.0.0.1:8000/api/login', json=login_data, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Admin login successful!")
                print(f"   User Type: {data.get('user_type')}")
                print(f"   Token: {data.get('access_token')[:30]}...")
                self.admin_token = data.get('access_token')
            else:
                print(f"❌ Admin login failed: {response.status_code}")

            # Test instructor login
            login_data = {"email": "isaac.romance@mapua.edu.ph", "password": "password"}
            response = requests.post('http://127.0.0.1:8000/api/login', json=login_data, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Instructor login successful!")
                print(f"   User Type: {data.get('user_type')}")
            else:
                print(f"❌ Instructor login failed: {response.status_code}")

            # Test admin analytics
            response = requests.get('http://127.0.0.1:8000/api/admin/analytics', timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Admin analytics retrieved!")
                print(f"   Total Users: {data.get('total_users')}")
                print(f"   Students: {data.get('total_students')}, Instructors: {data.get('total_instructors')}, Admins: {data.get('total_admins')}")
            else:
                print(f"❌ Admin analytics failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Backend test failed: {e}")
            return False

        return True

    def test_frontend_access(self):
        """Test frontend accessibility"""
        print("\n=== Testing Frontend Access ===")

        try:
            response = requests.get('http://127.0.0.1:4200', timeout=10)
            if response.status_code == 200:
                print("✅ Angular frontend is accessible")
                return True
            else:
                print(f"❌ Angular frontend returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Frontend test failed: {e}")
            return False

    def run_integration_test(self):
        """Run full integration test"""
        print("=== FRAS Integration Test ===")

        # Start servers
        self.start_flask_server()
        self.start_angular_server()

        # Test backend
        backend_ok = self.test_backend_api()

        # Test frontend
        frontend_ok = self.test_frontend_access()

        if backend_ok and frontend_ok:
            print("\n🎉 SUCCESS: Both backend and frontend are working!")
            print("\nYou can now:")
            print("1. Open http://127.0.0.1:4200 in your browser")
            print("2. Login with admin@mapua.edu.ph / admin123")
            print("3. Access admin features and user management")
            print("\nPress Ctrl+C to stop the servers")
        else:
            print("\n❌ Some tests failed. Check the output above.")

        # Keep servers running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping servers...")

        self.cleanup()

    def cleanup(self):
        """Clean up processes"""
        if self.flask_process:
            print("Stopping Flask server...")
            self.flask_process.terminate()
            self.flask_process.wait()

        if self.angular_process:
            print("Stopping Angular server...")
            self.angular_process.terminate()
            self.angular_process.wait()

def main():
    manager = ServerManager()
    try:
        manager.run_integration_test()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main()