import requests
import json

BASE_URL = "http://127.0.0.1:8000"
OPENAPI = f"{BASE_URL}/openapi.json"

session = requests.Session()
results = {"openapi": None, "login": None, "paths": {}}

try:
    r = session.get(OPENAPI, timeout=5)
    results["openapi"] = {"status": r.status_code, "ok": r.ok}
    spec = r.json()
    paths = list(spec.get("paths", {}).keys())
except Exception as e:
    print(json.dumps({"error": "openapi fetch failed", "exception": str(e)}))
    spec = {"paths": {}}
    paths = []

# Try seeded superadmin variants to get a token
creds = [
    ("test.superadmin@fras.com", "password123"),
    ("superadmin@fras.com", "super123"),
]

def try_login(email, password):
    login_url = f"{BASE_URL}/api/login"
    try:
        r = session.post(login_url, json={"email": email, "password": password}, timeout=5)
        return {"status": r.status_code, "ok": r.ok, "text": r.text}
    except Exception as e:
        return {"error": str(e)}

for email, pwd in creds:
    res = try_login(email, pwd)
    results["login"] = {"email": email, "result": res}
    if isinstance(res, dict) and res.get("status") in (200, 201):
        try:
            token = session.post(f"{BASE_URL}/api/login", json={"email": email, "password": pwd}, timeout=5).json().get("access_token")
            if token:
                session.headers.update({"Authorization": f"Bearer {token}"})
                results["login"]["token_obtained"] = True
                break
        except Exception:
            pass

# For each path, attempt GET if it has no path params
for p in paths:
    methods = spec.get("paths", {}).get(p, {})
    # skip paths with path params
    if "{" in p:
        continue
    if "get" in methods:
        url = BASE_URL + p
        try:
            # try without auth first
            r = requests.get(url, timeout=5)
            results["paths"][p] = {"status": r.status_code, "ok": r.ok, "auth_used": False}
            # if 401/403 and we have auth headers, retry with session headers
            if r.status_code in (401, 403) and session.headers.get("Authorization"):
                r2 = session.get(url, timeout=5)
                results["paths"][p]["status_with_auth"] = r2.status_code
        except Exception as e:
            results["paths"][p] = {"error": str(e)}

# Print concise summary
print(json.dumps({"openapi": results["openapi"], "login": results["login"], "sample_paths_count": len(results["paths"])}, indent=2))
# Also write full details to a file
with open("tools/smoke_test_results.json", "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=2)

print("Detailed results written to tools/smoke_test_results.json")
