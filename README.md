# Facial Attendance System

This project implements a facial attendance system that utilizes facial recognition technology to automate the process of taking attendance for students. The system captures images of students' faces and records their attendance in an SQLite database.

## Project Structure

```
facial_attendance_system/
├── dataset/               # Stores student face images
│   ├── 2023001/           # Example student folder
│   │   ├── img1.jpg
│   │   └── img2.jpg
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

## License

This project is licensed under the MIT License. See the LICENSE file for more details.