# Room Duplicate Protection

This patch prevents the Add/Edit Schedule flow from creating duplicate room records.

## What changed

- Room labels such as `305`, `Room 305`, `room-305`, and `RM 0305` are normalized to one canonical value: `305`.
- Schedule lookup, schedule update, room list, course list, and section list now use the normalized value.
- Existing duplicate rooms can be merged with `scripts/fix_duplicate_rooms.py`.
- A unique database index prevents duplicate room rows for the same campus/building/room number.

## One-time cleanup

Run this once after applying the patch:

```bash
python scripts/fix_duplicate_rooms.py
```

## Validation

After cleanup, test these cases in Add/Edit Schedule:

1. Open room `305` and save a schedule.
2. Open room `Room 305` and save again.
3. Open room `room-305` and save again.
4. Confirm the schedule still loads under room `305`.
5. Confirm the room list does not show duplicate `305` entries.

## Why this matters

The previous flow checked the raw room input but saved the extracted numeric room number. That allowed entries like `Room 305` and `305` to create conflicting records. The conflict could break View Schedule and Add/Edit Schedule.
