import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../../api.service';
import {
  V2ManualAttendanceStatus,
  V2ProfessorScheduleClass,
  V2SessionReviewResponse,
  V2StudentRecord
} from '../../models/v2-attendance.models';
import { V2StatusTone } from '../../components';

@Component({
  selector: 'app-v2-post-session-review',
  templateUrl: './post-session-review.component.html',
  styleUrls: ['./post-session-review.component.scss']
})
export class V2PostSessionReviewComponent implements OnInit {
  sessionId = 0;
  review: V2SessionReviewResponse | null = null;
  classInfo: V2ProfessorScheduleClass | null = null;
  searchQuery = '';
  isLoading = true;
  isSaving = false;
  isFinalizing = false;
  errorMessage = '';
  actionMessage = '';
  overrideMode = false;
  overrideSelections: Record<number, V2ManualAttendanceStatus> = {};

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {}

  ngOnInit(): void {
    this.sessionId = Number(this.route.snapshot.paramMap.get('sessionId') || 0);
    this.loadReview();
  }

  loadReview(): void {
    if (!this.sessionId) {
      this.errorMessage = 'Missing session id.';
      this.isLoading = false;
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.api.getV2SessionReview(this.sessionId).subscribe({
      next: (review) => {
        this.review = review;
        this.loadClassInfo(review.session.professor_id, review.session.class_id);
      },
      error: () => {
        this.errorMessage = 'Unable to load post-session review.';
        this.isLoading = false;
      }
    });
  }

  get session() {
    return this.review?.session || null;
  }

  get summary() {
    return this.review?.summary || null;
  }

  get roster(): V2StudentRecord[] {
    return this.review?.roster || [];
  }

  get filteredRoster(): V2StudentRecord[] {
    const query = this.searchQuery.trim().toLowerCase();
    if (!query) return this.roster;
    return this.roster.filter((student) =>
      student.student_name.toLowerCase().includes(query) ||
      student.student_number.toLowerCase().includes(query) ||
      student.final_status.toLowerCase().includes(query) ||
      student.system_assessment.toLowerCase().includes(query)
    );
  }

  get isFinalized(): boolean {
    return this.session?.session_status === 'finalized';
  }

  get validationRateLabel(): string {
    return `${this.summary?.presence_validation_rate ?? 0}%`;
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

  viewDetails(student: V2StudentRecord): void {
    this.router.navigate(['/student-evidence', this.sessionId, student.student_id]);
  }

  beginOverrideMode(): void {
    if (this.isFinalized) return;
    this.overrideSelections = {};
    for (const student of this.roster) {
      this.overrideSelections[student.record_id] = this.normalizeManualStatus(student.final_status);
    }
    this.overrideMode = true;
  }

  cancelOverrideMode(): void {
    if (this.isSaving) return;
    this.overrideMode = false;
    this.overrideSelections = {};
  }

  setOverrideStatus(student: V2StudentRecord, status: V2ManualAttendanceStatus): void {
    this.overrideSelections[student.record_id] = status;
  }

  overrideStatusFor(student: V2StudentRecord): V2ManualAttendanceStatus {
    return this.overrideSelections[student.record_id] || this.normalizeManualStatus(student.final_status);
  }

  setVisibleOverrideStatus(status: V2ManualAttendanceStatus): void {
    for (const student of this.filteredRoster) {
      this.overrideSelections[student.record_id] = status;
    }
  }

  get overrideChangeCount(): number {
    return this.changedOverrideRecords.length;
  }

  saveOverrideChanges(): void {
    if (!this.session || this.isSaving || this.isFinalized) return;
    const records = this.changedOverrideRecords.map((student) => ({
      record_id: student.record_id,
      student_id: student.student_id,
      status: this.overrideStatusFor(student)
    }));

    if (!records.length) {
      this.actionMessage = 'No override changes to save.';
      this.cancelOverrideMode();
      return;
    }

    this.isSaving = true;
    this.errorMessage = '';
    this.api.saveV2ManualAttendance(this.sessionId, {
      professor_id: this.session.professor_id,
      records,
      notes: 'Saved from post-session override mode.'
    }).subscribe({
      next: () => {
        this.isSaving = false;
        this.overrideMode = false;
        this.overrideSelections = {};
        this.actionMessage = `${records.length} attendance override${records.length === 1 ? '' : 's'} saved.`;
        this.loadReview();
      },
      error: () => {
        this.isSaving = false;
        this.errorMessage = 'Unable to save attendance overrides.';
      }
    });
  }

  finalizeAttendance(): void {
    if (!this.sessionId || this.isFinalizing || this.isFinalized) return;
    this.isFinalizing = true;
    this.errorMessage = '';
    this.api.finalizeV2Session(this.sessionId).subscribe({
      next: (review) => {
        this.review = review;
        this.isFinalizing = false;
        this.actionMessage = 'Attendance finalized. Blackboard CSV export is now available.';
      },
      error: () => {
        this.isFinalizing = false;
        this.errorMessage = 'Unable to finalize attendance.';
      }
    });
  }

  exportLogs(): void {
    this.downloadCsv('fras-session-review-log.csv', this.buildCsvRows(false));
  }

  exportBlackboardCsv(): void {
    if (!this.isFinalized) return;
    this.downloadCsv('fras-blackboard-attendance.csv', this.buildCsvRows(true));
  }

  goToHistory(): void {
    if (this.session?.class_id) {
      this.router.navigate(['/classes', this.session.class_id, 'session-history']);
      return;
    }
    this.router.navigate(['/session-history']);
  }

  statusTone(status: string): V2StatusTone {
    const normalized = status.toLowerCase();
    if (normalized === 'present') return 'success';
    if (normalized === 'late' || normalized === 'partial') return 'warning';
    if (normalized === 'absent') return 'danger';
    if (normalized === 'excused') return 'excused';
    return 'neutral';
  }

  assessmentClass(assessment: string): string {
    const normalized = assessment.toLowerCase();
    if (normalized === 'valid_presence') return 'valid';
    if (normalized === 'attendance_warning') return 'warning';
    if (normalized === 'requires_review') return 'review';
    return 'absent';
  }

  assessmentLabel(assessment: string): string {
    return this.statusLabel(assessment);
  }

  statusLabel(status: string): string {
    return (status || '-').replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
  }

  initialsForStudent(student: V2StudentRecord): string {
    return student.student_name
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
    forkJoin({
      schedule: this.api.getV2ProfessorSchedule(professorId)
    }).subscribe({
      next: ({ schedule }) => {
        this.classInfo = schedule.classes.find((item) => item.class_id === classId) || null;
        this.isLoading = false;
      },
      error: () => {
        this.classInfo = null;
        this.isLoading = false;
      }
    });
  }

  private get changedOverrideRecords(): V2StudentRecord[] {
    return this.roster.filter((student) =>
      this.overrideStatusFor(student) !== this.normalizeManualStatus(student.final_status)
    );
  }

  private normalizeManualStatus(status: string): V2ManualAttendanceStatus {
    if (status === 'present' || status === 'absent' || status === 'late' || status === 'excused') {
      return status;
    }
    return 'present';
  }

  private buildCsvRows(blackboardOnly: boolean): string[][] {
    const header = blackboardOnly
      ? ['Student Number', 'Student Name', 'Attendance Status']
      : ['Student Number', 'Student Name', 'Status', 'Presence Minutes', 'Outside Minutes', 'Break Count', 'System Assessment'];

    const rows = this.roster.map((student) => blackboardOnly
      ? [student.student_number, student.student_name, this.statusLabel(student.final_status)]
      : [
          student.student_number,
          student.student_name,
          this.statusLabel(student.final_status),
          String(student.total_presence_minutes),
          String(student.total_outside_minutes),
          String(student.break_count),
          this.statusLabel(student.system_assessment)
        ]);
    return [header, ...rows];
  }

  private downloadCsv(filename: string, rows: string[][]): void {
    const csv = rows
      .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }
}
