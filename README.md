# Facial Attendance System

This project implements a facial attendance system that utilizes facial recognition technology to automate the process of taking attendance for students. The system captures images of students' faces and records their attendance in an SQLite database.

## Project Structure

```
facial_attendance_system/
├── dataset/
└── IT164L/
    ├── AM4/
    │   ├── 2019123456/
    │   │   ├── img1.jpg
    │   │   └── img2.jpg
    │   ├── 2024123456/
    ├── AM5/
    │   ├── 2019123456/
    │   └── 2024123456/
    └── BM4/
        ├── 2019123456/
        └── 2024123456/
├── attendance.db          # SQLite database file (auto-created)
├── main.py                # Main script
├── utils.py               # Helper functions
└── README.md              # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd facial_attendance_system
   ```

2. **Install required packages:**
   Ensure you have Python installed, then install the necessary libraries:
   ```
   pip install -r requirements.txt
   ```

3. **Prepare the dataset:**
   Place student images in the `dataset/` directory, organized by student ID.

## Usage Guidelines

1. **Run the main script:**
   Execute the main script to start the attendance system:
   ```
   python main.py
   ```

2. **Attendance Recording:**
   The system will automatically recognize faces and update the attendance records in the `attendance.db` database.

## Additional Information

- The `utils.py` file contains helper functions for image processing and database interactions.
- The `attendance.db` file will be created automatically when the application is run for the first time.

**## DEPENDENCIES**
1. Python 3.10
Download from python.org

2. Required Python Packages
Install these using pip (in your project or virtual environment):
pip install opencv-python
pip install numpy
pip install deepface
pip install tf-keras
pip install pillow

opencv-python: For webcam and image processing.
numpy: Required by OpenCV and DeepFace.
deepface: For facial recognition.
tf-keras: Required for DeepFace (with TensorFlow 2.20+).
pillow: For image handling in Tkinter GUIs.

opencv-python: For webcam and image processing.
numpy: Required by OpenCV and DeepFace.
deepface: For facial recognition.
tf-keras: Required for DeepFace (with TensorFlow 2.20+).
pillow: For image handling in Tkinter GUIs.

3. TensorFlow (compatible version)
DeepFace works best with TensorFlow 2.10 or 2.11.
Recommended:
pip install tensorflow==2.10.0
or
pip install tensorflow==2.11.0

4. (Optional) SQLite Browser
For viewing your attendance.db database: DB Browser for SQLite

5. (Optional) Tkinter
Tkinter is included with standard Python installations on Windows.
If you get an error, install with:
pip install tk

**Summary of Commands**
pip install opencv-python numpy deepface tf-keras pillow tensorflow==2.10.0

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
