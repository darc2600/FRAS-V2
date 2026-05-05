import requests
import json
import re
from collections import defaultdict

BASE_URL = "http://127.0.0.1:8000"
OPENAPI = f"{BASE_URL}/openapi.json"

session = requests.Session()
results = {"openapi": None, "login": None, "endpoints": {}}

# Helper to try login and set auth header
def obtain_token():
    creds = [("test.superadmin@fras.com", "password123"), ("superadmin@fras.com", "super123")]
    for email, pwd in creds:
        try:
            r = session.post(f"{BASE_URL}/api/login", json={"email": email, "password": pwd}, timeout=5)
            if r.status_code in (200, 201):
                try:
                    token = r.json().get("access_token")
                except Exception:
                    token = None
                if token:
                    session.headers.update({"Authorization": f"Bearer {token}"})
                    results["login"] = {"email": email, "status": r.status_code}
                    return True
                else:
                    results["login"] = {"email": email, "status": r.status_code, "note": "no token in response"}
        except Exception as e:
            results["login"] = {"email": email, "error": str(e)}
    return False

# Fetch openapi
try:
    r = requests.get(OPENAPI, timeout=5)
    r.raise_for_status()
    spec = r.json()
    results["openapi"] = {"status": r.status_code, "title": spec.get("info", {}).get("title")}
except Exception as e:
    print(json.dumps({"error": "openapi fetch failed", "exception": str(e)}))
    spec = {"paths": {}}

paths = spec.get("paths", {})

# Discover collection endpoints to pull IDs
collection_samples = defaultdict(list)
for p, methods in paths.items():
    if "get" in methods and "{" not in p:
        url = BASE_URL + p
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                try:
                    body = r.json()
                except Exception:
                    body = None
                # If list, try to extract id keys from first item
                if isinstance(body, list) and len(body) > 0:
                    item = body[0]
                    if isinstance(item, dict):
                        for key in ("id","student_id","user_id","course_id","instructor_id","class_id","room_id"):
                            if key in item:
                                collection_samples[p].append(item[key])
                                break
                        else:
                            # pick any int-like key
                            for k, v in item.items():
                                if isinstance(v, int):
                                    collection_samples[p].append(v)
                                    break
                # If dict with items inside key 'data' etc, try extract
                if isinstance(body, dict):
                    for candidate in ("data","items","results"):
                        arr = body.get(candidate)
                        if isinstance(arr, list) and arr:
                            first = arr[0]
                            if isinstance(first, dict):
                                for key in ("id","student_id","user_id"):
                                    if key in first:
                                        collection_samples[p].append(first[key])
                                        break
        except Exception:
            pass

# Map of param name -> sample id, attempt naive mapping by path prefix
param_values = {}
for coll_path, ids in collection_samples.items():
    # derive resource name: /api/students -> students -> student_id
    m = re.match(r"/api/([^/]+)", coll_path)
    if m:
        res = m.group(1)
        key = res.rstrip('s') + "_id"
        if ids:
            param_values[key] = ids[0]

# Try to obtain token for authenticated endpoints
have_token = obtain_token()

# Now iterate over all paths & GET where possible
for p, methods in paths.items():
    results["endpoints"][p] = {}
    for mname, details in methods.items():
        mname_l = mname.lower()
        entry = {"method": mname_l}
        if mname_l == "get":
            # build concrete path if path params exist
            concrete = p
            params = re.findall(r"\{(.*?)\}", p)
            for param in params:
                val = param_values.get(param) or 1
                concrete = concrete.replace("{" + param + "}", str(val))
            url = BASE_URL + concrete
            try:
                # try unauthenticated first
                r = requests.get(url, timeout=5)
                entry.update({"status": r.status_code, "ok": r.ok})
                ct = r.headers.get("content-type","")
                entry["content_type"] = ct
                if r.status_code == 200:
                    # summarize body
                    try:
                        body = r.json()
                        if isinstance(body, list):
                            entry["items"] = len(body)
                        elif isinstance(body, dict):
                            entry["keys"] = list(body.keys())[:6]
                    except Exception:
                        entry["text_snippet"] = r.text[:200]
                # if need auth and we have token, retry
                if r.status_code in (401,403) and have_token:
                    r2 = session.get(url, timeout=5)
                    entry["status_with_auth"] = r2.status_code
                    if r2.status_code == 200:
                        try:
                            b2 = r2.json()
                            if isinstance(b2, list):
                                entry["items_with_auth"] = len(b2)
                        except Exception:
                            entry["text_snippet_with_auth"] = r2.text[:200]
            except Exception as e:
                entry["error"] = str(e)
        else:
            entry["skipped"] = "non-GET method - skip in this run"
        results["endpoints"][p][mname_l] = entry

# Summarize
summary = {"total_paths": len(paths), "tested_gets": sum(1 for p in results["endpoints"].values() if "get" in p), "have_token": have_token}
print(json.dumps({"summary": summary}, indent=2))
with open("tools/smoke_test_extended_results.json", "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=2)
print("Wrote tools/smoke_test_extended_results.json")
