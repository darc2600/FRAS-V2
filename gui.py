import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import os
import sqlite3
from services.db import get_connection
from datetime import datetime
from deepface import DeepFace
from services.settings_service import get_settings_service

# Initialize database
def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            course_code TEXT,
            section TEXT,
            timestamp TEXT
        )
    ''')
        # commit handled by connection wrapper

# Attendance monitoring logic
def start_attendance(course_code, section):
    dataset_path = os.path.join("dataset", course_code, section)
    if not os.path.exists(dataset_path):
        messagebox.showerror("Error", f"Dataset path not found: {dataset_path}")
        return

    with get_connection() as conn:
        cursor = conn.cursor()

    student_faces = {}
    for student_id in os.listdir(dataset_path):
        student_folder = os.path.join(dataset_path, student_id)
        if os.path.isdir(student_folder):
            images = [os.path.join(student_folder, img) for img in os.listdir(student_folder) if img.endswith(".jpg")]
            if images:
                student_faces[student_id] = images[0]

    cap = cv2.VideoCapture(0)
    messagebox.showinfo("Info", "Press 'q' in the webcam window to stop attendance monitoring.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imwrite("current_frame.jpg", frame)

        # Get settings for face recognition
        settings = get_settings_service()

        for student_id, img_path in student_faces.items():
            try:
                result = DeepFace.verify(
                    img1_path="current_frame.jpg",
                    img2_path=img_path,
                    model_name=settings.face_recognition_model,
                    enforce_detection=settings.face_detection_confidence > 0.5,
                    threshold=settings.recognition_threshold
                )
                if result["verified"]:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        INSERT INTO attendance (student_id, course_code, section, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, (student_id, course_code, section, timestamp))
                    # commit handled by context manager
                    print(f"Attendance recorded for {student_id} at {timestamp}")
                    break
            except Exception as e:
                print(f"Error verifying {student_id}: {e}")

        cv2.imshow("Attendance Monitoring", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    # connection closed by context manager

# GUI setup
init_db()
root = tk.Tk()
root.title("Facial Recognition Attendance System")
root.geometry("400x200")

# Course code input
tk.Label(root, text="Course Code:").pack(pady=5)
course_entry = ttk.Entry(root)
course_entry.pack(pady=5)

# Section input
tk.Label(root, text="Section:").pack(pady=5)
section_entry = ttk.Entry(root)
section_entry.pack(pady=5)

# Start button
start_button = ttk.Button(root, text="Start Attendance", command=lambda: start_attendance(course_entry.get(), section_entry.get()))
start_button.pack(pady=20)

root.mainloop()
