#!/usr/bin/env python3
"""
Test script to verify super admin login and user creation
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"  # Flask server

def test_super_admin_flow():
    """Test the complete super admin workflow"""
    print("=== Testing Super Admin Registration Flow ===\n")

    # Step 1: Login as super admin
    print("1. Logging in as Super Admin...")
    login_response = requests.post(f"{BASE_URL}/api/login", json={
        "email": "test.superadmin@fras.com",
        "password": "super123"
    })

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return

    login_data = login_response.json()
    token = login_data.get('access_token')
    print("✅ Login successful!")
    print(f"   User Type: {login_data.get('user_type')}")
    print(f"   Permissions: {login_data.get('permissions')}")

    # Step 2: Create a new instructor
    print("\n2. Creating a new Instructor...")
    instructor_data = {
        "email": "new.instructor@test.com",
        "password": "instructor123",
        "user_type": "instructor",
        "first_name": "John",
        "last_name": "Doe"
    }

    headers = {"Authorization": f"Bearer {token}"}
    create_response = requests.post(f"{BASE_URL}/api/admin/users",
                                  json=instructor_data,
                                  headers=headers)

    if create_response.status_code == 200:
        print("✅ Instructor created successfully!")
        print(f"   Response: {create_response.json()}")
    else:
        print(f"❌ Instructor creation failed: {create_response.text}")

    # Step 3: Create a new IT admin
    print("\n3. Creating a new IT Admin...")
    it_admin_data = {
        "email": "new.itadmin@test.com",
        "password": "itadmin123",
        "user_type": "it_admin",
        "first_name": "Jane",
        "last_name": "Smith"
    }

    create_response2 = requests.post(f"{BASE_URL}/api/admin/users",
                                   json=it_admin_data,
                                   headers=headers)

    if create_response2.status_code == 200:
        print("✅ IT Admin created successfully!")
        print(f"   Response: {create_response2.json()}")
    else:
        print(f"❌ IT Admin creation failed: {create_response2.text}")

    # Step 4: Get users list
    print("\n4. Getting users list...")
    users_response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)

    if users_response.status_code == 200:
        users = users_response.json()
        print(f"✅ Found {len(users)} users")
        # Show last few users (the newly created ones)
        for user in users[-3:]:
            print(f"   - {user.get('email')} ({user.get('user_type')})")
    else:
        print(f"❌ Failed to get users: {users_response.text}")

    # Step 5: Test login with new instructor
    print("\n5. Testing login with new Instructor...")
    instructor_login = requests.post(f"{BASE_URL}/api/login", json={
        "email": "new.instructor@test.com",
        "password": "instructor123"
    })

    if instructor_login.status_code == 200:
        inst_data = instructor_login.json()
        print("✅ Instructor login successful!")
        print(f"   User Type: {inst_data.get('user_type')}")
        print(f"   Permissions: {inst_data.get('permissions')}")
    else:
        print(f"❌ Instructor login failed: {instructor_login.text}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_super_admin_flow()