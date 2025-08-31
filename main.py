from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from api.attendance import router as attendance_router
from api.registration import router as registration_router
from api.recognition import router as recognition_router
from api.room import router as room_router
from api.capture import router as capture_router
from api.schedule import router as schedule_router
from api.debug import router as debug_router
from api.course_students import router as course_students_router
from api.student_courses import router as student_courses_router
from api.room_search import router as room_search_router


# Tag metadata for grouping in Swagger UI
tags_metadata = [
    {"name": "Rooms", "description": "Room listing and related endpoints."},
    {"name": "Courses", "description": "Course listing and related endpoints."},
    {"name": "Sections", "description": "Section listing and related endpoints."},
    {"name": "Attendance", "description": "Attendance retrieval and management."},
    {"name": "Registration", "description": "Student registration and management."},
    {"name": "Recognition", "description": "Face recognition endpoints."},
    {"name": "Capture", "description": "Image capture endpoints."},
    {"name": "Schedule", "description": "Room schedule management endpoints."},
    {"name": "Debug", "description": "Debug and utility endpoints."},
]

app = FastAPI(openapi_tags=tags_metadata)

# Add CORS middleware to allow requests from Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(schedule_router, tags=["Schedule"])
app.include_router(attendance_router, tags=["Attendance"])
app.include_router(registration_router, tags=["Registration"])
app.include_router(recognition_router, tags=["Recognition"])
app.include_router(room_router, tags=["Rooms", "Courses", "Sections"])
app.include_router(capture_router, tags=["Capture"])
app.include_router(debug_router, tags=["Debug"])
app.include_router(course_students_router, tags=["Registration"])
app.include_router(student_courses_router, tags=["Registration"])
app.include_router(room_search_router, tags=["Rooms", "Courses", "Sections"])