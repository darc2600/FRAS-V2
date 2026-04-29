"""Room code normalization helpers for FRAS.

The schedule editor can receive room labels in different formats such as
"305", "Room 305", "room-305", or "RM 305". The database should store one
canonical value so duplicate room rows do not break schedule lookups.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NormalizedRoom:
    room_number: str
    floor_level: int


_ROOM_NUMBER_PATTERN = re.compile(r"(\d+)")


def normalize_room_number(raw_room_code: object) -> str:
    """Return the canonical room number used for storage and lookup.

    Examples:
        "305" -> "305"
        "Room 305" -> "305"
        "room-305" -> "305"
        " RM 0305 " -> "305"

    Raises:
        ValueError: if the incoming room code does not contain a usable number.
    """

    raw_value = "" if raw_room_code is None else str(raw_room_code).strip()
    if not raw_value:
        raise ValueError("Room number is required.")

    matches = _ROOM_NUMBER_PATTERN.findall(raw_value)
    if not matches:
        raise ValueError("Room number must contain at least one digit.")

    room_number = matches[-1].lstrip("0") or "0"
    return room_number


def get_floor_level(room_number: str) -> int:
    """Infer the floor level from a normalized room number."""

    normalized = normalize_room_number(room_number)
    return int(normalized[0]) if normalized else 0


def normalize_room(raw_room_code: object) -> NormalizedRoom:
    room_number = normalize_room_number(raw_room_code)
    return NormalizedRoom(room_number=room_number, floor_level=get_floor_level(room_number))


def room_lookup_values(raw_room_code: object) -> tuple[str, str]:
    """Return values useful for backwards-compatible database lookups.

    First value is the canonical room number. Second value is the raw trimmed
    room code. Repositories use both to find older rows that may have been saved
    before normalization was introduced.
    """

    canonical = normalize_room_number(raw_room_code)
    raw = "" if raw_room_code is None else str(raw_room_code).strip()
    return canonical, raw
