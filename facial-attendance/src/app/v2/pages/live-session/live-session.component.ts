import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin, Observable, Subject } from 'rxjs';
import { WebcamImage } from 'ngx-webcam';
import { ApiService } from '../../../api.service';
import { AuthService } from '../../../auth.service';
import {
  V2AttendanceEvent,
  V2CreateEventRequest,
  V2ManualAttendanceStatus,
  V2ProfessorScheduleClass,
  V2ProfessorScheduleResponse,
  V2SessionDetailResponse,
  V2StudentRecord
} from '../../models/v2-attendance.models';
import { V2StatusTone } from '../../components';

const PROFESSOR_ID = 1;

@Component({
  selector: 'app-v2-live-session',
  templateUrl: './live-session.component.html',
  styleUrls: ['./live-session.component.scss']
})
export class V2LiveSessionComponent implements OnInit, OnDestroy {
  sessionId = 0;
  detail: V2SessionDetailResponse | null = null;
  classInfo: V2ProfessorScheduleClass | null = null;
  isLoading = true;
  isEnding = false;
  errorMessage = '';
  actionMessage = '';
  rosterSearch = '';
  selectedStudent: V2StudentRecord | null = null;
  unknownFaceLabel = '';
  autoCaptureActive = false;
  manualAttendanceOpen = false;
  manualAttendanceSaving = false;
  manualAttendanceSearch = '';
  manualAttendanceSelections: Record<number, V2ManualAttendanceStatus> = {};
  studentBreakLimitMinutes = 10;
  breakUnlocked = false;
  breakUnlockPassword = '';
  breakUnlockError = '';
  isBreakStarting = false;
  isBreakEnding = false;
  isUnlockingBreak = false;
  breakPreviewMode = false;
  cameraReady = false;
  webcamImage: WebcamImage | null = null;
  now = new Date();
  private timer: any;
  private trigger: Subject<void> = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private auth: AuthService
  ) {}

  ngOnInit(): void {
    this.sessionId = Number(this.route.snapshot.paramMap.get('sessionId') || 0);
    this.loadSession();
    this.timer = setInterval(() => this.now = new Date(), 1000);
    document.addEventListener('keydown', this.handleKeyDown);
  }

  ngOnDestroy(): void {
    if (this.timer) clearInterval(this.timer);
    document.removeEventListener('keydown', this.handleKeyDown);
  }

  loadSession(): void {
    if (!this.sessionId) {
      this.errorMessage = 'Missing session id.';
      this.isLoading = false;
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    forkJoin({
      detail: this.api.getV2Session(this.sessionId),
      schedule: this.api.getV2ProfessorSchedule(PROFESSOR_ID)
    }).subscribe({
      next: ({ detail, schedule }) => {
        this.detail = detail;
        this.classInfo = this.findClassInfo(schedule, detail.session.class_id);
        this.selectedStudent = null;
        if (this.isBreakMode) {
          this.autoCaptureActive = true;
          this.breakUnlocked = false;
        }
        this.isLoading = false;
      },
      error: () => {
        this.errorMessage = 'Unable to load this live session.';
        this.isLoading = false;
      }
    });
  }

  get session() {
    return this.detail?.session || null;
  }

  get roster(): V2StudentRecord[] {
    return this.detail?.roster || [];
  }

  get events(): V2AttendanceEvent[] {
    return [...(this.detail?.events || [])].sort((a, b) => b.event_time.localeCompare(a.event_time));
  }

  get filteredRoster(): V2StudentRecord[] {
    const query = this.rosterSearch.trim().toLowerCase();
    if (!query) return this.roster;
    return this.roster.filter((student) =>
      student.student_name.toLowerCase().includes(query) ||
      student.student_number.toLowerCase().includes(query) ||
      student.final_status.toLowerCase().includes(query)
    );
  }

  get scheduledTimeLabel(): string {
    if (!this.session) return '-';
    return `${this.formatDateTime(this.session.scheduled_start)} - ${this.formatTime(this.session.scheduled_end)}`;
  }

  get sessionTimerLabel(): string {
    if (!this.session?.actual_start) return '00:00:00';
    const end = this.session.actual_end ? new Date(this.session.actual_end) : this.now;
    const start = new Date(this.session.actual_start);
    const seconds = Math.max(0, Math.floor((end.getTime() - start.getTime()) / 1000));
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return [hours, minutes, secs].map((part) => String(part).padStart(2, '0')).join(':');
  }

  get presentCount(): number {
    return this.countByStatus('present');
  }

  get lateCount(): number {
    return this.countByStatus('late');
  }

  get onBreakCount(): number {
    return this.roster.filter((student) => this.lastStudentEvent(student.student_id)?.event_type === 'break_out').length;
  }

  get absentCount(): number {
    return this.countByStatus('absent');
  }

  get excusedCount(): number {
    return this.countByStatus('excused');
  }

  get selectedStudentEvents(): V2AttendanceEvent[] {
    if (!this.selectedStudent) return [];
    return this.events.filter((event) => event.student_id === this.selectedStudent?.student_id);
  }

  get triggerObservable(): Observable<void> {
    return this.trigger.asObservable();
  }

  get scheduledTimeRangeLabel(): string {
    if (!this.session) return '-';
    return `${this.formatTime(this.session.scheduled_start)} - ${this.formatTime(this.session.scheduled_end)}`;
  }

  get isBreakMode(): boolean {
    return this.session?.session_status === 'on_break';
  }

  get cameraModeLabel(): string {
    if (this.isBreakMode) {
      return `Return Detection Mode ${this.autoCaptureActive ? 'Active' : 'Idle'}`;
    }
    return `Face Recognition ${this.autoCaptureActive ? 'Active' : 'Idle'}`;
  }

  get breakInEvents(): V2AttendanceEvent[] {
    return this.events.filter((event) => event.event_type === 'break_in');
  }

  get returnedFromBreakCount(): number {
    return this.roster.filter((student) => this.lastStudentEvent(student.student_id)?.event_type === 'break_in').length;
  }

  get stillOutsideCount(): number {
    return this.onBreakCount;
  }

  selectStudent(student: V2StudentRecord): void {
    this.selectedStudent = student;
  }

  closeDrawer(): void {
    this.selectedStudent = null;
  }

  startSession(): void {
    this.actionMessage = this.session?.session_status === 'in_progress'
      ? 'This session is already in progress.'
      : 'Start session is handled from the Classes page for V2.';
  }

  manualAttendance(): void {
    if (this.controlsLockedByBreak()) return;
    this.openManualAttendanceModal();
  }

  manualCapture(): void {
    if (this.controlsLockedByBreak()) return;
    if (this.autoCaptureActive) {
      this.actionMessage = 'Manual capture is paused while auto capture is active.';
      return;
    }
    this.trigger.next();
    if (this.selectedStudent) {
      this.createStudentEvent('manual_capture', 'Manual capture recorded. Camera recognition is not connected yet.');
      return;
    }
    this.actionMessage = 'Manual capture requested. Select a student to attach the capture as an attendance event.';
  }

  handleImage(webcamImage: WebcamImage): void {
    this.webcamImage = webcamImage;
    this.cameraReady = true;
    this.actionMessage = 'Manual camera capture received.';
  }

  startAutoCapture(): void {
    this.autoCaptureActive = true;
    this.actionMessage = this.isBreakMode
      ? 'Return Detection Mode is active. Only Break In events should be recorded during Session Break.'
      : 'Auto capture placeholder is active. Camera integration will be connected later.';
  }

  stopAutoCapture(): void {
    this.autoCaptureActive = false;
    this.actionMessage = 'Auto capture stopped.';
  }

  toggleAutoCapture(): void {
    if (this.autoCaptureActive) {
      this.stopAutoCapture();
      return;
    }
    this.startAutoCapture();
  }

  startBreak(): void {
    if (this.isBreakStarting || this.isBreakMode) return;
    this.isBreakStarting = true;
    this.errorMessage = '';
    this.api.startV2SessionBreak(this.sessionId).subscribe({
      next: (detail) => {
        this.detail = detail;
        this.autoCaptureActive = true;
        this.breakUnlocked = false;
        this.breakUnlockPassword = '';
        this.breakUnlockError = '';
        this.isBreakStarting = false;
        this.actionMessage = 'Session Break started. Return Detection Mode is active.';
      },
      error: (error) => {
        this.isBreakStarting = false;
        if (error?.status === 404) {
          this.enterBreakPreviewMode();
          return;
        }
        this.errorMessage = this.apiErrorMessage(error, 'Unable to start Session Break.');
      }
    });
  }

  unlockBreakControls(): void {
    if (this.isUnlockingBreak) return;
    const email = this.auth.getCurrentUser()?.email;
    if (!email) {
      this.breakUnlockError = 'Current user account is unavailable. Please sign in again.';
      return;
    }
    if (!this.breakUnlockPassword.trim()) {
      this.breakUnlockError = 'Enter your password to unlock controls.';
      return;
    }

    this.isUnlockingBreak = true;
    this.breakUnlockError = '';
    this.api.reauthenticate(email, this.breakUnlockPassword).subscribe({
      next: () => {
        this.isUnlockingBreak = false;
        this.breakUnlocked = true;
        this.breakUnlockPassword = '';
        this.actionMessage = 'Professor controls unlocked.';
      },
      error: () => {
        this.isUnlockingBreak = false;
        this.breakUnlockError = 'Password verification failed.';
      }
    });
  }

  endBreak(): void {
    if (!this.breakUnlocked || this.isBreakEnding) return;
    if (this.breakPreviewMode) {
      this.exitBreakPreviewMode();
      return;
    }
    this.isBreakEnding = true;
    this.errorMessage = '';
    this.api.endV2SessionBreak(this.sessionId).subscribe({
      next: (detail) => {
        this.detail = detail;
        this.autoCaptureActive = true;
        this.breakUnlocked = false;
        this.isBreakEnding = false;
        this.actionMessage = 'Session Break ended. Regular monitoring resumed.';
      },
      error: (error) => {
        this.isBreakEnding = false;
        this.errorMessage = this.apiErrorMessage(error, 'Unable to end Session Break.');
      }
    });
  }

  markExcused(): void {
    if (this.controlsLockedByBreak()) return;
    this.actionMessage = 'Mark Excused requires the V2 override endpoint, which is not available yet.';
  }

  bathroomBreak(): void {
    if (this.controlsLockedByBreak()) return;
    if (!this.selectedStudent) {
      this.actionMessage = 'Select a student first.';
      return;
    }

    const lastEvent = this.lastStudentEvent(this.selectedStudent.student_id);
    const isCurrentlyOutside = lastEvent?.event_type === 'break_out';
    const minutes = this.normalizedStudentBreakLimit();
    this.createStudentEvent(
      isCurrentlyOutside ? 'break_in' : 'break_out',
      isCurrentlyOutside
        ? 'Bathroom Break In'
        : `Bathroom Break Out. Limit: ${minutes} minutes.`
    );
  }

  setStudentBreakLimit(value: number | string): void {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return;
    this.studentBreakLimitMinutes = Math.min(120, Math.max(1, Math.round(parsed)));
  }

  updateStatus(): void {
    if (this.controlsLockedByBreak()) return;
    this.actionMessage = 'Status override requires the V2 override endpoint, which is not available yet.';
  }

  quickOverrideStatus(status: V2ManualAttendanceStatus): void {
    if (this.controlsLockedByBreak()) return;
    if (!this.selectedStudent) {
      this.actionMessage = 'Select a student first.';
      return;
    }

    const selectedId = this.selectedStudent.student_id;
    this.api.saveV2ManualAttendance(this.sessionId, {
      professor_id: PROFESSOR_ID,
      records: [{
        record_id: this.selectedStudent.record_id,
        student_id: this.selectedStudent.student_id,
        status
      }],
      notes: `Quick override: ${this.statusLabel(status)}.`
    }).subscribe({
      next: (detail) => {
        this.detail = detail;
        this.selectedStudent = this.roster.find((student) => student.student_id === selectedId) || null;
        this.actionMessage = `Status overridden to ${this.statusLabel(status)}.`;
      },
      error: (error) => {
        this.errorMessage = this.apiErrorMessage(error, 'Unable to override student status.');
      }
    });
  }

  openManualAttendanceModal(): void {
    this.manualAttendanceSelections = {};
    for (const student of this.roster) {
      if (student.final_status === 'present' || student.final_status === 'excused') {
        this.manualAttendanceSelections[student.record_id] = student.final_status;
      } else {
        this.manualAttendanceSelections[student.record_id] = 'absent';
      }
    }
    this.manualAttendanceSearch = '';
    this.manualAttendanceOpen = true;
  }

  closeManualAttendanceModal(): void {
    if (this.manualAttendanceSaving) return;
    this.manualAttendanceOpen = false;
  }

  get filteredManualAttendanceRoster(): V2StudentRecord[] {
    const query = this.manualAttendanceSearch.trim().toLowerCase();
    if (!query) return this.roster;
    return this.roster.filter((student) =>
      student.student_name.toLowerCase().includes(query) ||
      student.student_number.toLowerCase().includes(query)
    );
  }

  setManualAttendanceStatus(student: V2StudentRecord, status: V2ManualAttendanceStatus): void {
    this.manualAttendanceSelections[student.record_id] = status;
  }

  manualAttendanceStatusFor(student: V2StudentRecord): V2ManualAttendanceStatus {
    return this.manualAttendanceSelections[student.record_id] || 'absent';
  }

  saveManualAttendance(): void {
    if (this.manualAttendanceSaving) return;
    this.manualAttendanceSaving = true;
    this.errorMessage = '';
    this.api.saveV2ManualAttendance(this.sessionId, {
      professor_id: PROFESSOR_ID,
      records: this.roster.map((student) => ({
        record_id: student.record_id,
        student_id: student.student_id,
        status: this.manualAttendanceStatusFor(student)
      })),
      notes: 'Saved from V2 live session manual attendance modal.'
    }).subscribe({
      next: (detail) => {
        this.detail = detail;
        this.manualAttendanceSaving = false;
        this.manualAttendanceOpen = false;
        this.actionMessage = 'Manual attendance saved.';
      },
      error: () => {
        this.manualAttendanceSaving = false;
        this.errorMessage = 'Unable to save manual attendance.';
      }
    });
  }

  endSession(): void {
    if (this.controlsLockedByBreak()) return;
    if (!this.sessionId || this.isEnding) return;
    this.isEnding = true;
    this.errorMessage = '';
    this.api.endV2Session(this.sessionId).subscribe({
      next: () => {
        this.isEnding = false;
        this.router.navigate(['/v2/sessions', this.sessionId, 'review']);
      },
      error: () => {
        this.isEnding = false;
        this.errorMessage = 'Unable to end this session.';
      }
    });
  }

  statusTone(status: string): V2StatusTone {
    const normalized = status.toLowerCase();
    if (normalized === 'present') return 'success';
    if (normalized === 'late' || normalized === 'partial' || normalized === 'in_progress') return 'warning';
    if (normalized === 'absent' || normalized === 'requires_review') return 'danger';
    if (normalized === 'excused') return 'excused';
    if (normalized === 'on_break' || normalized === 'break_out' || normalized === 'break_in') return 'info';
    return 'neutral';
  }

  eventTone(eventType: string): V2StatusTone {
    if (eventType === 'time_in' || eventType === 'manual_attendance') return 'success';
    if (eventType === 'break_out' || eventType === 'break_in') return 'warning';
    if (eventType === 'time_out') return 'neutral';
    if (eventType.includes('failure') || eventType === 'false_recognition') return 'danger';
    return 'warning';
  }

  statusLabel(status: string): string {
    return status.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
  }

  studentDisplayStatus(student: V2StudentRecord): string {
    const lastEvent = this.lastStudentEvent(student.student_id);
    if (lastEvent?.event_type === 'break_out') return 'On Break';
    return this.statusLabel(student.final_status);
  }

  studentStatusTone(student: V2StudentRecord): V2StatusTone {
    const lastEvent = this.lastStudentEvent(student.student_id);
    if (lastEvent?.event_type === 'break_out') return 'info';
    return this.statusTone(student.final_status);
  }

  studentNameForEvent(event: V2AttendanceEvent): string {
    if (!event.student_id) return 'System Event';
    return this.roster.find((student) => student.student_id === event.student_id)?.student_name || 'Unknown Student';
  }

  initialsForStudent(student: V2StudentRecord): string {
    return student.student_name
      .split(/[,\s]+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join('') || 'ST';
  }

  lastEventLabel(student: V2StudentRecord): string {
    const event = this.lastStudentEvent(student.student_id);
    return event ? `${this.statusLabel(event.event_type)} at ${this.formatTime(event.event_time)}` : '-';
  }

  breakOutHistory(student: V2StudentRecord | null): string[] {
    if (!student) return [];
    return this.events
      .filter((event) => event.student_id === student.student_id && event.event_type === 'break_out')
      .map((event) => this.formatTime(event.event_time));
  }

  breakInHistory(student: V2StudentRecord | null): string[] {
    if (!student) return [];
    return this.events
      .filter((event) => event.student_id === student.student_id && event.event_type === 'break_in')
      .map((event) => this.formatTime(event.event_time));
  }

  studentEventLog(student: V2StudentRecord | null): Array<{ time: string; label: string }> {
    if (!student) return [];
    return this.events
      .filter((event) => event.student_id === student.student_id && !event.is_voided)
      .sort((a, b) => b.event_time.localeCompare(a.event_time))
      .map((event) => ({
        time: this.formatTime(event.event_time),
        label: this.eventLogLabel(event)
      }));
  }

  activeStudentBreakTimerLabel(student: V2StudentRecord | null): string {
    if (!student) return '';
    const lastEvent = this.lastStudentEvent(student.student_id);
    if (!lastEvent || lastEvent.event_type !== 'break_out') return '';

    const limit = this.breakLimitFromEvent(lastEvent) || this.normalizedStudentBreakLimit();
    const startedAt = new Date(lastEvent.event_time).getTime();
    if (!Number.isFinite(startedAt)) return '';

    const elapsedSeconds = Math.max(0, Math.floor((this.now.getTime() - startedAt) / 1000));
    const remainingSeconds = (limit * 60) - elapsedSeconds;
    if (remainingSeconds <= 0) {
      const overdueMinutes = Math.ceil(Math.abs(remainingSeconds) / 60);
      return `Overdue by ${overdueMinutes}m`;
    }

    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = remainingSeconds % 60;
    return `${minutes}:${String(seconds).padStart(2, '0')} remaining`;
  }

  isStudentOut(student: V2StudentRecord | null): boolean {
    if (!student) return false;
    return this.lastStudentEvent(student.student_id)?.event_type === 'break_out';
  }

  formatDateTime(value: string): string {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    }).format(new Date(value));
  }

  formatTime(value?: string | null): string {
    if (!value) return '-';
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit'
    }).format(new Date(value));
  }

  minutesLabel(minutes: number): string {
    const safe = Math.max(0, minutes || 0);
    const hours = Math.floor(safe / 60);
    const mins = safe % 60;
    return hours ? `${hours}h ${mins}m` : `${mins}m`;
  }

  private createStudentEvent(eventType: V2CreateEventRequest['event_type'], notes: string): void {
    if (!this.selectedStudent) {
      this.actionMessage = 'Select a student first.';
      return;
    }

    this.api.createV2SessionEvent(this.sessionId, {
      student_id: this.selectedStudent.student_id,
      event_type: eventType,
      event_source: 'manual_professor',
      notes
    }).subscribe({
      next: (detail) => {
        const selectedId = this.selectedStudent?.student_id;
        this.detail = detail;
        this.selectedStudent = this.roster.find((student) => student.student_id === selectedId) || null;
        this.actionMessage = `${this.statusLabel(eventType)} recorded for ${this.selectedStudent?.student_name || 'student'}.`;
      },
      error: () => {
        this.errorMessage = `Unable to record ${this.statusLabel(eventType)}.`;
      }
    });
  }

  private lastStudentEvent(studentId: number): V2AttendanceEvent | null {
    return this.events.find((event) => event.student_id === studentId && !event.is_voided) || null;
  }

  private countByStatus(status: string): number {
    return this.roster.filter((student) => student.final_status === status).length;
  }

  private controlsLockedByBreak(): boolean {
    if (!this.isBreakMode || this.breakUnlocked) return false;
    this.actionMessage = 'Session Break controls are locked. Professor unlock is required.';
    return true;
  }

  private enterBreakPreviewMode(): void {
    if (!this.detail) return;

    const nowIso = new Date().toISOString();
    const activeStudents = this.roster.filter((student) =>
      ['present', 'late', 'partial'].includes(student.final_status) || !!student.time_in
    );
    const previewStudents = activeStudents.length ? activeStudents : this.roster;
    const breakEvents: V2AttendanceEvent[] = previewStudents.map((student, index) => ({
      event_id: -1 - index,
      session_id: this.sessionId,
      record_id: student.record_id,
      student_id: student.student_id,
      event_type: 'break_out',
      event_time: nowIso,
      event_source: 'system',
      recognition_confidence: null,
      notes: 'Preview Session Break. Backend endpoint was not available.',
      is_voided: false
    }));

    this.detail = {
      ...this.detail,
      session: {
        ...this.detail.session,
        session_status: 'on_break'
      },
      events: [...this.detail.events, ...breakEvents]
    };
    this.breakPreviewMode = true;
    this.autoCaptureActive = true;
    this.breakUnlocked = false;
    this.breakUnlockPassword = '';
    this.breakUnlockError = '';
    this.errorMessage = '';
    this.actionMessage = 'Session Break preview mode is active because the backend break endpoint returned Not Found.';
  }

  private exitBreakPreviewMode(): void {
    if (!this.detail) return;
    this.detail = {
      ...this.detail,
      session: {
        ...this.detail.session,
        session_status: 'in_progress'
      },
      events: this.detail.events.filter((event) => event.event_id >= 0)
    };
    this.breakPreviewMode = false;
    this.breakUnlocked = false;
    this.autoCaptureActive = true;
    this.actionMessage = 'Session Break preview ended. Regular monitoring resumed.';
  }

  private apiErrorMessage(error: any, fallback: string): string {
    const detail = error?.error?.detail || error?.error?.message || error?.message;
    return detail ? `${fallback} ${detail}` : fallback;
  }

  private eventLogLabel(event: V2AttendanceEvent): string {
    const notes = (event.notes || '').trim();
    if (notes.toLowerCase().includes('bathroom break in')) return 'Bathroom Break In';
    if (notes.toLowerCase().includes('bathroom break out')) {
      const limit = this.breakLimitFromEvent(event);
      return limit ? `Bathroom Break Out (${limit}m)` : 'Bathroom Break Out';
    }
    if (event.event_type === 'time_in') return 'Time In';
    if (event.event_type === 'break_in') return 'Break In';
    if (event.event_type === 'break_out') return 'Break Out';
    if (event.event_type === 'time_out') return 'Time Out';
    if (event.event_type === 'manual_attendance') return 'Manual Attendance';
    if (event.event_type === 'manual_capture') return 'Manual Capture';
    return this.statusLabel(event.event_type);
  }

  private normalizedStudentBreakLimit(): number {
    return Math.min(120, Math.max(1, Math.round(Number(this.studentBreakLimitMinutes) || 10)));
  }

  private breakLimitFromEvent(event: V2AttendanceEvent): number | null {
    const match = (event.notes || '').match(/limit:\s*(\d+)\s*minutes?/i);
    if (!match) return null;
    const value = Number(match[1]);
    return Number.isFinite(value) ? value : null;
  }

  private findClassInfo(schedule: V2ProfessorScheduleResponse, classId: number): V2ProfessorScheduleClass | null {
    return schedule.classes.find((classItem) => classItem.class_id === classId) || null;
  }

  private handleKeyDown = (event: KeyboardEvent): void => {
    if (event.code !== 'Space' || event.repeat) return;
    const target = event.target as HTMLElement | null;
    if (target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return;
    event.preventDefault();
    this.manualCapture();
  };
}
