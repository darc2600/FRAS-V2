import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000"
session = requests.Session()
results = {"login": None, "create_user": None, "delete_user": None}

# obtain token
creds = [("test.superadmin@fras.com", "password123"), ("superadmin@fras.com", "super123")]
for email, pwd in creds:
    try:
        r = session.post(f"{BASE_URL}/api/login", json={"email": email, "password": pwd}, timeout=5)
        if r.status_code in (200,201):
            try:
                token = r.json().get("access_token")
            except Exception:
                token = None
            if token:
                session.headers.update({"Authorization": f"Bearer {token}"})
                results["login"] = {"email": email, "status": r.status_code}
                break
            else:
                results["login"] = {"email": email, "status": r.status_code, "note": "no token"}
    except Exception as e:
        results["login"] = {"email": email, "error": str(e)}

if not results.get("login"):
    print(json.dumps({"error": "no login token obtained"}))
    raise SystemExit(1)

# create unique user
ts = int(time.time())
email = f"ci.test.user.{ts}@fras.local"
payload = {
    "email": email,
    "password": "TempPass!123",
    "user_type": "instructor",
    "first_name": "CI",
    "last_name": "TestUser"
}
try:
    r = session.post(f"{BASE_URL}/api/admin/users", json=payload, timeout=10)
    results["create_user"] = {"status": r.status_code, "text": r.text}
    user_id = None
    if r.status_code in (200,201):
        try:
            user_id = r.json().get("user_id") or r.json().get("id")
        except Exception:
            # try common shapes
            try:
                body = r.json()
                if isinstance(body, dict):
                    # find first int value
                    for k,v in body.items():
                        if isinstance(v, int):
                            user_id = v
                            break
            except Exception:
                pass
    # if creation succeeded and we have user_id, attempt delete
    if user_id:
        dr = session.delete(f"{BASE_URL}/api/admin/users/{user_id}", timeout=10)
        results["delete_user"] = {"status": dr.status_code, "text": dr.text}
    else:
        results["delete_user"] = {"status": "skipped", "reason": "no user_id returned"}
except Exception as e:
    results["create_user"] = {"error": str(e)}

with open("tools/smoke_test_post_results.json", "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=2)

print(json.dumps(results, indent=2))
print("Wrote tools/smoke_test_post_results.json")
