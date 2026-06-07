import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { ApiService } from '../../../api.service';
import { V2StatusTone } from '../../components';
import { V2StudentClassHistoryRecord, V2StudentClassHistoryResponse } from '../../models/v2-attendance.models';

type StatusFilter = 'all' | 'present' | 'late' | 'partial' | 'absent' | 'excused';
type AssessmentFilter = 'all' | 'valid_presence' | 'attendance_warning' | 'requires_review' | 'absent';

@Component({
  selector: 'app-v2-student-class-history',
  templateUrl: './student-class-history.component.html',
  styleUrls: ['./student-class-history.component.scss']
})
export class V2StudentClassHistoryComponent implements OnInit {
  classId = 0;
  studentId = 0;
  history: V2StudentClassHistoryResponse | null = null;
  isLoading = true;
  errorMessage = '';

  filterStartDate = '';
  filterEndDate = '';
  statusFilter: StatusFilter = 'all';
  assessmentFilter: AssessmentFilter = 'all';
  applied = {
    start: '',
    end: '',
    status: 'all' as StatusFilter,
    assessment: 'all' as AssessmentFilter
  };

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {}

  ngOnInit(): void {
    this.classId = Number(this.route.snapshot.paramMap.get('classId')) || 0;
    this.studentId = Number(this.route.snapshot.paramMap.get('studentId')) || 0;
    this.loadHistory();
  }

  loadHistory(): void {
    if (!this.classId || !this.studentId) {
      this.errorMessage = 'Open Student Attendance History from a specific class roster student.';
      this.isLoading = false;
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.api.getV2StudentClassHistory(this.classId, this.studentId).subscribe({
      next: (history) => {
        this.history = history;
        this.isLoading = false;
      },
      error: () => {
        this.errorMessage = 'Unable to load student attendance history.';
        this.isLoading = false;
      }
    });
  }

  get header() {
    return this.history?.header || null;
  }

  get summary() {
    return this.history?.summary || null;
  }

  get filteredRecords(): V2StudentClassHistoryRecord[] {
    let rows = [...(this.history?.records || [])];
    if (this.applied.start) {
      rows = rows.filter((row) => row.session_date >= this.applied.start);
    }
    if (this.applied.end) {
      rows = rows.filter((row) => row.session_date <= this.applied.end);
    }
    if (this.applied.status !== 'all') {
      rows = rows.filter((row) => row.attendance_status === this.applied.status);
    }
    if (this.applied.assessment !== 'all') {
      rows = rows.filter((row) => row.system_assessment === this.applied.assessment);
    }
    return rows;
  }

  applyFilters(): void {
    this.applied = {
      start: this.filterStartDate,
      end: this.filterEndDate,
      status: this.statusFilter,
      assessment: this.assessmentFilter
    };
  }

  clearFilters(): void {
    this.filterStartDate = '';
    this.filterEndDate = '';
    this.statusFilter = 'all';
    this.assessmentFilter = 'all';
    this.applyFilters();
  }

  viewSessionEvidence(row: V2StudentClassHistoryRecord): void {
    this.router.navigate(['/student-evidence', row.session_id, this.studentId]);
  }

  backToRoster(): void {
    this.router.navigate(['/v2/classes', this.classId, 'students']);
  }

  studentInitials(name: string): string {
    const parts = name.replace(',', '').split(' ').filter(Boolean);
    return parts.slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'ST';
  }

  statusTone(status: string): V2StatusTone {
    if (status === 'present') return 'success';
    if (status === 'late' || status === 'partial') return 'warning';
    if (status === 'excused') return 'excused';
    return 'danger';
  }

  assessmentTone(assessment: string): V2StatusTone {
    if (assessment === 'valid_presence') return 'success';
    if (assessment === 'attendance_warning') return 'warning';
    if (assessment === 'requires_review') return 'danger';
    return 'neutral';
  }

  statusLabel(status: string): string {
    return status.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
  }

  assessmentLabel(assessment: string): string {
    const labels: Record<string, string> = {
      valid_presence: 'Valid Presence',
      attendance_warning: 'Attendance Warning',
      requires_review: 'Requires Review',
      absent: 'Absent'
    };
    return labels[assessment] || this.statusLabel(assessment);
  }

  formatDate(value: string): string {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(new Date(`${value}T00:00:00`));
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
