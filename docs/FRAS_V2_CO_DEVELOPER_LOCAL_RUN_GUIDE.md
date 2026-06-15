# FRAS V2 Co-Developer Local Run Guide

This guide explains how to run FRAS V2 cleanly on a local Windows machine.

Use this when setting up a co-developer laptop, preparing a clean demo, or fixing login/database confusion.

## 1. What This Setup Runs

FRAS V2 has three main parts:

1. PostgreSQL database
2. Python/FastAPI backend
3. Angular frontend

For local development:

- Backend runs on `http://127.0.0.1:8000`
- Frontend runs on `http://localhost:4200`
- PostgreSQL runs locally on port `5432`

## 2. Required Software

Install these first:

1. PostgreSQL Server
2. PostgreSQL Command Line Tools
3. pgAdmin 4, optional but helpful
4. Python 3.11
5. Node.js 20 or newer
6. Git, if cloning from repository
7. Chrome or Edge browser

Optional for camera testing:

1. A better external webcam
2. A phone-as-webcam app and matching desktop driver

## 3. Project Folder

The project should be opened from the FRAS root folder.

Example:

```powershell
cd C:\Users\<YOUR_NAME>\Downloads\facial_attendance_system\FRAS
```

All backend/database commands in this guide should be run from this root folder.

## 4. Create The PostgreSQL Database

Open pgAdmin or PSQL and create the V2 database:

```sql
CREATE DATABASE fras_v2;
```

Recommended local connection:

```text
Host: localhost
Port: 5432
Database: fras_v2
User: postgres
Password: your local PostgreSQL password
```

Important: remember the PostgreSQL password. It will be used in `DATABASE_URL`.

## 5. Password URL Encoding

If the PostgreSQL password has special characters, encode them in the connection URL.

Common examples:

```text
% becomes %25
@ becomes %40
# becomes %23
space becomes %20
```

Example:

```text
Raw password:
X4EE%MKja%xd%B7W

Encoded password:
X4EE%25MKja%25xd%25B7W
```

## 6. Prepare Python Environment

If `.venv` already exists, skip to the next section.

If `.venv` does not exist, create it:

```powershell
cd C:\Users\<YOUR_NAME>\Downloads\facial_attendance_system\FRAS

py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If Python 3.11 is not available through `py -3.11`, install Python 3.11 first.

## 7. Prepare Angular Frontend

Run this once:

```powershell
cd C:\Users\<YOUR_NAME>\Downloads\facial_attendance_system\FRAS\facial-attendance
npm install
```

After installing packages, return to the FRAS root folder:

```powershell
cd C:\Users\<YOUR_NAME>\Downloads\facial_attendance_system\FRAS
```

## 8. Set Local Environment Variables

In the PowerShell window where backend/database commands will run:

```powershell
cd C:\Users\<YOUR_NAME>\Downloads\facial_attendance_system\FRAS

$env:DATABASE_URL="postgresql://postgres:<ENCODED_POSTGRES_PASSWORD>@localhost:5432/fras_v2"
$env:FRAS_MODE="v2"
$env:DATASET_PATH="dataset"
```

Example:

```powershell
$env:DATABASE_URL="postgresql://postgres:X4EE%25MKja%25xd%25B7W@localhost:5432/fras_v2"
```

Use the real local PostgreSQL password for that machine.

## 9. Clean Database Reset

Use this only when a clean local database is needed.

This deletes and recreates the V2 tables:

```powershell
.\.venv\Scripts\python.exe database\init_v2_database.py --force
```

Important: `--force` is destructive. It resets V2 database tables.

## 10. Seed Professors, Schedules, Students, And Enrollments

Use the faculty load document:

```powershell
.\.venv\Scripts\python.exe database\seed_v2_integration_data.py --docx "<FULL_PATH_TO_FRAS-prof-database.docx>" --enroll-all-active-classes
```

Example:

```powershell
.\.venv\Scripts\python.exe database\seed_v2_integration_data.py --docx "C:\Users\<YOUR_NAME>\Downloads\FRAS REVISIONS\FRAS-prof-database.docx" --enroll-all-active-classes
```

This creates or updates:

1. Professor user accounts
2. Professor profiles
3. Courses
4. Rooms
5. Classes and schedules
6. 40 sample students
7. Enrollments
8. Special test professor account

## 11. Seed Saved Face Profiles

If saved face images exist under:

```text
dataset\v2_face_profiles\<student_number>\active\front.jpg
```

then restore face profiles and embeddings:

```powershell
.\.venv\Scripts\python.exe database\seed_v2_face_profiles_from_images.py
```

Notes:

1. `2025103037` is expected to remain unregistered if its image was removed for tester registration.
2. `2025103053`, `2025103056`, and `2025103069` are skipped by default because they were marked as problematic and should be retaken manually.
3. The script may print TensorFlow warnings. These are normal.
4. The first run may be slow because DeepFace loads the face model.

## 12. Verify The Seed

Run:

```powershell
.\.venv\Scripts\python.exe database\verify_v2_integration_seed.py
```

Expected result:

1. Database connection works.
2. Professors exist.
3. Classes exist.
4. Students exist.
5. Enrollments exist.
6. Test professor login works.

Also useful:

```powershell
.\.venv\Scripts\python.exe database\check_v2_seed.py
.\.venv\Scripts\python.exe database\check_v2_roster_counts.py
```

## 13. Run The Backend

Important: use `uvicorn`, not `python backend.py`.

Correct backend command:

```powershell
cd C:\Users\<YOUR_NAME>\Downloads\facial_attendance_system\FRAS

$env:DATABASE_URL="postgresql://postgres:<ENCODED_POSTGRES_PASSWORD>@localhost:5432/fras_v2"
$env:FRAS_MODE="v2"
$env:DATASET_PATH="dataset"

.\.venv\Scripts\python.exe -m uvicorn backend:app --reload --host 127.0.0.1 --port 8000
```

The backend should stay running.

If the command returns to the PowerShell prompt immediately, the server is not running.

## 14. Run The Frontend

Open a second PowerShell window:

```powershell
cd C:\Users\<YOUR_NAME>\Downloads\facial_attendance_system\FRAS\facial-attendance
npm start
```

Open the browser:

```text
http://localhost:4200
```

The frontend proxy sends `/api` requests to:

```text
http://127.0.0.1:8000
```

So the backend must be running before logging in.

## 15. Test Accounts

Use these development-only accounts:

| Account | Email | Password |
| --- | --- | --- |
| Test professor | `test.professor@fras.local` | `password123` |
| Faculty-load professors | generated from professor names | `password` |

To list or verify generated professor accounts:

```powershell
.\.venv\Scripts\python.exe database\verify_v2_integration_seed.py
```

## 16. Quick Login Test Without Frontend

Use this to confirm the backend login works:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/login" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"email":"test.professor@fras.local","password":"password123"}'
```

If this works, the backend and database login are correct.

If this returns `401 Unauthorized`, check:

1. Wrong password
2. Backend connected to wrong database
3. Database was not seeded
4. `DATABASE_URL` uses the wrong PostgreSQL user/password

## 17. Phone As Webcam

If the laptop webcam is low quality, use a phone as the webcam.

General steps:

1. Install a phone-as-webcam app on the phone.
2. Install the matching desktop driver/app on Windows.
3. Connect the phone through USB or the same Wi-Fi network.
4. Open the phone webcam app.
5. Open FRAS in Chrome or Edge.
6. In browser camera permissions, select the phone webcam as the camera source.
7. Test the camera on the Face Profile Registration page.

Camera tips:

1. Use good lighting.
2. Keep only one face in frame during registration.
3. Keep the face centered.
4. Avoid motion blur.
5. Avoid strong backlight.
6. Clean the phone camera lens.

## 18. Common Problems And Fixes

### Problem: `401 Unauthorized` on login

Cause:

- Wrong credentials, wrong database, or seed not applied.

Fix:

```powershell
$env:DATABASE_URL="postgresql://postgres:<ENCODED_POSTGRES_PASSWORD>@localhost:5432/fras_v2"
.\.venv\Scripts\python.exe database\verify_v2_integration_seed.py
```

Then use:

```text
test.professor@fras.local
password123
```

### Problem: Backend command exits immediately

Cause:

- Running `python backend.py` only loads the app. It does not start the server.

Fix:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend:app --reload --host 127.0.0.1 --port 8000
```

### Problem: Frontend says no face profile

Cause:

- Saved image files exist, but `student_face_profiles` rows are missing in the database being used.

Fix:

```powershell
.\.venv\Scripts\python.exe database\seed_v2_face_profiles_from_images.py
```

### Problem: Camera does not show

Fix:

1. Allow camera permission in the browser.
2. Close other apps using the webcam.
3. Refresh the page.
4. Select the correct webcam.
5. Try a phone-as-webcam setup.

### Problem: Face registration keeps failing

Fix:

1. Improve lighting.
2. Keep only one face visible.
3. Move closer to the camera.
4. Keep the face centered.
5. Retake the image.
6. Use a better webcam or phone camera.

### Problem: TensorFlow warnings appear

This is normal.

Examples:

```text
oneDNN custom operations are on
tf.losses.sparse_softmax_cross_entropy is deprecated
```

These warnings do not mean FRAS failed.

## 19. Clean Local Run Command Summary

Run from FRAS root:

```powershell
cd C:\Users\<YOUR_NAME>\Downloads\facial_attendance_system\FRAS

$env:DATABASE_URL="postgresql://postgres:<ENCODED_POSTGRES_PASSWORD>@localhost:5432/fras_v2"
$env:FRAS_MODE="v2"
$env:DATASET_PATH="dataset"

.\.venv\Scripts\python.exe database\init_v2_database.py --force
.\.venv\Scripts\python.exe database\seed_v2_integration_data.py --docx "<FULL_PATH_TO_FRAS-prof-database.docx>" --enroll-all-active-classes
.\.venv\Scripts\python.exe database\seed_v2_face_profiles_from_images.py
.\.venv\Scripts\python.exe database\verify_v2_integration_seed.py
.\.venv\Scripts\python.exe -m uvicorn backend:app --reload --host 127.0.0.1 --port 8000
```

Run frontend in another PowerShell window:

```powershell
cd C:\Users\<YOUR_NAME>\Downloads\facial_attendance_system\FRAS\facial-attendance
npm start
```

Open:

```text
http://localhost:4200
```

## 20. Important Reminder

Do not run destructive reset commands unless a clean database is intentionally needed.

Destructive command:

```powershell
.\.venv\Scripts\python.exe database\init_v2_database.py --force
```

This resets V2 tables and removes database records, including face profile rows.

Saved image files under `dataset\v2_face_profiles` are separate from database rows and can be used to reseed face profiles when available.
