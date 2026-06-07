from __future__ import annotations

import argparse
import re
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, time
from pathlib import Path
from xml.etree import ElementTree as ET

import psycopg2

try:
    from database.init_v2_database import load_local_env
except ImportError:
    from init_v2_database import load_local_env


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DOCX_PATH = Path.home() / "Downloads" / "FRAS REVISIONS" / "FRAS-prof-database.docx"
DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
LOCAL_PROFESSOR_PASSWORD = "password"


@dataclass
class ProfessorLoad:
    document_index: int
    raw_name: str
    first_name: str
    last_name: str
    employment_status: str = ""
    total_units: int = 0
    lecture_units: int = 0
    lab_units: int = 0
    entries: list["ScheduleEntry"] = field(default_factory=list)


@dataclass
class ScheduleEntry:
    day_of_week: str
    start_time: time
    end_time: time
    course_code: str
    section: str
    room: str


def extract_docx_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))

    paragraphs = []
    for paragraph in root.findall(".//w:p", DOCX_NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", DOCX_NS)).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def parse_int_value(text: str) -> int:
    match = re.search(r"(-?\d+)", text or "")
    return int(match.group(1)) if match else 0


def parse_professor_name(raw_name: str) -> tuple[str, str]:
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", raw_name).strip()
    if "," not in cleaned:
        parts = cleaned.split()
        return (" ".join(parts[1:]) or "Professor", parts[0].title() if parts else "Unknown")

    last_name, first_name = cleaned.split(",", 1)
    return (first_name.strip().title() or "Professor", last_name.strip().title() or "Unknown")


def parse_time_range(value: str) -> tuple[time, time]:
    normalized = value.replace("–", "-").replace("—", "-")
    if "onwards" in normalized.lower():
        start_text = re.sub(r"\s*onwards\s*", "", normalized, flags=re.IGNORECASE).strip()
        return (
            datetime.strptime(start_text, "%I:%M %p").time(),
            datetime.strptime("09:00 PM", "%I:%M %p").time(),
        )
    start_text, end_text = [part.strip() for part in normalized.split("-", 1)]
    return (
        datetime.strptime(start_text, "%I:%M %p").time(),
        datetime.strptime(end_text, "%I:%M %p").time(),
    )


def parse_professor_loads(paragraphs: list[str]) -> list[ProfessorLoad]:
    loads: list[ProfessorLoad] = []
    current: ProfessorLoad | None = None
    current_day = ""
    skipped_time_rows = 0
    i = 0

    while i < len(paragraphs):
        line = paragraphs[i]
        professor_match = re.match(r"^(\d+)\.\s+(.+)$", line)
        if professor_match:
            first_name, last_name = parse_professor_name(professor_match.group(2))
            current = ProfessorLoad(
                document_index=int(professor_match.group(1)),
                raw_name=professor_match.group(2).strip(),
                first_name=first_name,
                last_name=last_name,
            )
            loads.append(current)
            current_day = ""
            i += 1
            continue

        if current and line.startswith("Employment Status:"):
            current.employment_status = line.split(":", 1)[1].strip()
            i += 1
            continue

        if current and line.startswith("Total Units:"):
            current.total_units = parse_int_value(line)
            i += 1
            continue

        if current and line.startswith("Lecture Units:"):
            current.lecture_units = parse_int_value(line)
            i += 1
            continue

        if current and line.startswith("Lab Units:"):
            current.lab_units = parse_int_value(line)
            i += 1
            continue

        if current and line in DAYS:
            current_day = line
            i += 1
            continue

        if current and current_day and line.startswith("Time:"):
            time_value = line.split(":", 1)[1].strip()
            course_line = paragraphs[i + 1] if i + 1 < len(paragraphs) else ""
            section_line = paragraphs[i + 2] if i + 2 < len(paragraphs) else ""
            room_line = paragraphs[i + 3] if i + 3 < len(paragraphs) else ""
            if not course_line.startswith("Course Code:"):
                i += 1
                continue

            try:
                start_time, end_time = parse_time_range(time_value)
            except ValueError:
                skipped_time_rows += 1
                i += 1
                continue
            current.entries.append(
                ScheduleEntry(
                    day_of_week=current_day,
                    start_time=start_time,
                    end_time=end_time,
                    course_code=course_line.split(":", 1)[1].strip(),
                    section=section_line.split(":", 1)[1].strip() if section_line.startswith("Section:") else "TBA",
                    room=room_line.split(":", 1)[1].strip() if room_line.startswith("Room:") else "TBA",
                )
            )
            i += 4
            continue

        i += 1

    if skipped_time_rows:
        print(f"Skipped {skipped_time_rows} malformed time row(s).")
    return loads


def ensure_professor_metadata_columns(cursor) -> None:
    columns = {
        "employment_status": "VARCHAR(100)",
        "total_units": "INT DEFAULT 0",
        "lecture_units": "INT DEFAULT 0",
        "lab_units": "INT DEFAULT 0",
    }
    for column, definition in columns.items():
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'professors'
              AND column_name = %s
            """,
            (column,),
        )
        if not cursor.fetchone():
            cursor.execute(f"ALTER TABLE professors ADD COLUMN {column} {definition}")


def slug_email(first_name: str, last_name: str, index: int) -> str:
    base = re.sub(r"[^a-z0-9]+", ".", f"{first_name}.{last_name}".lower()).strip(".")
    return f"{base or 'professor'}.{index:03d}@mapua.test"


def room_floor(room_number: str) -> int | None:
    match = re.search(r"MP0?(\d)", room_number or "")
    return int(match.group(1)) if match else None


def upsert_professor(cursor, load: ProfessorLoad) -> int:
    faculty_number = f"DOCX-{load.document_index:03d}"
    email = slug_email(load.first_name, load.last_name, load.document_index)
    cursor.execute(
        """
        INSERT INTO users (email, password_hash, role)
        VALUES (%s, %s, 'professor')
        ON CONFLICT (email) DO UPDATE
        SET password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role,
            updated_at = CURRENT_TIMESTAMP
        RETURNING user_id
        """,
        (email, LOCAL_PROFESSOR_PASSWORD),
    )
    user_id = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO professors (
            user_id, faculty_number, first_name, last_name, email,
            employment_status, total_units, lecture_units, lab_units
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (faculty_number) DO UPDATE
        SET first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            email = EXCLUDED.email,
            employment_status = EXCLUDED.employment_status,
            total_units = EXCLUDED.total_units,
            lecture_units = EXCLUDED.lecture_units,
            lab_units = EXCLUDED.lab_units,
            updated_at = CURRENT_TIMESTAMP
        RETURNING professor_id
        """,
        (
            user_id,
            faculty_number,
            load.first_name,
            load.last_name,
            email,
            load.employment_status,
            load.total_units,
            load.lecture_units,
            load.lab_units,
        ),
    )
    return cursor.fetchone()[0]


def upsert_course(cursor, code: str) -> int:
    cursor.execute(
        """
        INSERT INTO courses (course_code, course_name, units)
        VALUES (%s, %s, 3)
        ON CONFLICT (course_code) DO UPDATE
        SET course_name = CASE
                WHEN courses.course_name LIKE 'Pending Course Name - %%'
                THEN EXCLUDED.course_name
                ELSE courses.course_name
            END,
            updated_at = CURRENT_TIMESTAMP
        RETURNING course_id
        """,
        (code, f"Pending Course Name - {code}"),
    )
    return cursor.fetchone()[0]


def upsert_room(cursor, room: str) -> int:
    normalized = room or "TBA"
    cursor.execute(
        """
        INSERT INTO rooms (room_number, floor_level, building)
        VALUES (%s, %s, %s)
        ON CONFLICT (room_number) DO UPDATE
        SET floor_level = COALESCE(rooms.floor_level, EXCLUDED.floor_level),
            building = COALESCE(rooms.building, EXCLUDED.building),
            updated_at = CURRENT_TIMESTAMP
        RETURNING room_id
        """,
        (normalized, room_floor(normalized), "Mapua"),
    )
    return cursor.fetchone()[0]


def upsert_class(cursor, professor_id: int, entry: ScheduleEntry) -> None:
    course_id = upsert_course(cursor, entry.course_code)
    room_id = upsert_room(cursor, entry.room)
    cursor.execute(
        """
        SELECT class_id
        FROM classes
        WHERE professor_id = %s
          AND course_id = %s
          AND section = %s
          AND day_of_week = %s
          AND start_time = %s
          AND end_time = %s
        """,
        (
            professor_id,
            course_id,
            entry.section,
            entry.day_of_week,
            entry.start_time,
            entry.end_time,
        ),
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            """
            UPDATE classes
            SET room_id = %s,
                term = '2025-3RD',
                academic_year = '2025-2026',
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
            WHERE class_id = %s
            """,
            (room_id, existing[0]),
        )
        return

    cursor.execute(
        """
        INSERT INTO classes (
            course_id, professor_id, room_id, section, day_of_week,
            start_time, end_time, term, academic_year
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, '2025-3RD', '2025-2026')
        """,
        (
            course_id,
            professor_id,
            room_id,
            entry.section,
            entry.day_of_week,
            entry.start_time,
            entry.end_time,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import FRAS V2 professor schedules from the faculty-load DOCX.")
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX_PATH)
    parser.add_argument("--replace-docx-schedules", action="store_true")
    args = parser.parse_args(argv)

    if not args.docx.exists():
        print(f"Missing DOCX file: {args.docx}")
        return 1

    load_local_env()
    database_url = __import__("os").environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    loads = parse_professor_loads(extract_docx_paragraphs(args.docx))
    if not loads:
        print("No professor schedules were parsed from the DOCX.")
        return 1

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            ensure_professor_metadata_columns(cursor)
            if args.replace_docx_schedules:
                cursor.execute(
                    """
                    DELETE FROM classes
                    WHERE professor_id IN (
                        SELECT professor_id
                        FROM professors
                        WHERE faculty_number LIKE 'DOCX-%'
                    )
                    """
                )

            class_count = 0
            for load in loads:
                professor_id = upsert_professor(cursor, load)
                for entry in load.entries:
                    upsert_class(cursor, professor_id, entry)
                    class_count += 1

    print(f"Imported {len(loads)} professors and {class_count} schedule entries from {args.docx}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
