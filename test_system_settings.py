#!/usr/bin/env python3
"""
Test system settings endpoints
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_system_settings():
    """Test the system settings endpoints"""

    print("Testing system settings endpoints...")

    try:
        # Test get system settings (this should work without auth for now)
        response = requests.get(f"{BASE_URL}/api/admin/system-settings")
        print(f"GET /api/admin/system-settings: {response.status_code}")

        if response.status_code == 200:
            settings = response.json()
            print(f"Retrieved {len(settings)} settings")
            print("Sample settings:")
            for i, (key, value) in enumerate(list(settings.items())[:5]):
                print(f"  {key}: {value}")
        else:
            print(f"Error: {response.text}")

        # Test analytics endpoint
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        print(f"GET /api/admin/analytics: {response.status_code}")

        if response.status_code == 200:
            analytics = response.json()
            print("Analytics data:")
            for key, value in analytics.items():
                print(f"  {key}: {value}")
        else:
            print(f"Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Backend server is not running")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_system_settings()