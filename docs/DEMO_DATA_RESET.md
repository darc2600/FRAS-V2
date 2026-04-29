# Demo Data Reset Workflow

This document explains how to rebuild a clean FRAS demo database for thesis panel reviews, local testing, and presentation rehearsals.

## Purpose

The project previously had demo data that could be lost, changed, or duplicated during deployment/testing. The reset workflow gives the team a repeatable way to restore a clean database with realistic records.

## New script

```bash
python scripts/reset_demo_data.py
```

By default, the script uses:

```txt
attendance.db
```

It creates a timestamped backup before modifying the database:

```txt
backups/attendance_before_demo_reset_YYYYMMDD_HHMMSS.db
```

## Demo accounts

All seeded demo accounts use this password:

```txt
DemoPass123!
```

| Role | Email |
|---|---|
| Super Admin | superadmin@fras.demo |
| IT Admin | itadmin@fras.demo |
| Instructor | elena.garcia@fras.demo |
| Instructor | marco.delacruz@fras.demo |

## Seeded data

The reset script seeds:

```txt
Departments
Students
Instructors
Super Admin and IT Admin users
Rooms
Buildings
Courses
School terms
Classes
Enrollments
Attendance logs across January to December
Student face registration coverage
Support tickets
Permissions
Role permissions
System settings
```

## Expected demo data shape

After running the script, the database should contain approximately:

```txt
120 students
4 instructors
6 rooms
6 classes
100+ enrollments
monthly attendance logs
90+ face-registered students
4 support tickets
```

## Recommended local reset steps

From the project root:

```bash
python scripts/reset_demo_data.py
```

Then restart the backend:

```bash
uvicorn backend:app --reload --host 127.0.0.1 --port 8000
```

Then restart the frontend if needed:

```bash
cd facial-attendance
npm run start
```

## Reset without backup

Only use this if you are sure you do not need the current database:

```bash
python scripts/reset_demo_data.py --no-backup
```

## Reset a different database path

```bash
python scripts/reset_demo_data.py --db path/to/attendance.db
```

## Demo validation checklist

After running the reset script, check these pages:

```txt
1. Login page
2. User Management
3. Room Schedule / Add Edit Schedule
4. Attendance Reports
5. System Analytics
6. Contact Support
```

The analytics page should now have enough monthly data to show meaningful charts.

## Git note

Do not commit real local database backups. The `.gitignore` should keep backup files out of version control.
