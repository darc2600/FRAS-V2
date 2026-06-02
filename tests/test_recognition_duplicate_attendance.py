import sqlite3
from datetime import datetime, timedelta
from types import SimpleNamespace

from repositories.recognition_repo import MANILA_TZ, RecognitionRepository


def test_same_student_cannot_mark_attendance_twice_for_same_class_today():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE classes (
            class_id INTEGER PRIMARY KEY,
            day_of_week TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        );
        CREATE TABLE attendance_status_types (
            status_id INTEGER PRIMARY KEY,
            status_name TEXT NOT NULL
        );
        CREATE TABLE students (
            student_id INTEGER PRIMARY KEY,
            last_name TEXT NOT NULL
        );
        CREATE TABLE attendance_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            class_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            status_id INTEGER NOT NULL,
            notes TEXT
        );
        """
    )

    now = datetime.now(MANILA_TZ)
    cursor.execute(
        "INSERT INTO classes (class_id, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?)",
        (
            10,
            now.strftime("%A"),
            (now - timedelta(minutes=20)).strftime("%H:%M"),
            (now + timedelta(minutes=30)).strftime("%H:%M"),
        ),
    )
    cursor.execute("INSERT INTO attendance_status_types (status_id, status_name) VALUES (?, ?)", (1, "Present"))
    cursor.execute("INSERT INTO attendance_status_types (status_id, status_name) VALUES (?, ?)", (2, "Late"))
    cursor.execute("INSERT INTO students (student_id, last_name) VALUES (?, ?)", (25, "Davis"))
    cursor.execute(
        """
        INSERT INTO attendance_logs (student_id, class_id, timestamp, status_id, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            25,
            10,
            (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
            1,
            "Existing attendance",
        ),
    )
    conn.commit()

    repo = RecognitionRepository()
    repo.settings = SimpleNamespace(late_threshold_minutes=15, absent_threshold_minutes=30)

    response = repo._build_attendance_response(cursor, conn, student_id=25, class_id=10)

    assert response.status == "success"
    assert response.attendance_recorded is False
    assert response.message == "Attendance already marked for Davis."

    cursor.execute("SELECT COUNT(*) FROM attendance_logs WHERE student_id = ? AND class_id = ?", (25, 10))
    assert cursor.fetchone()[0] == 1
