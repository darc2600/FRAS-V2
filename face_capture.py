import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import os

# Function to capture face images
def capture_faces(course_code, section, student_id):
    save_path = os.path.join("dataset", course_code, section, student_id)
    os.makedirs(save_path, exist_ok=True)

    cap = cv2.VideoCapture(0)
    count = 0
    max_images = 10

    messagebox.showinfo("Info", f"Capturing {max_images} images. Press 'q' to quit early.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        count += 1
        img_name = os.path.join(save_path, f"img{count}.jpg")
        cv2.imwrite(img_name, frame)
        cv2.imshow("Capturing Faces", frame)

        if count >= max_images:
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    messagebox.showinfo("Done", f"Captured {count} images for {student_id} in {course_code}/{section}.")

# GUI setup
root = tk.Tk()
root.title("Face Capture Tool")
root.geometry("400x250")

# Course code input
tk.Label(root, text="Course Code:").pack(pady=5)
course_entry = ttk.Entry(root)
course_entry.pack(pady=5)

# Section input
tk.Label(root, text="Section:").pack(pady=5)
section_entry = ttk.Entry(root)
section_entry.pack(pady=5)

# Student ID input
tk.Label(root, text="Student ID:").pack(pady=5)
student_entry = ttk.Entry(root)
student_entry.pack(pady=5)

# Capture button
capture_button = ttk.Button(
    root,
    text="Capture Faces",
    command=lambda: capture_faces(course_entry.get(), section_entry.get(), student_entry.get())
)
capture_button.pack(pady=20)

root.mainloop()
