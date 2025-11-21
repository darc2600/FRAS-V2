import requests

try:
    r = requests.get('http://127.0.0.1:8000/test')
    print(f'Server status: {r.status_code} - {r.json()}')
except Exception as e:
    print(f'Server not running or not accessible: {str(e)}')