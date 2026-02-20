#!/usr/bin/env python3
"""
Seed system settings with default values for FRAS
"""

import sqlite3
import os

DB_PATH = "attendance.db"

def seed_system_settings():
    """Insert default system settings"""

    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Default system settings with appropriate types and values
        default_settings = [
            # Attendance settings
            ('absent_threshold_minutes', '15', 'number'),
            ('late_threshold_minutes', '10', 'number'),
            ('attendance_grace_period_minutes', '5', 'number'),
            ('auto_absent_delay_hours', '2', 'number'),
            ('duplicate_prevention_window_minutes', '5', 'number'),
            ('allow_makeup_attendance', 'true', 'boolean'),
            ('makeup_deadline_hours', '24', 'number'),

            # Recognition settings
            ('recognition_threshold', '0.8', 'number'),
            ('min_face_confidence', '0.5', 'number'),
            ('face_detection_model', 'opencv', 'text'),
            ('max_recognition_attempts', '3', 'number'),
            ('image_compression_quality', '85', 'number'),
            ('image_max_size', '1024', 'number'),

            # Automation settings
            ('auto_absent_enabled', 'true', 'boolean'),

            # System settings
            ('system_name', 'FRAS - Facial Recognition Attendance System', 'text'),
            ('theme_primary_color', '#007bff', 'text'),
            ('theme_secondary_color', '#6c757d', 'text'),
            ('system_logo_url', '', 'text'),
            ('welcome_message', 'Welcome to FRAS', 'text'),
            ('user_guide', 'Please follow the attendance guidelines.', 'text'),
        ]

        # Insert or replace settings
        cursor.executemany("""
            INSERT OR REPLACE INTO system_settings (setting_key, setting_value, setting_type, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, default_settings)

        conn.commit()
        print(f"✅ Successfully seeded {len(default_settings)} system settings")

    except Exception as e:
        print(f"❌ Failed to seed system settings: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    seed_system_settings()