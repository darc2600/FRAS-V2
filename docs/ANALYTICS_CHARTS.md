# Analytics Charts and Face Registration Insights

This patch upgrades the System Analytics page from simple number cards into a clearer visual dashboard.

## What changed

- Added monthly student registration chart.
- Added monthly instructor registration chart.
- Added monthly attendance records chart.
- Added attendance status breakdown.
- Added top classes by attendance activity.
- Renamed technical face embedding labels into presentation-friendly wording.
- Added a face registration completion donut indicator.
- Added clearer helper text explaining what face registration readiness means.

## Backend endpoint updated

The existing endpoint was expanded:

```txt
GET /api/admin/analytics
```

It now returns:

```txt
total_students
total_instructors
total_attendance_records
recent_attendance
chart_year
monthly_student_registrations
monthly_instructor_registrations
monthly_attendance_records
attendance_status_distribution
top_classes_by_attendance
```

## Why this matters

The panel feedback specifically asked for analytics that show trends from January to December instead of only current total numbers.

This patch directly addresses that by making the analytics page more visual, easier to understand, and more useful for demo presentation.

## Test checklist

1. Login as Super Admin or an account with analytics permission.
2. Open System Analytics.
3. Confirm total cards still display.
4. Confirm monthly student registration chart appears.
5. Confirm monthly instructor registration chart appears.
6. Confirm monthly attendance chart appears.
7. Confirm attendance status breakdown appears.
8. Confirm face registration labels no longer mention "embedding coverage" or "missing all face data".
9. Confirm the page still loads when there is no data.
10. Confirm backend endpoint works:

```bash
curl http://127.0.0.1:8000/api/admin/analytics
```

If your endpoint requires authentication in your setup, test through the logged-in frontend instead.
