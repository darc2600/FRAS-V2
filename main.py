from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.attendance import router as attendance_router
from api.registration import router as registration_router
from api.recognition import router as recognition_router
from api.room import router as room_router
from api.capture import router as capture_router
from api.schedule import router as schedule_router
from api.debug import router as debug_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(attendance_router)
app.include_router(registration_router)
app.include_router(recognition_router)
app.include_router(room_router)
app.include_router(capture_router)
app.include_router(schedule_router)
app.include_router(debug_router)