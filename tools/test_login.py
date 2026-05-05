import requests
r = requests.post('http://127.0.0.1:8000/api/login', json={'email':'superadmin@fras.com','password':'superadmin'})
print(r.status_code)
print(r.text)
