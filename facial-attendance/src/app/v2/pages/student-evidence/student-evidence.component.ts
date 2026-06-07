import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../../api.service';
import {
  V2AttendanceEvent,
  V2ManualAttendanceStatus,
  V2ProfessorScheduleClass,
  V2SessionReviewResponse,
  V2StudentRecord
} from '../../models/v2-attendance.models';
import { V2StatusTone } from '../../components';

type EvidenceTimelineItem = {
  time: string;
  eventType: string;
  title: string;
  description: string;
  source: string;
  tone: 'success' | 'warning' | 'danger' | 'info' | 'neutral';
};

@Component({
  selector: 'app-v2-student-evidence',
  templateUrl: './student-evidence.component.html',
  styleUrls: ['./student-evidence.component.scss']
})
export class V2StudentEvidenceComponent implements OnInit {
  sessionId = 0;
  studentId = 0;
  review: V2SessionReviewResponse | null = null;
  sessionEvents: V2AttendanceEvent[] = [];
  student: V2StudentRecord | null = null;
  classInfo: V2ProfessorScheduleClass | null = null;
  isLoading = true;
  isSaving = false;
  errorMessage = '';
  actionMessage = '';
  overrideOpen = false;
  overrideStatusValue: V2ManualAttendanceStatus = 'present';
  overrideReason = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {}

  ngOnInit(): void {
    this.sessionId = Number(this.route.snapshot.paramMap.get('sessionId') || 0);
    this.studentId = Number(this.route.snapshot.paramMap.get('studentId') || 0);
    this.loadEvidence();
  }

  loadEvidence(): void {
    if (!this.sessionId || !this.studentId) {
      this.errorMessage = 'Missing session or student id.';
      this.isLoading = false;
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    forkJoin({
      review: this.api.getV2SessionReview(this.sessionId),
      detail: this.api.getV2Session(this.sessionId)
    }).subscribe({
      next: ({ review, detail }) => {
        this.review = review;
        this.sessionEvents = detail.events || [];
        this.student = review.roster.find((item) => item.student_id === this.studentId) || null;
        if (!this.student) {
          this.errorMessage = 'Student record was not found for this session.';
          this.isLoading = false;
          return;
        }
        this.loadClassInfo(review.session.professor_id, review.session.class_id);
      },
      error: () => {
        this.errorMessage = 'Unable to load student evidence.';
        this.isLoading = false;
      }
    });
  }

  get session() {
    return this.review?.session || null;
  }

  get studentEvents(): V2AttendanceEvent[] {
    return this.sessionEvents.filter((event) => event.student_id === this.studentId && !event.is_voided);
  }

  get timelineItems(): EvidenceTimelineItem[] {
    const events = this.studentEvents.length ? this.studentEvents : this.fallbackTimelineEvents();
    return [...events]
      .sort((a, b) => a.event_time.localeCompare(b.event_time))
      .map((event) => ({
        time: this.formatTime(event.event_time),
        eventType: event.event_type,
        title: this.statusLabel(event.event_type),
        description: this.eventDescription(event),
        source: this.evidenceSourceLabel(event),
        tone: this.timelineTone(event.event_type)
      }));
  }

  get sessionDurationMinutes(): number {
    if (!this.session) return 0;
    return this.minutesBetween(this.session.scheduled_start, this.session.scheduled_end);
  }

  get insideSeconds(): number {
    return (this.student?.total_presence_minutes || 0) * 60;
  }

  get outsideSeconds(): number {
    return (this.student?.total_outside_minutes || 0) * 60;
  }

  get sessionSeconds(): number {
    return Math.max(1, this.sessionDurationMinutes * 60);
  }

  get untrackedMinutes(): number {
    const tracked = (this.student?.total_presence_minutes || 0) + (this.student?.total_outside_minutes || 0);
    return Math.max(0, this.sessionDurationMinutes - tracked);
  }

  get assessmentTitle(): string {
    return this.assessmentLabel(this.student?.system_assessment || '');
  }

  get assessmentExplanation(): string {
    if (!this.student) return 'Evidence is unavailable for this student.';
    if (this.student.final_status === 'excused') {
      return 'This record has been approved as an exception by the professor.';
    }
    if (this.student.final_status === 'absent') {
      return 'No valid classroom time in was recorded for this student.';
    }
    if (this.student.final_status === 'late') {
      return `The student arrived ${this.student.late_minutes || 0} minutes after the scheduled start.`;
    }
    if (this.student.system_assessment === 'requires_review') {
      return 'Presence is below the expected threshold or the break pattern needs professor validation.';
    }
    if (this.student.system_assessment === 'attendance_warning') {
      return 'Presence was detected, but the duration or break pattern is close to the warning threshold.';
    }
    return 'The student has enough validated classroom presence for this session.';
  }

  get assessmentNotes(): string {
    if (!this.student) return 'No assessment notes available.';
    if (this.student.review_reason) return this.student.review_reason;
    if (this.student.final_status === 'present') return 'The student met the expected classroom presence threshold.';
    if (this.student.final_status === 'partial') return 'The student has partial presence and should be reviewed before finalization.';
    if (this.student.final_status === 'late') return 'The student was present but arrived after the grace period.';
    if (this.student.final_status === 'absent') return 'The system did not record a valid time in for this student.';
    if (this.student.final_status === 'excused') return 'The professor marked this student as excused.';
    return 'Review the timeline and presence ratio before confirming this record.';
  }

  get scheduledDateLabel(): string {
    if (!this.session) return '-';
    return new Intl.DateTimeFormat('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    }).format(new Date(this.session.scheduled_start));
  }

  get scheduledTimeRangeLabel(): string {
    if (!this.session) return '-';
    return `${this.formatTime(this.session.scheduled_start)} - ${this.formatTime(this.session.scheduled_end)}`;
  }

  get isFinalized(): boolean {
    return this.session?.session_status === 'finalized';
  }

  markExcused(): void {
    if (!this.student) return;
    this.saveStatus('excused', 'Marked excused from student evidence page.');
  }

  openOverride(): void {
    if (!this.student) return;
    this.overrideStatusValue = this.normalizeManualStatus(this.student.final_status);
    this.overrideReason = '';
    this.overrideOpen = true;
  }

  closeOverride(): void {
    if (this.isSaving) return;
    this.overrideOpen = false;
  }

  saveOverride(): void {
    const reason = this.overrideReason.trim();
    if (!reason) {
      this.errorMessage = 'Override reason is required.';
      return;
    }
    this.saveStatus(this.overrideStatusValue, `Override from student evidence page. Reason: ${reason}`);
  }

  confirmAttendance(): void {
    if (!this.student) return;
    if (this.isSaving || this.isFinalized) return;
    this.isSaving = true;
    this.errorMessage = '';
    this.api.confirmV2StudentRecord(this.sessionId, this.student.student_id).subscribe({
      next: () => {
        this.isSaving = false;
        this.actionMessage = 'Attendance confirmed for this student.';
        this.loadEvidence();
      },
      error: () => {
        this.isSaving = false;
        this.errorMessage = 'Unable to confirm this student record.';
      }
    });
  }

  backToReview(): void {
    this.router.navigate(['/session-review', this.sessionId]);
  }

  statusTone(status: string): V2StatusTone {
    const normalized = status.toLowerCase();
    if (normalized === 'present') return 'success';
    if (normalized === 'late' || normalized === 'partial') return 'warning';
    if (normalized === 'absent') return 'danger';
    if (normalized === 'excused') return 'excused';
    return 'neutral';
  }

  assessmentTone(): V2StatusTone {
    const assessment = this.student?.system_assessment || '';
    if (assessment === 'valid_presence') return 'success';
    if (assessment === 'attendance_warning') return 'warning';
    if (assessment === 'requires_review') return 'danger';
    return this.statusTone(this.student?.final_status || '');
  }

  statusLabel(value: string): string {
    return (value || '-').replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
  }

  assessmentLabel(value: string): string {
    return this.statusLabel(value || this.student?.final_status || 'Assessment');
  }

  initialsForStudent(): string {
    if (!this.student) return 'ST';
    return this.student.student_name
      .split(/[,\s]+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join('') || 'ST';
  }

  minutesLabel(minutes: number): string {
    const safe = Math.max(0, minutes || 0);
    const hours = Math.floor(safe / 60);
    const mins = safe % 60;
    return hours ? `${hours}h ${mins}m` : `${mins}m`;
  }

  formatTime(value?: string | null): string {
    if (!value) return '-';
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit'
    }).format(new Date(value));
  }

  private loadClassInfo(professorId: number, classId: number): void {
    this.api.getV2ProfessorSchedule(professorId).subscribe({
      next: (schedule) => {
        this.classInfo = schedule.classes.find((item) => item.class_id === classId) || null;
        this.isLoading = false;
      },
      error: () => {
        this.classInfo = null;
        this.isLoading = false;
      }
    });
  }

  private saveStatus(status: V2ManualAttendanceStatus, notes: string): void {
    if (!this.session || !this.student || this.isSaving || this.isFinalized) return;
    this.isSaving = true;
    this.errorMessage = '';
    this.api.saveV2ManualAttendance(this.sessionId, {
      professor_id: this.session.professor_id,
      records: [{
        record_id: this.student.record_id,
        student_id: this.student.student_id,
        status
      }],
      notes
    }).subscribe({
      next: () => {
        this.isSaving = false;
        this.overrideOpen = false;
        this.actionMessage = `Student status updated to ${this.statusLabel(status)}.`;
        this.loadEvidence();
      },
      error: () => {
        this.isSaving = false;
        this.errorMessage = 'Unable to update this student record.';
      }
    });
  }

  private fallbackTimelineEvents(): V2AttendanceEvent[] {
    if (!this.student) return [];
    const events: V2AttendanceEvent[] = [];
    if (this.student.time_in) {
      events.push(this.syntheticEvent('time_in', this.student.time_in, 'Calculated from student session record.'));
    }
    if (this.student.time_out) {
      events.push(this.syntheticEvent('time_out', this.student.time_out, 'Calculated from student session record.'));
    }
    if (!events.length && this.student.final_status === 'absent' && this.session) {
      events.push(this.syntheticEvent('missed_recognition', this.session.scheduled_start, 'No recognition event was recorded for this student.'));
    }
    return events;
  }

  private syntheticEvent(eventType: string, eventTime: string, notes: string): V2AttendanceEvent {
    return {
      event_id: 0,
      session_id: this.sessionId,
      record_id: this.student?.record_id || null,
      student_id: this.studentId,
      event_type: eventType,
      event_time: eventTime,
      event_source: 'system',
      recognition_confidence: null,
      notes,
      is_voided: false
    };
  }

  private eventDescription(event: V2AttendanceEvent): string {
    if (event.notes) return event.notes;
    if (event.event_type === 'time_in') return 'Student entered the classroom attendance session.';
    if (event.event_type === 'break_out') return 'Student left the classroom and outside duration tracking began.';
    if (event.event_type === 'break_in') return 'Student returned to the classroom and presence tracking resumed.';
    if (event.event_type === 'time_out') return 'Student was last recorded before session close.';
    if (event.event_type === 'manual_attendance') return 'Professor manually updated this attendance record.';
    return 'Attendance evidence event recorded for this session.';
  }

  private evidenceSourceLabel(event: V2AttendanceEvent): string {
    if (event.event_source === 'facial_recognition') return 'Face Recognition';
    if (event.event_source === 'manual_professor') return 'Professor Action';
    return 'System Evidence';
  }

  private timelineTone(eventType: string): EvidenceTimelineItem['tone'] {
    if (eventType === 'time_in' || eventType === 'manual_attendance') return 'success';
    if (eventType === 'break_out' || eventType === 'break_in') return 'info';
    if (eventType.includes('failure') || eventType.includes('missed')) return 'danger';
    if (eventType === 'false_recognition') return 'warning';
    return 'neutral';
  }

  private normalizeManualStatus(status: string): V2ManualAttendanceStatus {
    if (status === 'present' || status === 'absent' || status === 'late' || status === 'excused') {
      return status;
    }
    return 'present';
  }

  private minutesBetween(start: string, end: string): number {
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();
    if (!Number.isFinite(startTime) || !Number.isFinite(endTime)) return 0;
    return Math.max(0, Math.floor((endTime - startTime) / 60000));
  }
}
