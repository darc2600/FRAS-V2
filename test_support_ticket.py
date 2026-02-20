import requests
import json

# Test login
login_data = {
    "email": "admin@mapua.edu.ph",
    "password": "admin123"
}

try:
    login_response = requests.post('http://127.0.0.1:8000/api/login', json=login_data)
    print(f'Login status: {login_response.status_code}')
    if login_response.status_code == 200:
        login_result = login_response.json()
        token = login_result.get('access_token')
        print(f'Login successful, got token: {token[:20]}...')

        # Test support ticket creation
        headers = {'Authorization': f'Bearer {token}'}
        ticket_data = {
            "subject": "Test Support Ticket",
            "description": "This is a test ticket to verify the endpoint works",
            "category": "technical",
            "priority": "high"
        }

        ticket_response = requests.post('http://127.0.0.1:8000/api/support/tickets', json=ticket_data, headers=headers)
        print(f'Ticket creation status: {ticket_response.status_code}')
        print(f'Response: {ticket_response.text}')

    else:
        print(f'Login failed: {login_response.text}')

except Exception as e:
    print(f'Error: {str(e)}')