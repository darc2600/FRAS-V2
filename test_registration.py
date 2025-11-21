#!/usr/bin/env python3
"""
Test script for the updated registration endpoint
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_registration():
    """Test the registration endpoint"""
    print("=== Testing Instructor Registration ===\n")

    # Test data with unique email
    timestamp = int(time.time())
    registration_data = {
        "email": f"test.instructor{timestamp}@fras.com",
        "password": "Instructor123",
        "first_name": "Test",
        "last_name": "Instructor"
    }

    print("1. Testing registration with complete data...")
    response = requests.post(f"{BASE_URL}/api/user/register",
                           json=registration_data)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ Registration successful!")
        print(f"Response: {data}")

        # Test login with the new user
        print("\n2. Testing login with registered user...")
        login_response = requests.post(f"{BASE_URL}/api/login", json={
            "email": registration_data["email"],
            "password": registration_data["password"]
        })

        print(f"Login Status: {login_response.status_code}")
        if login_response.status_code == 200:
            login_data = login_response.json()
            print("✅ Login successful!")
            print(f"User Type: {login_data.get('user_type')}")
            print(f"Permissions: {login_data.get('permissions')}")
        else:
            print(f"❌ Login failed: {login_response.text}")

    else:
        print(f"❌ Registration failed: {response.text}")

    # Test missing fields
    print("\n3. Testing registration with missing fields...")
    incomplete_data = {
        "email": "incomplete@test.com",
        "password": "Password123"
        # Missing first_name and last_name
    }

    response2 = requests.post(f"{BASE_URL}/api/user/register",
                            json=incomplete_data)

    print(f"Status: {response2.status_code}")
    if response2.status_code == 400:
        print("✅ Correctly rejected incomplete registration")
        print(f"Error: {response2.json()}")
    else:
        print(f"❌ Should have rejected incomplete data: {response2.text}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_registration()