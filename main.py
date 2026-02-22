import os
import cv2
import sqlite3
import numpy as np
from utils import create_database, add_attendance_record, load_images, recognize_face

def main():
    # Create the SQLite database and attendance table
    create_database('attendance.db')

    # Load images and their corresponding labels
    images, labels = load_images('dataset')

    # Initialize the face recognizer
    face_recognizer = cv2.face.LBPHFaceRecognizer_create()
    face_recognizer.train(images, np.array(labels))

    # Start video capture
    video_capture = cv2.VideoCapture(0)

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        # Recognize face in the frame
        student_id, confidence = recognize_face(frame, face_recognizer)

        if confidence < 100:  # Confidence threshold
            # Add attendance record for recognized student
            add_attendance_record('attendance.db', student_id)

        # Display the resulting frame
        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture and close windows
    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()