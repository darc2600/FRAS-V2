#!/usr/bin/env python3
"""
Test script for the new user management system
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_login(email: str, password: str):
    """Test login functionality"""
    print(f"\n--- Testing Login: {email} ---")
    try:
        response = requests.post(f"{BASE_URL}/api/login", json={
            "email": email,
            "password": password
        })

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"User Type: {data.get('user_type')}")
            print(f"Permissions: {data.get('permissions')}")
            return data.get('access_token')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_create_user(token: str, user_data: dict):
    """Test user creation"""
    print(f"\n--- Creating User: {user_data['email']} ---")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/admin/users",
                               json=user_data,
                               headers=headers)

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ User created successfully!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ User creation failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_get_users(token: str):
    """Test getting users list"""
    print("\n--- Getting Users List ---")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Found {len(users)} users:")
            for user in users[:3]:  # Show first 3
                print(f"  - {user.get('email')} ({user.get('user_type')})")
        else:
            print(f"❌ Failed to get users: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("=== Testing New User Management System ===")

    # Test login with super admin
    super_token = test_login("superadmin@fras.com", "super123")
    if not super_token:
        print("❌ Cannot proceed without super admin login")
        return

    # Test creating an instructor
    test_create_user(super_token, {
        "email": "new.instructor@fras.com",
        "password": "instructor123",
        "user_type": "instructor",
        "first_name": "New",
        "last_name": "Instructor"
    })

    # Test creating an IT admin
    test_create_user(super_token, {
        "email": "new.itadmin@fras.com",
        "password": "itadmin123",
        "user_type": "it_admin",
        "first_name": "New",
        "last_name": "IT Admin"
    })

    # Test getting users
    test_get_users(super_token)

    # Test login with new instructor
    test_login("new.instructor@fras.com", "instructor123")

    # Test login with new IT admin
    test_login("new.itadmin@fras.com", "itadmin123")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()