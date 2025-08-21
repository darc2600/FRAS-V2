import cv2
import os
import sqlite3
from datetime import datetime
from deepface import DeepFace

# Configuration
course_code = "IT164L"
section = "AM4"
dataset_path = os.path.join("dataset", course_code, section)
db_path = "attendance.db"

# Initialize database
conn = sqlite3.connect(db_path)
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
conn.commit()

# Load student images
student_faces = {}
for student_id in os.listdir(dataset_path):
    student_folder = os.path.join(dataset_path, student_id)
    if os.path.isdir(student_folder):
        images = [os.path.join(student_folder, img) for img in os.listdir(student_folder) if img.lower().endswith(".jpg")]
        if images:
            student_faces[student_id] = images[0]  # Use the first image for recognition

# Start webcam
cap = cv2.VideoCapture(0)
print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Save current frame temporarily
    cv2.imwrite("current_frame.jpg", frame)

    # Try to match with known student faces
    for student_id, img_path in student_faces.items():
        try:
            result = DeepFace.verify(img1_path="current_frame.jpg", img2_path=img_path, model_name="ArcFace", enforce_detection=False)
            if result["verified"]:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO attendance (student_id, course_code, section, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (student_id, course_code, section, timestamp))
                conn.commit()
                print(f"Attendance recorded for {student_id} at {timestamp}")
                break  # Stop checking after first match
        except Exception as e:
            print(f"Error verifying {student_id}: {e}")

    # Display the frame
    cv2.imshow("Attendance Monitoring", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
conn.close()
print("Attendance monitoring stopped.")