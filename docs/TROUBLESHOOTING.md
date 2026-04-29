# FRAS Troubleshooting Guide

## Frontend says `ng` is not recognized

Run this inside the frontend folder:

```bash
cd facial-attendance
npm install
npm start
```

## Backend cannot start because a package is missing

Activate your Python virtual environment and install the required packages:

```bash
pip install fastapi uvicorn python-multipart pyjwt passlib bcrypt pydantic
```

## Login background image does not show after deployment

Confirm the image exists here:

```txt
facial-attendance/src/assets/mapua-bg2.jpg
```

Then rebuild the frontend:

```bash
cd facial-attendance
npm run build
```

## Database appears empty

Confirm the backend is using the expected database file:

```txt
attendance.db
```

If using `DATABASE_URL`, confirm it points to the correct database.

## Face images are missing

Confirm this folder exists and is writable:

```txt
dataset/
```

## Room schedule breaks after adding rooms

This is a known high-priority fix area. The next planned patch will normalize room numbers and prevent duplicate room records.

## Reports page looks incorrect

This is a planned polish area. The current branch has partial report improvements, but the report display will be cleaned in a dedicated patch.

## Analytics lacks graphs

This is planned for the analytics patch. Current analytics is card-based and will be upgraded with monthly and distribution charts.
