import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { ApiService } from '../../../api.service';
import { V2ClassRosterResponse, V2ClassRosterStudent, V2FaceProfileStatus, V2RecognitionStatus } from '../../models/v2-attendance.models';
import { V2StatusTone } from '../../components';

@Component({
  selector: 'app-v2-class-roster',
  templateUrl: './class-roster.component.html',
  styleUrls: ['./class-roster.component.scss']
})
export class V2ClassRosterComponent implements OnInit {
  classId = 0;
  roster: V2ClassRosterResponse | null = null;
  selectedStudent: V2ClassRosterStudent | null = null;
  searchTerm = '';
  isLoading = false;
  errorMessage = '';

  constructor(
    private api: ApiService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.classId = Number(this.route.snapshot.paramMap.get('classId')) || 0;
    this.loadRoster();
  }

  loadRoster(): void {
    if (!this.classId) {
      this.errorMessage = 'Class roster route is missing a class id.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.api.getV2ClassRoster(this.classId).subscribe({
      next: (data) => {
        this.roster = data;
        this.selectedStudent = data.students[0] || null;
        this.isLoading = false;
      },
      error: () => {
        this.errorMessage = 'Unable to load the class roster.';
        this.isLoading = false;
      }
    });
  }

  get filteredStudents(): V2ClassRosterStudent[] {
    const students = this.roster?.students || [];
    const query = this.searchTerm.trim().toLowerCase();
    if (!query) return students;
    return students.filter((student) =>
      student.student_name.toLowerCase().includes(query) ||
      student.student_number.toLowerCase().includes(query) ||
      (student.email || '').toLowerCase().includes(query)
    );
  }

  get registeredFaceCount(): number {
    return (this.roster?.students || []).filter((student) => student.face_profile_status !== 'no_face_profile').length;
  }

  get averageAttendanceRate(): number {
    const students = this.roster?.students || [];
    if (!students.length) return 0;
    const total = students.reduce((sum, student) => sum + student.attendance_rate, 0);
    return Math.round((total / students.length) * 10) / 10;
  }

  selectStudent(student: V2ClassRosterStudent): void {
    this.selectedStudent = student;
  }

  manageFaceData(student: V2ClassRosterStudent | null = this.selectedStudent): void {
    if (!student) return;
    this.router.navigate(['/v2/classes', this.classId, 'students', student.student_id, 'face-profile']);
  }

  backToClasses(): void {
    this.router.navigate(['/v2/classes']);
  }

  initials(student: V2ClassRosterStudent): string {
    const parts = student.student_name.replace(',', '').split(' ').filter(Boolean);
    return parts.slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'ST';
  }

  formatDate(value?: string | null): string {
    if (!value) return 'No update yet';
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(new Date(value));
  }

  formatHistoryDate(value: string): string {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric'
    }).format(new Date(`${value}T00:00:00`));
  }

  faceStatusLabel(status: V2FaceProfileStatus): string {
    const labels: Record<V2FaceProfileStatus, string> = {
      registered: 'Registered',
      needs_update: 'Needs Update',
      no_face_profile: 'No Face Profile'
    };
    return labels[status];
  }

  recognitionStatusLabel(status: V2RecognitionStatus): string {
    const labels: Record<V2RecognitionStatus, string> = {
      active: 'Active',
      low_confidence: 'Low Confidence',
      not_recognized_recently: 'Not Recognized Recently',
      not_available: 'Not Available'
    };
    return labels[status];
  }

  faceTone(status: V2FaceProfileStatus): V2StatusTone {
    if (status === 'registered') return 'success';
    if (status === 'needs_update') return 'warning';
    return 'danger';
  }

  recognitionTone(status: V2RecognitionStatus): V2StatusTone {
    if (status === 'active') return 'success';
    if (status === 'low_confidence') return 'warning';
    if (status === 'not_recognized_recently') return 'info';
    return 'neutral';
  }

  statusTone(status: string): V2StatusTone {
    if (status === 'present') return 'success';
    if (status === 'late') return 'warning';
    if (status === 'excused') return 'excused';
    return 'danger';
  }

  statusLabel(status: string): string {
    return status.replace('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
  }
}
