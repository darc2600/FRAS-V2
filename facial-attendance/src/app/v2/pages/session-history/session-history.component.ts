import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../../api.service';
import { AuthService } from '../../../auth.service';
import { V2HistorySessionStatus, V2SessionHistoryResponse } from '../../models/v2-attendance.models';
import { V2StatusTone } from '../../components';

type HistoryRow = V2SessionHistoryResponse['sessions'][number];
type ReviewFilter = 'all' | 'review' | 'clean';
type StatusFilter = 'all' | V2HistorySessionStatus;
type RateFilter = 'all' | 'below80' | '80to90' | 'above90';

@Component({
  selector: 'app-v2-session-history',
  templateUrl: './session-history.component.html',
  styleUrls: ['./session-history.component.scss']
})
export class V2SessionHistoryComponent implements OnInit {
  classId = 0;
  professorId = 0;
  professorName = '';
  history: V2SessionHistoryResponse | null = null;
  isLoading = true;
  errorMessage = '';
  filterStartDate = '';
  filterEndDate = '';
  rateFilter: RateFilter = 'all';
  statusFilter: StatusFilter = 'all';
  reviewFilter: ReviewFilter = 'all';
  applied = {
    start: '',
    end: '',
    rate: 'all' as RateFilter,
    status: 'all' as StatusFilter,
    review: 'all' as ReviewFilter,
  };

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.classId = Number(
      this.route.snapshot.paramMap.get('classId') ||
      this.route.parent?.snapshot.paramMap.get('classId') ||
      0
    );
    this.loadHistory();
  }

  loadHistory(): void {
    this.isLoading = true;
    this.errorMessage = '';

    if (!this.classId) {
      this.loadProfessorHistory();
      return;
    }

    this.api.getV2ClassSessionHistory(this.classId).subscribe({
      next: (history) => {
        this.history = history;
        this.isLoading = false;
      },
      error: () => {
        this.errorMessage = 'Unable to load session history.';
        this.isLoading = false;
      }
    });
  }

  loadProfessorHistory(): void {
    const currentUser = this.authService.getCurrentUser();
    if (!currentUser) {
      this.errorMessage = 'Login as an instructor to view session history.';
      this.isLoading = false;
      return;
    }

    this.api.getV2Professors().subscribe({
      next: (professors) => {
        const matchedProfessor = professors.find((professor) => professor.user_id === currentUser.userId);
        if (!matchedProfessor) {
          this.errorMessage = 'No professor profile is linked to this account.';
          this.isLoading = false;
          return;
        }

        this.professorId = matchedProfessor.professor_id;
        this.professorName = matchedProfessor.professor_name;
        this.api.getV2ProfessorSessionHistory(this.professorId).subscribe({
          next: (history) => {
            this.history = history;
            this.isLoading = false;
          },
          error: () => {
            this.errorMessage = 'Unable to load professor session history.';
            this.isLoading = false;
          }
        });
      },
      error: () => {
        this.errorMessage = 'Unable to load professor profile.';
        this.isLoading = false;
      }
    });
  }

  get context() {
    return this.history?.class_context || null;
  }

  get summary() {
    return this.history?.summary || null;
  }

  get isProfessorWideHistory(): boolean {
    return !this.classId;
  }

  get filteredSessions(): HistoryRow[] {
    let rows = [...(this.history?.sessions || [])];
    if (this.applied.start) {
      rows = rows.filter((row) => row.date >= this.applied.start);
    }
    if (this.applied.end) {
      rows = rows.filter((row) => row.date <= this.applied.end);
    }
    if (this.applied.rate === 'below80') {
      rows = rows.filter((row) => row.attendance_rate < 80);
    } else if (this.applied.rate === '80to90') {
      rows = rows.filter((row) => row.attendance_rate >= 80 && row.attendance_rate <= 90);
    } else if (this.applied.rate === 'above90') {
      rows = rows.filter((row) => row.attendance_rate > 90);
    }
    if (this.applied.status !== 'all') {
      rows = rows.filter((row) => row.status === this.applied.status);
    }
    if (this.applied.review === 'review') {
      rows = rows.filter((row) => row.warning_count > 0 || row.status === 'needs_review');
    } else if (this.applied.review === 'clean') {
      rows = rows.filter((row) => row.warning_count === 0 && row.status !== 'needs_review');
    }
    return rows;
  }

  applyFilters(): void {
    this.applied = {
      start: this.filterStartDate,
      end: this.filterEndDate,
      rate: this.rateFilter,
      status: this.statusFilter,
      review: this.reviewFilter,
    };
  }

  viewSessionSummary(row: HistoryRow): void {
    this.router.navigate(['/session-review', row.session_id]);
  }

  exportFullHistory(): void {
    const headers = this.isProfessorWideHistory
      ? ['Course', 'Section', 'Room', 'Date', 'Start', 'End', 'Attendance Count', 'Total Students', 'Attendance Rate', 'Average Presence Minutes', 'Warnings', 'Excused', 'Status']
      : ['Date', 'Start', 'End', 'Attendance Count', 'Total Students', 'Attendance Rate', 'Average Presence Minutes', 'Warnings', 'Excused', 'Status'];
    const rows = [
      headers,
      ...this.filteredSessions.map((row) => {
        const base = [
        this.formatDate(row.date),
        this.formatTime(row.scheduled_start),
        this.formatTime(row.scheduled_end),
        String(row.attendance_count),
        String(row.total_students),
        `${row.attendance_rate}%`,
        String(row.average_presence_minutes),
        String(row.warning_count),
        String(row.excused_count),
        this.statusLabel(row.status)
        ];
        return this.isProfessorWideHistory
          ? [row.course_code || '-', row.section || '-', row.room || '-', ...base]
          : base;
      })
    ];
    const csv = rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = this.isProfessorWideHistory ? 'fras-professor-session-history.csv' : 'fras-class-session-history.csv';
    link.click();
    URL.revokeObjectURL(link.href);
  }

  classLabel(row: HistoryRow): string {
    const section = row.section ? ` - ${row.section}` : '';
    return `${row.course_code || 'Course'}${section}`;
  }

  statusTone(status: V2HistorySessionStatus): V2StatusTone {
    if (status === 'completed') return 'success';
    if (status === 'needs_review') return 'danger';
    return 'warning';
  }

  statusLabel(status: string): string {
    return status.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
  }

  formatDate(value: string): string {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(new Date(`${value}T00:00:00`));
  }

  formatDay(value: string): string {
    return new Intl.DateTimeFormat('en-US', { weekday: 'long' }).format(new Date(`${value}T00:00:00`));
  }

  formatTime(value: string): string {
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
}
