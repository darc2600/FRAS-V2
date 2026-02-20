#!/usr/bin/env python3
"""
Test script for attendance export endpoints
"""
import requests
import json
import jwt
from datetime import datetime, timedelta

# JWT settings (matching backend)
JWT_SECRET = "dev-secret-change-me"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440

def create_jwt_token(user_id: int = 1, user_type: str = "super_admin", email: str = "test.superadmin@fras.com"):
    """Create a JWT token for testing"""
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "user_type": user_type,
        "email": email,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# Test the attendance export endpoints
def test_attendance_export():
    base_url = "http://localhost:8000"  # Adjust if your server runs on different port

    # Create JWT token for super admin
    token = create_jwt_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Test data
    export_request = {
        "date_from": "2024-01-01",
        "date_to": "2024-12-31",
        "export_format": "json"
    }

    try:
        # Test class attendance export
        print("Testing class attendance export...")
        response = requests.post(
            f"{base_url}/api/admin/attendance/export",
            json=export_request,
            headers=headers
        )

        if response.status_code == 200:
            print("✓ Class attendance export endpoint working")
            if export_request["export_format"] == "json":
                data = response.json()
                print(f"  Report title: {data.get('report_title', 'N/A')}")
                print(f"  Records count: {len(data.get('records', []))}")
                print(f"  Attendance percentage: {data.get('class_summary', {}).get('attendance_percentage', 'N/A')}%")
        else:
            print(f"✗ Class attendance export failed: {response.status_code}")
            print(f"  Response: {response.text}")

        # Test CSV export
        print("\nTesting CSV export...")
        csv_request = export_request.copy()
        csv_request["export_format"] = "csv"

        response = requests.post(
            f"{base_url}/api/admin/attendance/export",
            json=csv_request,
            headers=headers
        )

        if response.status_code == 200:
            print("✓ CSV export working")
            print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"  Content-Length: {len(response.content)} bytes")
        else:
            print(f"✗ CSV export failed: {response.status_code}")

        # Test Excel export
        print("\nTesting Excel export...")
        excel_request = export_request.copy()
        excel_request["export_format"] = "excel"

        response = requests.post(
            f"{base_url}/api/admin/attendance/export",
            json=excel_request,
            headers=headers
        )

        if response.status_code == 200:
            print("✓ Excel export working")
            print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"  Content-Length: {len(response.content)} bytes")
        else:
            print(f"✗ Excel export failed: {response.status_code}")

        # Test PDF export
        print("\nTesting PDF export...")
        pdf_request = export_request.copy()
        pdf_request["export_format"] = "pdf"

        response = requests.post(
            f"{base_url}/api/admin/attendance/export",
            json=pdf_request,
            headers=headers
        )

        if response.status_code == 200:
            print("✓ PDF export working")
            print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"  Content-Length: {len(response.content)} bytes")
        else:
            print(f"✗ PDF export failed: {response.status_code}")

        # Test professor attendance export (requires instructor_id)
        print("\nTesting professor attendance export...")
        professor_request = export_request.copy()
        professor_request["instructor_id"] = 1  # Assuming instructor with ID 1 exists

        response = requests.post(
            f"{base_url}/api/admin/attendance/export/professor",
            json=professor_request,
            headers=headers
        )

        if response.status_code == 200:
            print("✓ Professor attendance export endpoint working")
            data = response.json()
            print(f"  Professor: {data.get('professor_name', 'N/A')}")
            print(f"  Classes count: {len(data.get('classes', []))}")
        elif response.status_code == 404:
            print("⚠ Professor attendance export: No classes found for instructor (expected if no data)")
        else:
            print(f"✗ Professor attendance export failed: {response.status_code}")
            print(f"  Response: {response.text}")

        # Test with filters
        print("\nTesting with status filter...")
        filtered_request = export_request.copy()
        filtered_request["status_filter"] = ["Present", "Absent"]

        response = requests.post(
            f"{base_url}/api/admin/attendance/export",
            json=filtered_request,
            headers=headers
        )

        if response.status_code == 200:
            print("✓ Filtered export working")
            if filtered_request["export_format"] == "json":
                data = response.json()
                print(f"  Filtered records: {len(data.get('records', []))}")
        else:
            print(f"✗ Filtered export failed: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Make sure the backend is running on http://localhost:8000")
        print("  Start the server with: python flask_server.py")
    except Exception as e:
        print(f"✗ Test failed with error: {e}")

if __name__ == "__main__":
    test_attendance_export()