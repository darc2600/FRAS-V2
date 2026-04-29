"""
Database migration system for schema versioning
"""
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
import logging

LOG = logging.getLogger(__name__)

class Migration:
    """Represents a database migration"""

    def __init__(self, version: str, description: str, up_sql: str, down_sql: str = None):
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.applied_at = None

    def apply(self, cursor):
        """Apply the migration"""
        try:
            cursor.executescript(self.up_sql)
            cursor.execute(
                "INSERT INTO schema_migrations (version, description, applied_at) VALUES (?, ?, ?)",
                (self.version, self.description, datetime.now().isoformat())
            )
            LOG.info(f"Applied migration {self.version}: {self.description}")
        except Exception as e:
            LOG.error(f"Failed to apply migration {self.version}: {e}")
            raise

    def rollback(self, cursor):
        """Rollback the migration"""
        if not self.down_sql:
            raise Exception(f"No rollback SQL provided for migration {self.version}")

        try:
            cursor.executescript(self.down_sql)
            cursor.execute("DELETE FROM schema_migrations WHERE version = ?", (self.version,))
            LOG.info(f"Rolled back migration {self.version}")
        except Exception as e:
            LOG.error(f"Failed to rollback migration {self.version}: {e}")
            raise

class MigrationManager:
    """Manages database migrations"""

    def __init__(self, db_path: str = "attendance.db"):
        self.db_path = db_path
        self.migrations: Dict[str, Migration] = {}
        self._ensure_migration_table()

    def _ensure_migration_table(self):
        """Create migrations table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
            ''')
            conn.commit()

    def add_migration(self, migration: Migration):
        """Add a migration to the manager"""
        self.migrations[migration.version] = migration

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_migrations ORDER BY applied_at")
            return [row[0] for row in cursor.fetchall()]

    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that haven't been applied yet"""
        applied = set(self.get_applied_migrations())
        return [m for m in self.migrations.values() if m.version not in applied]

    def migrate(self):
        """Apply all pending migrations"""
        pending = self.get_pending_migrations()
        if not pending:
            LOG.info("No pending migrations")
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                for migration in pending:
                    LOG.info(f"Applying migration {migration.version}")
                    migration.apply(cursor)
                conn.commit()
                LOG.info(f"Successfully applied {len(pending)} migrations")
            except Exception as e:
                conn.rollback()
                LOG.error(f"Migration failed: {e}")
                raise

    def rollback(self, steps: int = 1):
        """Rollback the last N migrations"""
        applied = self.get_applied_migrations()
        if not applied:
            LOG.info("No migrations to rollback")
            return

        to_rollback = applied[-steps:]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                for version in reversed(to_rollback):
                    if version in self.migrations:
                        migration = self.migrations[version]
                        LOG.info(f"Rolling back migration {version}")
                        migration.rollback(cursor)
                    else:
                        LOG.warning(f"No rollback script for migration {version}")
                conn.commit()
                LOG.info(f"Successfully rolled back {len(to_rollback)} migrations")
            except Exception as e:
                conn.rollback()
                LOG.error(f"Rollback failed: {e}")
                raise

# Global migration manager
migration_manager = MigrationManager()

def create_initial_schema_migration():
    """Create the initial schema migration"""
    up_sql = '''
    -- Students table
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_number VARCHAR(20) UNIQUE NOT NULL,
        last_name TEXT NOT NULL,
        first_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        face_data_path TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Instructors table
    CREATE TABLE IF NOT EXISTS instructors (
        instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        instructor_number VARCHAR(20) UNIQUE NOT NULL,
        last_name TEXT NOT NULL,
        first_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        dept_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Courses table
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code VARCHAR(20) UNIQUE NOT NULL,
        course_name VARCHAR(100) NOT NULL,
        units INTEGER,
        dept_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Departments table
    CREATE TABLE IF NOT EXISTS departments (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_code VARCHAR(20) UNIQUE NOT NULL,
        dept_name TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Room types table
    CREATE TABLE IF NOT EXISTS room_types (
        room_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name VARCHAR(50) UNIQUE NOT NULL
    );

    -- Campuses table
    CREATE TABLE IF NOT EXISTS campuses (
        campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_name TEXT UNIQUE NOT NULL,
        location TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Buildings table
    CREATE TABLE IF NOT EXISTS buildings (
        building_id INTEGER PRIMARY KEY AUTOINCREMENT,
        building_name TEXT NOT NULL,
        campus_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(campus_id) REFERENCES campuses(campus_id),
        UNIQUE(building_name, campus_id)
    );

    -- Rooms table
    CREATE TABLE IF NOT EXISTS rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number VARCHAR(20) NOT NULL,
        floor_level INTEGER NOT NULL,
        campus_id INTEGER NOT NULL,
        building_id INTEGER NOT NULL,
        room_type_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(campus_id) REFERENCES campuses(campus_id),
        FOREIGN KEY(building_id) REFERENCES buildings(building_id),
        FOREIGN KEY(room_type_id) REFERENCES room_types(room_type_id),
        UNIQUE(campus_id, building_id, room_number)
    );

    -- School terms table
    CREATE TABLE IF NOT EXISTS school_terms (
        term_id INTEGER PRIMARY KEY AUTOINCREMENT,
        school_year VARCHAR(20) NOT NULL,
        term INTEGER NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL
    );

    -- Classes table
    CREATE TABLE IF NOT EXISTS classes (
        class_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        instructor_id INTEGER NOT NULL,
        section VARCHAR(10) NOT NULL,
        day_of_week VARCHAR(10) NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        term_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(course_id) REFERENCES courses(course_id),
        FOREIGN KEY(room_id) REFERENCES rooms(room_id),
        FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id),
        FOREIGN KEY(term_id) REFERENCES school_terms(term_id)
    );

    -- Enrollments table
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        class_id INTEGER NOT NULL,
        enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(class_id) REFERENCES classes(class_id),
        UNIQUE(student_id, class_id)
    );

    -- Attendance logs table
    CREATE TABLE IF NOT EXISTS attendance_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        class_id INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20) NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(class_id) REFERENCES classes(class_id)
    );
    '''

    migration = Migration(
        version="001_initial_schema",
        description="Create initial database schema with all tables and constraints",
        up_sql=up_sql
    )

    migration_manager.add_migration(migration)

def create_indexes_migration():
    """Create indexes migration"""
    up_sql = '''
    CREATE INDEX IF NOT EXISTS idx_students_number ON students(student_number);
    CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
    CREATE INDEX IF NOT EXISTS idx_enrollments_student_class ON enrollments(student_id, class_id);
    CREATE INDEX IF NOT EXISTS idx_classes_course_section ON classes(course_id, section);
    CREATE INDEX IF NOT EXISTS idx_classes_room_day_time ON classes(room_id, day_of_week, start_time);
    CREATE INDEX IF NOT EXISTS idx_attendance_logs_class_date ON attendance_logs(class_id, DATE(timestamp));
    CREATE INDEX IF NOT EXISTS idx_attendance_logs_student_date ON attendance_logs(student_id, DATE(timestamp));
    CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(course_code);
    CREATE INDEX IF NOT EXISTS idx_instructors_number ON instructors(instructor_number);
    '''

    migration = Migration(
        version="002_add_indexes",
        description="Add database indexes for performance optimization",
        up_sql=up_sql
    )

    migration_manager.add_migration(migration)

# Initialize migrations
create_initial_schema_migration()
create_indexes_migration()