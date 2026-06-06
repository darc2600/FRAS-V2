from datetime import date, datetime

from backend import app
from database.init_v2_database import main as init_v2_database
from database.seed_v2_from_v1 import main as seed_v2_database
from v2.models import V2CreateEventRequest, V2StartSessionRequest
from v2.service import V2AttendanceService


def setup_module():
    assert init_v2_database() == 0
    assert seed_v2_database() == 0


def test_v2_routes_are_registered():
    paths = {route.path for route in app.routes}
    assert "/api/v2/professors/{professor_id}/today/classes" in paths
    assert "/api/v2/professors/{professor_id}/schedule" in paths
    assert "/api/v2/classes/{class_id}/sessions/start" in paths
    assert "/api/v2/sessions/{session_id}/events" in paths
    assert "/api/v2/sessions/{session_id}/review" in paths


def test_v2_today_classes_start_session_event_and_review_flow():
    service = V2AttendanceService()

    today = service.get_today_classes(professor_id=1, target_date=date(2026, 6, 4))
    all_classes = today.current + today.upcoming + today.completed
    assert len(all_classes) == 1
    assert all_classes[0].course_code == "IT119"
    assert all_classes[0].student_count == 30

    schedule = service.get_professor_schedule(professor_id=1)
    assert len(schedule.classes) == 1
    assert schedule.classes[0].day_of_week == "Thursday"

    session_detail = service.start_session(
        class_id=1,
        payload=V2StartSessionRequest(professor_id=1, session_date=date(2026, 6, 4)),
    )
    assert session_detail.session.session_status == "in_progress"
    assert session_detail.session.student_record_count == 30
    assert len(session_detail.roster) == 30
    session_id = session_detail.session.session_id
    student_id = session_detail.roster[0].student_id

    event_detail = service.create_event(
        session_id=session_id,
        payload=V2CreateEventRequest(
            student_id=student_id,
            event_type="time_in",
            event_source="manual_professor",
            event_time=datetime(2026, 6, 4, 11, 45),
            notes="Smoke test time in",
        ),
    )
    assert len(event_detail.events) == 1

    review = service.get_session_review(session_id=session_id)
    assert review.summary.total_students == 30
    assert review.summary.present_count == 1
    assert review.summary.absent_count == 29

    break_detail = service.start_break(session_id=session_id)
    assert break_detail.session.session_status == "on_break"
    assert any(event.event_type == "break_out" for event in break_detail.events)

    resumed_detail = service.end_break(session_id=session_id)
    assert resumed_detail.session.session_status == "in_progress"

    end_response = service.end_session(session_id=session_id)
    assert end_response.session.session_status == "under_review"
