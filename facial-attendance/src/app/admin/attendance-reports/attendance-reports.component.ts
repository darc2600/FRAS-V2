import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../api.service';
import { HttpClientModule } from '@angular/common/http';

interface AttendanceRecord {
  student_id: string;
  student_name: string;
  date: string;
  time_in: string;
  status: string;
}

interface ClassSummary {
  total_students: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  excused_count: number;
  attendance_percentage: number;
  needs_attention: string[];
}

interface AttendanceReport {
  report_title: string;
  generated_at: string;
  exported_by: string;
  date_range: string;
  records: AttendanceRecord[];
  class_summary: ClassSummary;
}

interface ProfessorReport {
  professor_name: string;
  generated_at: string;
  exported_by: string;
  date_range: string;
  classes: AttendanceReport[];
  consolidated_summary: ClassSummary;
}

@Component({
  selector: 'app-attendance-reports',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HttpClientModule],
  templateUrl: './attendance-reports.component.html',
  styleUrl: './attendance-reports.component.css'
})
export class AttendanceReportsComponent implements OnInit {
  reportForm: FormGroup;
  isLoading = false;
  reportData: AttendanceReport | ProfessorReport | null = null;
  studentList: any[] = [];
  myClasses: any[] = [];
  instructorList: string[] = [];
  showAdvanced: boolean = false;
  exportFormats = [
    { value: 'json', label: 'JSON' },
    { value: 'csv', label: 'CSV' },
    { value: 'excel', label: 'Excel' },
    { value: 'pdf', label: 'PDF' }
  ];

  statusOptions = [
    { value: 'Present', label: 'Present' },
    { value: 'Absent', label: 'Absent' },
    { value: 'Late', label: 'Late' },
    { value: 'Excused', label: 'Excused' }
  ];

  reportTypes = [
    { value: 'class', label: 'Class Report' },
    { value: 'professor', label: 'Professor Report' }
  ];

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService
  ) {
    this.reportForm = this.fb.group({
      reportType: ['class', Validators.required],
      classId: [''],
      dateFrom: [''],
      dateTo: [''],
        studentId: [''],
        studentIds: [''],
      statusFilter: [[]],
      courseCode: [''],
      section: [''],
      instructorId: [''],
        professorName: [''],
      exportFormat: ['json', Validators.required]
    });
  }

  ngOnInit(): void {
    // Set default date range to current month
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

    this.reportForm.patchValue({
      dateFrom: firstDay.toISOString().split('T')[0],
      dateTo: lastDay.toISOString().split('T')[0]
    });

    // Load students for dropdown
    this.loadStudents();
    // Load classes for dropdown
    this.loadClasses();
    // Load professors for professor report dropdown
    this.loadInstructors();
  }

  loadStudents(): void {
    this.apiService.getStudents().subscribe({
      next: (students: any[]) => {
        this.studentList = students;
      },
      error: (error: any) => {
        console.error('Error loading students:', error);
      }
    });
  }

  loadClasses(): void {
    console.log('Loading classes...');
    this.apiService.getClasses().subscribe({
      next: (classes: any[]) => {
        console.log('Classes loaded:', classes);
        this.myClasses = classes;
      },
      error: (error: any) => {
        console.error('Error loading classes:', error);
      }
    });
  }

  loadInstructors(): void {
    this.apiService.getInstructors().subscribe({
      next: (instructors: string[]) => {
        this.instructorList = instructors;
      },
      error: (error: any) => {
        console.error('Error loading instructors:', error);
      }
    });
  }

  get recordsGroupedByDate(): { date: string; records: AttendanceRecord[] }[] {
    if (!this.reportData || this.isProfessorReport(this.reportData)) {
      return [];
    }

    const grouped = new Map<string, AttendanceRecord[]>();
    for (const record of this.reportData.records) {
      if (!grouped.has(record.date)) {
        grouped.set(record.date, []);
      }
      grouped.get(record.date)!.push(record);
    }

    return Array.from(grouped.entries())
      .map(([date, records]) => ({ date, records }))
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }

  get requiresClassSelection(): boolean {
    return this.reportForm.get('reportType')?.value === 'class';
  }

  get isClassReportType(): boolean {
    return this.reportForm.get('reportType')?.value === 'class';
  }

  get isProfessorReportType(): boolean {
    return this.reportForm.get('reportType')?.value === 'professor';
  }

  get filteredProfessorClasses(): any[] {
    const selectedProfessor = this.reportForm.get('professorName')?.value;
    if (!selectedProfessor) {
      return [];
    }

    return this.myClasses.filter((classItem: any) =>
      classItem?.instructor_name === selectedProfessor
    );
  }

  onReportTypeChange(): void {
    if (this.isProfessorReportType) {
      this.reportForm.patchValue({
        classId: '',
        studentId: '',
        studentIds: ''
      });
    } else {
      this.reportForm.patchValue({
        instructorId: '',
        professorName: ''
      });
    }
  }

  onProfessorSelectionChange(): void {
    this.reportForm.patchValue({ classId: '' });
  }

  isStatusSelected(status: string): boolean {
    const selected: string[] = this.reportForm.get('statusFilter')?.value || [];
    return selected.includes(status);
  }

  onStatusToggle(status: string, checked: boolean): void {
    const selected: string[] = [...(this.reportForm.get('statusFilter')?.value || [])];
    const statusIndex = selected.indexOf(status);

    if (checked && statusIndex === -1) {
      selected.push(status);
    }

    if (!checked && statusIndex !== -1) {
      selected.splice(statusIndex, 1);
    }

    this.reportForm.patchValue({ statusFilter: selected });
  }

  onSubmit(): void {
    if (this.reportForm.valid) {
      this.generateReport();
    }
  }

  generateReport(): void {
    this.isLoading = true;
    this.reportData = null;

    const formValue = this.reportForm.value;
    const selectedClass = this.getSelectedClass(formValue.classId);
    const requestData: any = {
      dateFrom: formValue.dateFrom || undefined,
      dateTo: formValue.dateTo || undefined,
      classId: formValue.classId ? parseInt(formValue.classId, 10) : undefined,
      // Support either single student selection or comma-separated list
      studentIds: formValue.studentId ? [parseInt(formValue.studentId)] : (formValue.studentIds ? formValue.studentIds.split(',').map((id: string) => parseInt(id.trim())) : undefined),
      statusFilter: formValue.statusFilter.length > 0 ? formValue.statusFilter : undefined,
      courseCode: formValue.courseCode || selectedClass?.course_code || selectedClass?.courseCode || undefined,
      section: formValue.section || selectedClass?.section || undefined,
      instructorId: formValue.instructorId ? parseInt(formValue.instructorId) : (selectedClass?.instructor_id || selectedClass?.instructorId || undefined),
      professorName: formValue.professorName || undefined,
      exportFormat: formValue.exportFormat
    };

    // Client-side validation for professor reports (prevent accidental empty requests)
    if (formValue.reportType === 'professor' && !requestData.instructorId && !requestData.professorName) {
      this.isLoading = false;
      alert('Please provide either Instructor ID or Professor name when generating a Professor report.');
      return;
    }

    // Remove undefined values
    Object.keys(requestData).forEach((key: string) => {
      if (requestData[key] === undefined) {
        delete requestData[key];
      }
    });

    const endpoint = formValue.reportType === 'professor'
      ? '/api/admin/attendance/export/professor'
      : '/api/admin/attendance/export';

    if (formValue.exportFormat === 'json') {
      // For JSON responses, display in UI
      this.apiService.post(endpoint, requestData).subscribe({
        next: (response: any) => {
          this.reportData = response;
          this.isLoading = false;
        },
        error: (error: any) => {
          console.error('Error generating report:', error);
          this.isLoading = false;
          alert('Error generating report: ' + (error.error?.detail || error.message));
        }
      });
    } else {
      // For file downloads
      console.log('Attempting file download with format:', formValue.exportFormat);
      this.apiService.postBlob(endpoint, requestData).subscribe({
        next: (blob: Blob) => {
          console.log('Blob received, size:', blob.size, 'type:', blob.type);
          this.downloadFile(blob, formValue.exportFormat);
          this.isLoading = false;
        },
        error: (error: any) => {
          console.error('Error generating report:', error);
          this.isLoading = false;
          alert('Error generating report: ' + (error.error?.detail || error.message));
        }
      });
    }
  }

  private downloadFile(blob: Blob, format: string): void {
    try {
      console.log('DownloadFile called with format:', format, 'blob size:', blob.size);

      if (blob.size === 0) {
        alert('The exported file is empty. Please check your filters and try again.');
        return;
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.style.display = 'none';

      let filename = 'attendance_report';
      switch (format.toLowerCase()) {
        case 'csv':
          filename += '.csv';
          break;
        case 'excel':
          filename += '.xlsx';
          break;
        case 'pdf':
          filename += '.pdf';
          break;
        default:
          filename += '.txt';
      }
      a.download = filename;

      console.log('Creating download link for:', filename);

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      console.log('File download initiated');
    } catch (error) {
      console.error('Error in downloadFile:', error);
      alert('Error downloading file: ' + error);
    }
  }

  isProfessorReport(data: AttendanceReport | ProfessorReport): data is ProfessorReport {
    return 'classes' in data;
  }

  getStatusBadgeClass(status: string): string {
    switch (status.toLowerCase()) {
      case 'present': return 'badge-success';
      case 'absent': return 'badge-danger';
      case 'late': return 'badge-warning';
      case 'excused': return 'badge-info';
      default: return 'badge-secondary';
    }
  }

  clearForm(): void {
    this.reportData = null;
    // Reset to default values
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

    this.reportForm.reset({
      reportType: 'class',
      dateFrom: firstDay.toISOString().split('T')[0],
      dateTo: lastDay.toISOString().split('T')[0],
      studentIds: '',
      statusFilter: [],
      courseCode: '',
      section: '',
      instructorId: '',
      professorName: '',
      exportFormat: 'json'
    });
  }

  exportCurrentReport(format: string): void {
    if (!this.reportData) return;

    // Create a temporary form data for export
    const exportData: any = {
      exportFormat: format
    };

    // Copy current filter values
    const formValue = this.reportForm.value;
    if (formValue.dateFrom) exportData.dateFrom = formValue.dateFrom;
    if (formValue.dateTo) exportData.dateTo = formValue.dateTo;
    const selectedClass = this.getSelectedClass(formValue.classId);
    if (formValue.classId) exportData.classId = parseInt(formValue.classId, 10);
    if (formValue.studentIds) exportData.studentIds = formValue.studentIds.split(',').map((id: string) => parseInt(id.trim()));
    if (formValue.studentId) exportData.studentIds = [parseInt(formValue.studentId)];
    if (formValue.statusFilter.length > 0) exportData.statusFilter = formValue.statusFilter;
    if (formValue.courseCode || selectedClass?.course_code || selectedClass?.courseCode) {
      exportData.courseCode = formValue.courseCode || selectedClass?.course_code || selectedClass?.courseCode;
    }
    if (formValue.section || selectedClass?.section) {
      exportData.section = formValue.section || selectedClass?.section;
    }
    if (formValue.instructorId || selectedClass?.instructor_id || selectedClass?.instructorId) {
      exportData.instructorId = formValue.instructorId
        ? parseInt(formValue.instructorId)
        : (selectedClass?.instructor_id || selectedClass?.instructorId);
    }
    if (formValue.professorName) exportData.professorName = formValue.professorName;

    const endpoint = formValue.reportType === 'professor'
      ? '/api/admin/attendance/export/professor'
      : '/api/admin/attendance/export';

    this.apiService.postBlob(endpoint, exportData).subscribe({
      next: (blob: Blob) => {
        this.downloadFile(blob, format);
      },
      error: (error: any) => {
        console.error('Error exporting report:', error);
        alert('Error exporting report: ' + (error.error?.detail || error.message));
      }
    });
  }

  viewClassDetails(classReport: AttendanceReport): void {
    // For now, just show an alert with class details
    // In a real app, you might open a modal or navigate to a detail view
    alert(`Class: ${classReport.report_title}\nRecords: ${classReport.records.length}\nAttendance Rate: ${classReport.class_summary.attendance_percentage}%`);
  }

  private getSelectedClass(classId: string | number | undefined): any | undefined {
    if (!classId) {
      return undefined;
    }

    const classIdNumber = typeof classId === 'number' ? classId : parseInt(classId, 10);
    if (Number.isNaN(classIdNumber)) {
      return undefined;
    }

    return this.myClasses.find((classItem: any) => {
      const candidateId = classItem?.id ?? classItem?.class_id;
      return Number(candidateId) === classIdNumber;
    });
  }
}
