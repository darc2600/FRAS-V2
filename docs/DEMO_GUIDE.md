# FRAS Demo Guide

This guide is for preparing a clean FRAS demo before a thesis panel review or project presentation.

## 1. Reset the demo database

From the project root, run:

```bash
python scripts/reset_demo_data.py
```

The script creates a backup first, then seeds a clean presentation-ready dataset.

## 2. Demo accounts

All demo accounts use this password:

```txt
DemoPass123!
```

| Role | Email | Suggested demo use |
|---|---|---|
| Super Admin | superadmin@fras.demo | Full admin walkthrough, analytics, user management |
| IT Admin | itadmin@fras.demo | User support, user management, tickets |
| Instructor | elena.garcia@fras.demo | Instructor flow, attendance checking |
| Instructor | marco.delacruz@fras.demo | Secondary instructor account |

## 3. Suggested demo flow

```txt
1. Start at the redesigned login page.
2. Login as Super Admin.
3. Open User Management and show default user list.
4. Show the filter button and filtered search behavior.
5. Open System Analytics and show monthly charts.
6. Explain Face Registration Completion using the new user-friendly labels.
7. Open Attendance Reports and generate a Class Report.
8. Export report as CSV/Excel/PDF if needed.
9. Open Add/Edit Schedule and show that duplicate rooms are now protected.
10. Open Contact Support and show category/priority placeholders.
```

## 4. Demo data highlights

The seeded database includes:

```txt
120 students
4 instructors
6 rooms
6 classes
attendance logs across January to December
face registration coverage data
support tickets with different statuses and priorities
```

## 5. Before presenting

Run this checklist:

```txt
Backend starts without error
Frontend loads without console-breaking errors
Login works with demo accounts
Analytics page has charts/data
Attendance Reports can generate a class report
Room schedule page loads correctly
Support form loads category and priority placeholders
```

## 6. Important security reminder

Demo accounts are for local/demo use only. Do not use the demo password in production.
