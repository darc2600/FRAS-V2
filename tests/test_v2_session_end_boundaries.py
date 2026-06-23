from datetime import datetime
from types import SimpleNamespace

from v2.models import V2SessionResponse
from v2.service import V2AttendanceService


class FakeRepo:
    def __init__(self):
        self.events_by_student = {
            10: [("time_in", datetime(2026, 6, 17, 12, 0))],
            11: [
                ("time_in", datetime(2026, 6, 17, 12, 0)),
                ("break_out", datetime(2026, 6, 17, 12, 30)),
            ],
            12: [
                ("time_in", datetime(2026, 6, 17, 12, 0)),
                ("time_out", datetime(2026, 6, 17, 12, 45)),
            ],
        }
        self.created_events = []

    def get_student_events(self, session_id, student_id):
        return self.events_by_student[student_id]

    def create_event(
        self,
        session_id,
        record_id,
        student_id,
        event_type,
        event_time,
        event_source,
        recognition_confidence,
        notes,
    ):
        self.created_events.append(
            {
                "session_id": session_id,
                "record_id": record_id,
                "student_id": student_id,
                "event_type": event_type,
                "event_time": event_time,
                "event_source": event_source,
                "recognition_confidence": recognition_confidence,
                "notes": notes,
            }
        )
        return len(self.created_events)


def test_session_close_adds_time_out_for_inside_and_outside_students():
    service = V2AttendanceService(repo=FakeRepo())
    service._get_roster = lambda _session_id: [
        SimpleNamespace(record_id=100, student_id=10),
        SimpleNamespace(record_id=101, student_id=11),
        SimpleNamespace(record_id=102, student_id=12),
    ]
    session = V2SessionResponse(
        session_id=3,
        class_id=50,
        professor_id=5,
        scheduled_start=datetime(2026, 6, 17, 10, 30),
        scheduled_end=datetime(2026, 6, 17, 14, 0),
        actual_start=datetime(2026, 6, 17, 12, 1),
        actual_end=datetime(2026, 6, 17, 14, 0),
        session_status="under_review",
        student_record_count=3,
    )

    service._close_open_student_timelines(session)

    assert service.repo.created_events == [
        {
            "session_id": 3,
            "record_id": 100,
            "student_id": 10,
            "event_type": "time_out",
            "event_time": datetime(2026, 6, 17, 14, 0),
            "event_source": "system",
            "recognition_confidence": None,
            "notes": "Session ended by professor. Student automatically timed out at session end.",
        },
        {
            "session_id": 3,
            "record_id": 101,
            "student_id": 11,
            "event_type": "time_out",
            "event_time": datetime(2026, 6, 17, 14, 0),
            "event_source": "system",
            "recognition_confidence": None,
            "notes": "Session ended while student was out on break. Outside duration closed at session end.",
        },
    ]
