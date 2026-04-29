"""Normalize room numbers and merge duplicate FRAS room records.

Run from the project root:
    python scripts/fix_duplicate_rooms.py

This script is intentionally conservative:
- It normalizes room_number values such as "Room 305" or "room-305" to "305".
- It keeps the lowest room_id as the canonical room.
- It moves classes from duplicate rooms into the canonical room.
- It deletes duplicate room rows only after their classes have been moved.
- It adds a unique index to stop the issue from coming back.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path
import re

DB_PATH = Path("attendance.db")


def normalize_room_number(value: object) -> str:
    raw = "" if value is None else str(value).strip()
    matches = re.findall(r"(\d+)", raw)
    if not matches:
        return raw.upper()
    return (matches[-1].lstrip("0") or "0")


def floor_from_room(room_number: str) -> int:
    return int(room_number[0]) if room_number and room_number[0].isdigit() else 0


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database file not found: {DB_PATH.resolve()}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("SELECT room_id, room_number, campus_id, building_id FROM rooms ORDER BY room_id")
    rows = cursor.fetchall()

    groups: dict[tuple[int, int, str], list[int]] = defaultdict(list)
    for room_id, room_number, campus_id, building_id in rows:
        normalized = normalize_room_number(room_number)
        floor_level = floor_from_room(normalized)
        cursor.execute(
            "UPDATE rooms SET room_number = ?, floor_level = ? WHERE room_id = ?",
            (normalized, floor_level, room_id),
        )
        groups[(campus_id or 1, building_id or 1, normalized)].append(room_id)

    merged_count = 0
    for (_campus_id, _building_id, _room_number), room_ids in groups.items():
        if len(room_ids) <= 1:
            continue

        canonical_id = min(room_ids)
        duplicate_ids = [room_id for room_id in room_ids if room_id != canonical_id]

        for duplicate_id in duplicate_ids:
            cursor.execute(
                "UPDATE classes SET room_id = ? WHERE room_id = ?",
                (canonical_id, duplicate_id),
            )
            cursor.execute("DELETE FROM rooms WHERE room_id = ?", (duplicate_id,))
            merged_count += 1

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_rooms_unique_location_number
        ON rooms(campus_id, building_id, room_number)
        """
    )

    conn.commit()
    conn.close()

    print(f"Room cleanup complete. Duplicate room rows merged: {merged_count}")


if __name__ == "__main__":
    main()
