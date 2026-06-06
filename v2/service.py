from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from v2.models import (
    V2AttendanceEvent,
    V2ClassCard,
    V2CreateEventRequest,
    V2ManualAttendanceRequest,
    V2ProfessorScheduleClass,
    V2ProfessorScheduleResponse,
    V2ReviewSummary,
    V2SessionDetailResponse,
    V2SessionResponse,
    V2SessionReviewResponse,
    V2StartSessionRequest,
    V2StudentRecord,
    V2TodayClassesResponse,
)
from v2.repository import V2AttendanceRepository


MANILA_TZ = ZoneInfo("Asia/Manila")


class V2AttendanceService:
    def __init__(self, repo: V2AttendanceRepository | None = None):
        self.repo = repo or V2AttendanceRepository()

    def get_today_classes(self, professor_id: int = 1, target_date: date | None = None) -> V2TodayClassesResponse:
        target_date = target_date or datetime.now(MANILA_TZ).date()
        now = datetime.now(MANILA_TZ)
        day_name = target_date.strftime("%A")
        rows = self.repo.list_professor_classes_for_day(professor_id, day_name)

        current: list[V2ClassCard] = []
        upcoming: list[V2ClassCard] = []
        completed: list[V2ClassCard] = []

        for row in rows:
            start_time = self._coerce_time(row[6])
            end_time = self._coerce_time(row[7])
            status = self._class_status(target_date, start_time, end_time, now)
            card = V2ClassCard(
                class_id=row[0],
                course_code=row[1],
                course_name=row[2],
                section=row[3],
                room=row[4] or "TBA",
                day_of_week=row[5],
                start_time=start_time,
                end_time=end_time,
                student_count=row[8],
                status=status,
                active_session_id=row[9],
            )
            if status == "current":
                current.append(card)
            elif status == "upcoming":
                upcoming.append(card)
            else:
                completed.append(card)

        return V2TodayClassesResponse(
            professor_id=professor_id,
            date=target_date,
            current=current,
            upcoming=upcoming,
            completed=completed,
        )

    def get_professor_schedule(self, professor_id: int = 1) -> V2ProfessorScheduleResponse:
        classes = [
            V2ProfessorScheduleClass(
                class_id=row[0],
                course_code=row[1],
                course_name=row[2],
                section=row[3],
                room=row[4] or "TBA",
                day_of_week=row[5],
                start_time=self._coerce_time(row[6]),
                end_time=self._coerce_time(row[7]),
                student_count=row[8],
            )
            for row in self.repo.list_professor_schedule(professor_id)
        ]
        return V2ProfessorScheduleResponse(professor_id=professor_id, classes=classes)

    def start_session(self, class_id: int, payload: V2StartSessionRequest) -> V2SessionDetailResponse:
        session_date = payload.session_date or datetime.now(MANILA_TZ).date()
        class_row = self.repo.get_class_for_session_start(class_id, payload.professor_id)
        if not class_row:
            raise HTTPException(status_code=404, detail="Class not found for professor.")

        active = self.repo.get_active_session(class_id, payload.professor_id)
        if active:
            return self.get_session_detail(active[0])

        start_time = self._coerce_time(class_row[3])
        end_time = self._coerce_time(class_row[4])
        scheduled_start = self._combine_local(session_date, start_time)
        scheduled_end = self._combine_local(session_date, end_time)
        actual_start = datetime.now(MANILA_TZ).replace(tzinfo=None)

        session_id = self.repo.create_session(
            class_id=class_id,
            professor_id=payload.professor_id,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            actual_start=actual_start,
        )
        return self.get_session_detail(session_id)

    def get_session_detail(self, session_id: int) -> V2SessionDetailResponse:
        session = self._get_session_or_404(session_id)
        return V2SessionDetailResponse(
            session=session,
            roster=self._get_roster(session_id),
            events=self._get_events(session_id),
        )

    def get_session_review(self, session_id: int) -> V2SessionReviewResponse:
        session = self._get_session_or_404(session_id)
        roster = self._get_roster(session_id)
        summary = self._build_review_summary(roster)
        return V2SessionReviewResponse(session=session, summary=summary, roster=roster)

    def create_event(self, session_id: int, payload: V2CreateEventRequest) -> V2SessionDetailResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status not in {"in_progress", "on_break", "under_review"}:
            raise HTTPException(status_code=400, detail="Session is not accepting attendance events.")

        record_row = self.repo.get_record_for_student(session_id, payload.student_id)
        if not record_row:
            raise HTTPException(status_code=404, detail="Student is not enrolled in this session.")

        event_time = payload.event_time or datetime.now(MANILA_TZ).replace(tzinfo=None)
        record_id = int(record_row[0])
        self.repo.create_event(
            session_id=session_id,
            record_id=record_id,
            student_id=payload.student_id,
            event_type=payload.event_type,
            event_time=event_time,
            event_source=payload.event_source,
            recognition_confidence=payload.recognition_confidence,
            notes=payload.notes,
        )
        self._recalculate_student_record(session, record_id, payload.student_id)
        return self.get_session_detail(session_id)

    def save_manual_attendance(self, session_id: int, payload: V2ManualAttendanceRequest) -> V2SessionDetailResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status not in {"in_progress", "on_break", "under_review"}:
            raise HTTPException(status_code=400, detail="Session is not accepting manual attendance.")

        now = datetime.now(MANILA_TZ).replace(tzinfo=None)
        for item in payload.records:
            record_row = self.repo.get_record_for_override(session_id, item.record_id, item.student_id)
            if not record_row:
                raise HTTPException(status_code=404, detail="Student record not found for this session.")

            previous_status = str(record_row[1])
            existing_time_in = self._coerce_datetime(record_row[2]) if record_row[2] else None
            if item.status in {"present", "late"}:
                assessment = "valid_presence"
                time_in = existing_time_in or now
            elif item.status == "excused":
                assessment = "valid_presence"
                time_in = existing_time_in
            else:
                assessment = "absent"
                time_in = existing_time_in

            self.repo.apply_manual_status(
                record_id=item.record_id,
                professor_id=payload.professor_id,
                previous_status=previous_status,
                new_status=item.status,
                system_assessment=assessment,
                time_in=time_in,
                notes=payload.notes,
            )
            if item.status in {"present", "late"} and not existing_time_in:
                self.repo.create_event(
                    session_id=session_id,
                    record_id=item.record_id,
                    student_id=item.student_id,
                    event_type="manual_attendance",
                    event_time=now,
                    event_source="manual_professor",
                    recognition_confidence=None,
                    notes=payload.notes or f"Marked {item.status} from manual attendance.",
                )

        return self.get_session_detail(session_id)

    def start_break(self, session_id: int) -> V2SessionDetailResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status == "on_break":
            return self.get_session_detail(session_id)
        if session.session_status != "in_progress":
            raise HTTPException(status_code=400, detail="Session break can only start during an in-progress session.")

        now = datetime.now(MANILA_TZ).replace(tzinfo=None)
        self.repo.set_session_status(session_id, "on_break")
        session = self._get_session_or_404(session_id)

        for record_id, student_id, _final_status, _time_in in self.repo.list_break_candidate_records(session_id):
            last_event = self.repo.get_student_events(session_id, int(student_id))[-1:]
            if last_event and last_event[0][0] == "break_out":
                continue

            self.repo.create_event(
                session_id=session_id,
                record_id=int(record_id),
                student_id=int(student_id),
                event_type="break_out",
                event_time=now,
                event_source="system",
                recognition_confidence=None,
                notes="Session Break started by professor. Return Detection Mode enabled.",
            )
            self._recalculate_student_record(session, int(record_id), int(student_id))

        return self.get_session_detail(session_id)

    def end_break(self, session_id: int) -> V2SessionDetailResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status != "on_break":
            raise HTTPException(status_code=400, detail="Session is not currently on break.")

        self.repo.set_session_status(session_id, "in_progress")
        return self.get_session_detail(session_id)

    def end_session(self, session_id: int) -> V2SessionReviewResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status not in {"in_progress", "on_break", "under_review"}:
            raise HTTPException(status_code=400, detail="Session cannot be ended from its current status.")

        self.repo.end_session(session_id, datetime.now(MANILA_TZ).replace(tzinfo=None))
        refreshed = self._get_session_or_404(session_id)
        for record in self._get_roster(session_id):
            self._recalculate_student_record(refreshed, record.record_id, record.student_id)
        return self.get_session_review(session_id)

    def _recalculate_student_record(self, session: V2SessionResponse, record_id: int, student_id: int) -> None:
        events = self.repo.get_student_events(session.session_id, student_id)
        normalized = [(row[0], self._coerce_datetime(row[1])) for row in events]
        time_in = next((event_time for event_type, event_time in normalized if event_type in {"time_in", "manual_attendance"}), None)
        time_out = None
        presence_minutes = 0
        outside_minutes = 0
        break_count = 0
        outside_started_at = None
        inside_started_at = None

        session_end = session.actual_end or datetime.now(MANILA_TZ).replace(tzinfo=None)

        for event_type, event_time in normalized:
            if event_type in {"time_in", "break_in", "manual_attendance"}:
                if outside_started_at:
                    outside_minutes += self._minutes_between(outside_started_at, event_time)
                    outside_started_at = None
                if not inside_started_at:
                    inside_started_at = event_time
                if not time_in:
                    time_in = event_time
            elif event_type in {"break_out", "time_out"}:
                if inside_started_at:
                    presence_minutes += self._minutes_between(inside_started_at, event_time)
                    inside_started_at = None
                if event_type == "break_out":
                    break_count += 1
                    outside_started_at = event_time
                else:
                    time_out = event_time

        if inside_started_at:
            presence_minutes += self._minutes_between(inside_started_at, session_end)
        if outside_started_at:
            outside_minutes += self._minutes_between(outside_started_at, session_end)

        scheduled_minutes = max(1, self._minutes_between(session.scheduled_start, session.scheduled_end))
        ratio = presence_minutes / scheduled_minutes
        late_minutes = 0
        if time_in:
            late_minutes = max(0, self._minutes_between(session.scheduled_start, time_in))

        if not time_in:
            final_status = "absent"
            system_assessment = "absent"
            requires_review = False
            review_reason = None
        elif late_minutes > 15:
            final_status = "late"
            system_assessment = self._assessment_from_ratio(ratio)
            requires_review = system_assessment == "requires_review"
            review_reason = "Student arrived after the 15-minute attendance window."
        elif ratio >= 0.8:
            final_status = "present"
            system_assessment = "valid_presence"
            requires_review = False
            review_reason = None
        elif ratio >= 0.6:
            final_status = "partial"
            system_assessment = "attendance_warning"
            requires_review = False
            review_reason = "Presence is below 80% of the scheduled session."
        else:
            final_status = "partial"
            system_assessment = "requires_review"
            requires_review = True
            review_reason = "Presence is below 60% of the scheduled session."

        self.repo.update_student_record(
            record_id=record_id,
            final_status=final_status,
            system_assessment=system_assessment,
            time_in=time_in,
            time_out=time_out,
            total_presence_minutes=presence_minutes,
            total_outside_minutes=outside_minutes,
            break_count=break_count,
            late_minutes=late_minutes,
            requires_review=requires_review,
            review_reason=review_reason,
        )

    def _get_session_or_404(self, session_id: int) -> V2SessionResponse:
        row = self.repo.get_session(session_id)
        if not row:
            raise HTTPException(status_code=404, detail="Session not found.")
        return V2SessionResponse(
            session_id=row[0],
            class_id=row[1],
            professor_id=row[2],
            scheduled_start=self._coerce_datetime(row[3]),
            scheduled_end=self._coerce_datetime(row[4]),
            actual_start=self._coerce_datetime(row[5]) if row[5] else None,
            actual_end=self._coerce_datetime(row[6]) if row[6] else None,
            session_status=row[7],
            student_record_count=row[8],
        )

    def _get_roster(self, session_id: int) -> list[V2StudentRecord]:
        records = []
        for row in self.repo.list_session_records(session_id):
            records.append(
                V2StudentRecord(
                    record_id=row[0],
                    student_id=row[1],
                    student_number=row[2],
                    student_name=f"{row[4]}, {row[3]}",
                    final_status=row[5],
                    system_assessment=row[6],
                    time_in=self._coerce_datetime(row[7]) if row[7] else None,
                    time_out=self._coerce_datetime(row[8]) if row[8] else None,
                    total_presence_minutes=row[9],
                    total_outside_minutes=row[10],
                    break_count=row[11],
                    late_minutes=row[12],
                    requires_review=bool(row[13]),
                    review_reason=row[14],
                )
            )
        return records

    def _get_events(self, session_id: int) -> list[V2AttendanceEvent]:
        events = []
        for row in self.repo.list_session_events(session_id):
            events.append(
                V2AttendanceEvent(
                    event_id=row[0],
                    session_id=row[1],
                    record_id=row[2],
                    student_id=row[3],
                    event_type=row[4],
                    event_time=self._coerce_datetime(row[5]),
                    event_source=row[6],
                    recognition_confidence=float(row[7]) if row[7] is not None else None,
                    notes=row[8],
                    is_voided=bool(row[9]),
                )
            )
        return events

    def _build_review_summary(self, roster: list[V2StudentRecord]) -> V2ReviewSummary:
        total = len(roster)
        present = sum(1 for record in roster if record.final_status == "present")
        late = sum(1 for record in roster if record.final_status == "late")
        partial = sum(1 for record in roster if record.final_status == "partial")
        absent = sum(1 for record in roster if record.final_status == "absent")
        excused = sum(1 for record in roster if record.final_status == "excused")
        review = sum(1 for record in roster if record.requires_review)
        validated = present + late + partial + excused
        rate = round((validated / total) * 100, 2) if total else 0.0
        return V2ReviewSummary(
            present_count=present,
            late_count=late,
            partial_count=partial,
            absent_count=absent,
            excused_count=excused,
            students_requiring_review=review,
            total_students=total,
            presence_validation_rate=rate,
        )

    def _class_status(
        self,
        target_date: date,
        start_time: time,
        end_time: time,
        now: datetime,
    ) -> str:
        start_dt = self._combine_local(target_date, start_time)
        end_dt = self._combine_local(target_date, end_time)
        local_now = now.replace(tzinfo=None)
        if start_dt <= local_now <= end_dt:
            return "current"
        if local_now < start_dt:
            return "upcoming"
        return "completed"

    def _assessment_from_ratio(self, ratio: float) -> str:
        if ratio >= 0.8:
            return "valid_presence"
        if ratio >= 0.6:
            return "attendance_warning"
        return "requires_review"

    def _combine_local(self, value_date: date, value_time: time) -> datetime:
        return datetime.combine(value_date, value_time)

    def _coerce_time(self, value) -> time:
        if isinstance(value, time):
            return value
        text = str(value).strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(text, fmt).time()
            except ValueError:
                continue
        raise ValueError(f"Invalid time value: {value}")

    def _coerce_datetime(self, value) -> datetime:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        text = str(value).strip().replace("T", " ")
        if text.endswith("Z"):
            text = text[:-1]
        if "+" in text[10:]:
            text = text.split("+", 1)[0]
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return datetime.fromisoformat(text).replace(tzinfo=None)

    def _minutes_between(self, start: datetime, end: datetime) -> int:
        return max(0, int((end - start).total_seconds() // 60))


def get_v2_attendance_service() -> V2AttendanceService:
    return V2AttendanceService()
