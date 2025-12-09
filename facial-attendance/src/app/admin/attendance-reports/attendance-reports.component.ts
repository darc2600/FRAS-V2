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
      studentIds: [''],
      statusFilter: [[]],
      courseCode: [''],
      section: [''],
      instructorId: [''],
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

  onReportTypeChange(): void {
    // Clear class selection when switching report types
    if (!this.requiresClassSelection) {
      this.reportForm.patchValue({ classId: '' });
    }
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
    const requestData: any = {
      date_from: formValue.dateFrom || undefined,
      date_to: formValue.dateTo || undefined,
      class_id: formValue.classId ? parseInt(formValue.classId) : undefined,
      student_ids: formValue.studentIds ? formValue.studentIds.split(',').map((id: string) => parseInt(id.trim())) : undefined,
      status_filter: formValue.statusFilter.length > 0 ? formValue.statusFilter : undefined,
      course_code: formValue.courseCode || undefined,
      section: formValue.section || undefined,
      instructor_id: formValue.instructorId ? parseInt(formValue.instructorId) : undefined,
      export_format: formValue.exportFormat
    };

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
      exportFormat: 'json'
    });
  }

  exportCurrentReport(format: string): void {
    if (!this.reportData) return;

    // Create a temporary form data for export
    const exportData: any = {
      export_format: format
    };

    // Copy current filter values
    const formValue = this.reportForm.value;
    if (formValue.dateFrom) exportData.date_from = formValue.dateFrom;
    if (formValue.dateTo) exportData.date_to = formValue.dateTo;
    if (formValue.classId) exportData.class_id = parseInt(formValue.classId);
    if (formValue.studentIds) exportData.student_ids = formValue.studentIds.split(',').map((id: string) => parseInt(id.trim()));
    if (formValue.statusFilter.length > 0) exportData.status_filter = formValue.statusFilter;
    if (formValue.courseCode) exportData.course_code = formValue.courseCode;
    if (formValue.section) exportData.section = formValue.section;
    if (formValue.instructorId) exportData.instructor_id = parseInt(formValue.instructorId);

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
}
