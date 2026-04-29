import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { finalize } from 'rxjs/operators';
import { ApiService } from '../../api.service';

interface AttendanceRecord {
  student_id: string | number;
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

interface DateGroup {
  date: string;
  records: AttendanceRecord[];
}

interface SummaryTile {
  label: string;
  value: string | number;
  tone: 'primary' | 'success' | 'danger' | 'warning' | 'info';
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
  isExporting = false;
  showAdvanced = false;
  errorMessage = '';
  successMessage = '';
  activeExportFormat = '';
  expandedProfessorClassIndex: number | null = null;

  reportData: AttendanceReport | ProfessorReport | null = null;
  studentList: any[] = [];
  myClasses: any[] = [];
  instructorList: string[] = [];

  readonly reportTypes = [
    { value: 'class', label: 'Class Report' },
    { value: 'professor', label: 'Professor Report' }
  ];

  readonly statusOptions = [
    { value: 'Present', label: 'Present' },
    { value: 'Absent', label: 'Absent' },
    { value: 'Late', label: 'Late' },
    { value: 'Excused', label: 'Excused' }
  ];

  readonly exportFormats = [
    { value: 'json', label: 'Preview in page' },
    { value: 'csv', label: 'Download CSV' },
    { value: 'excel', label: 'Download Excel' },
    { value: 'pdf', label: 'Download PDF' }
  ];

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService
  ) {
    this.reportForm = this.fb.group({
      reportType: ['class', Validators.required],
      classId: [''],
      professorName: [''],
      dateFrom: ['', Validators.required],
      dateTo: ['', Validators.required],
      studentId: [''],
      studentIds: [''],
      statusFilter: [[]],
      exportFormat: ['json', Validators.required]
    });
  }

  ngOnInit(): void {
    this.setDefaultDateRange();
    this.loadStudents();
    this.loadClasses();
    this.loadInstructors();
  }

  get isClassReportType(): boolean {
    return this.reportForm.get('reportType')?.value === 'class';
  }

  get isProfessorReportType(): boolean {
    return this.reportForm.get('reportType')?.value === 'professor';
  }

  get classReportData(): AttendanceReport | null {
    return this.reportData && !this.isProfessorReport(this.reportData) ? this.reportData : null;
  }

  get professorReportData(): ProfessorReport | null {
    return this.reportData && this.isProfessorReport(this.reportData) ? this.reportData : null;
  }

  get hasReportData(): boolean {
    if (!this.reportData) return false;
    if (this.isProfessorReport(this.reportData)) {
      return this.reportData.classes.length > 0;
    }
    return this.reportData.records.length > 0;
  }

  get activeFilterCount(): number {
    const value = this.reportForm.value;
    let count = 0;

    if (value.classId) count++;
    if (value.professorName) count++;
    if (value.studentId) count++;
    if (value.studentIds?.trim()) count++;
    if (value.statusFilter?.length) count++;

    return count;
  }

  get selectedClassLabel(): string {
    const selectedClass = this.getSelectedClass(this.reportForm.get('classId')?.value);
    if (!selectedClass) return 'No class selected';

    const courseCode = selectedClass.course_code || selectedClass.courseCode || 'Course';
    const section = selectedClass.section || 'Section';
    const instructor = selectedClass.instructor_name || selectedClass.instructorName || 'Instructor not assigned';
    return `${courseCode} - ${section} (${instructor})`;
  }

  get reportDateRangeLabel(): string {
    const from = this.reportForm.get('dateFrom')?.value || 'Start date';
    const to = this.reportForm.get('dateTo')?.value || 'End date';
    return `${from} to ${to}`;
  }

  get recordsGroupedByDate(): DateGroup[] {
    const report = this.classReportData;
    if (!report?.records?.length) return [];

    return this.groupRecordsByDate(report.records);
  }

  get classSummaryTiles(): SummaryTile[] {
    const summary = this.classReportData?.class_summary;
    return summary ? this.buildSummaryTiles(summary) : [];
  }

  get professorSummaryTiles(): SummaryTile[] {
    const summary = this.professorReportData?.consolidated_summary;
    return summary ? this.buildSummaryTiles(summary) : [];
  }

  get filteredProfessorClasses(): any[] {
    const selectedProfessor = this.reportForm.get('professorName')?.value;
    if (!selectedProfessor) return [];

    return this.myClasses.filter((classItem: any) => classItem?.instructor_name === selectedProfessor);
  }

  loadStudents(): void {
    this.apiService.getStudents().subscribe({
      next: (students: any[]) => {
        this.studentList = Array.isArray(students) ? students : [];
      },
      error: () => {
        this.studentList = [];
      }
    });
  }

  loadClasses(): void {
    this.apiService.getClasses().subscribe({
      next: (classes: any[]) => {
        this.myClasses = Array.isArray(classes) ? classes : [];
      },
      error: () => {
        this.myClasses = [];
      }
    });
  }

  loadInstructors(): void {
    this.apiService.getInstructors().subscribe({
      next: (instructors: string[]) => {
        this.instructorList = Array.isArray(instructors) ? instructors : [];
      },
      error: () => {
        this.instructorList = [];
      }
    });
  }

  onReportTypeChange(): void {
    this.reportData = null;
    this.errorMessage = '';
    this.successMessage = '';
    this.expandedProfessorClassIndex = null;

    if (this.isProfessorReportType) {
      this.reportForm.patchValue({
        classId: '',
        studentId: '',
        studentIds: ''
      });
    } else {
      this.reportForm.patchValue({
        professorName: ''
      });
    }
  }

  onProfessorSelectionChange(): void {
    this.reportData = null;
    this.expandedProfessorClassIndex = null;
  }

  isStatusSelected(status: string): boolean {
    const selected: string[] = this.reportForm.get('statusFilter')?.value || [];
    return selected.includes(status);
  }

  onStatusToggle(status: string, checked: boolean): void {
    const selected: string[] = [...(this.reportForm.get('statusFilter')?.value || [])];
    const statusIndex = selected.indexOf(status);

    if (checked && statusIndex === -1) selected.push(status);
    if (!checked && statusIndex !== -1) selected.splice(statusIndex, 1);

    this.reportForm.patchValue({ statusFilter: selected });
  }

  clearStatuses(): void {
    this.reportForm.patchValue({ statusFilter: [] });
  }

  onSubmit(): void {
    this.errorMessage = '';
    this.successMessage = '';

    if (!this.validateReportForm()) return;

    const format = this.reportForm.get('exportFormat')?.value;
    if (format === 'json') {
      this.generateReportPreview();
    } else {
      this.exportReport(format);
    }
  }

  generateReportPreview(): void {
    this.isLoading = true;
    this.reportData = null;
    this.expandedProfessorClassIndex = null;

    const endpoint = this.getReportEndpoint();
    const requestData = this.buildRequestData('json');

    this.apiService.post(endpoint, requestData)
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (response: AttendanceReport | ProfessorReport) => {
          this.reportData = response;
          this.successMessage = this.hasReportData
            ? 'Report generated successfully.'
            : 'Report generated, but no attendance records matched the selected filters.';
        },
        error: (error: any) => {
          this.errorMessage = this.getApiErrorMessage(error, 'Unable to generate report.');
        }
      });
  }

  exportCurrentReport(format: string): void {
    if (!this.validateReportForm()) return;
    this.exportReport(format);
  }

  exportReport(format: string): void {
    this.isExporting = true;
    this.activeExportFormat = format;
    this.errorMessage = '';
    this.successMessage = '';

    const endpoint = this.getReportEndpoint();
    const requestData = this.buildRequestData(format);

    this.apiService.postBlob(endpoint, requestData)
      .pipe(finalize(() => {
        this.isExporting = false;
        this.activeExportFormat = '';
      }))
      .subscribe({
        next: (blob: Blob) => {
          if (!blob || blob.size === 0) {
            this.errorMessage = 'The exported file is empty. Please adjust the filters and try again.';
            return;
          }

          this.downloadFile(blob, format);
          this.successMessage = `${format.toUpperCase()} export downloaded successfully.`;
        },
        error: (error: any) => {
          this.errorMessage = this.getApiErrorMessage(error, 'Unable to export report.');
        }
      });
  }

  clearForm(): void {
    this.reportData = null;
    this.errorMessage = '';
    this.successMessage = '';
    this.expandedProfessorClassIndex = null;
    this.setDefaultDateRange(true);
  }

  toggleAdvancedFilters(): void {
    this.showAdvanced = !this.showAdvanced;
  }

  clearAdvancedFilters(): void {
    this.reportForm.patchValue({
      studentId: '',
      studentIds: '',
      statusFilter: []
    });
  }

  toggleProfessorClass(index: number): void {
    this.expandedProfessorClassIndex = this.expandedProfessorClassIndex === index ? null : index;
  }

  isProfessorReport(data: AttendanceReport | ProfessorReport): data is ProfessorReport {
    return 'classes' in data;
  }

  getStatusBadgeClass(status: string): string {
    switch ((status || '').toLowerCase()) {
      case 'present': return 'badge-success';
      case 'absent': return 'badge-danger';
      case 'late': return 'badge-warning';
      case 'excused': return 'badge-info';
      default: return 'badge-secondary';
    }
  }

  getSummaryToneClass(tone: SummaryTile['tone']): string {
    return `summary-${tone}`;
  }

  getClassRecordGroups(classReport: AttendanceReport): DateGroup[] {
    return this.groupRecordsByDate(classReport.records || []);
  }

  private validateReportForm(): boolean {
    this.reportForm.markAllAsTouched();

    const formValue = this.reportForm.value;
    if (!formValue.dateFrom || !formValue.dateTo) {
      this.errorMessage = 'Please select both From and To dates.';
      return false;
    }

    if (new Date(formValue.dateFrom) > new Date(formValue.dateTo)) {
      this.errorMessage = 'The From date cannot be later than the To date.';
      return false;
    }

    if (formValue.reportType === 'class' && !formValue.classId) {
      this.errorMessage = 'Please select a class before generating a class report.';
      return false;
    }

    if (formValue.reportType === 'professor' && !formValue.professorName) {
      this.errorMessage = 'Please select a professor before generating a professor report.';
      return false;
    }

    return true;
  }

  private buildRequestData(exportFormat: string): any {
    const formValue = this.reportForm.value;
    const selectedClass = this.getSelectedClass(formValue.classId);
    const parsedStudentIds = this.parseStudentIds(formValue.studentId, formValue.studentIds);

    const requestData: any = {
      dateFrom: formValue.dateFrom,
      dateTo: formValue.dateTo,
      exportFormat
    };

    if (formValue.reportType === 'class') {
      requestData.classId = parseInt(formValue.classId, 10);
      requestData.courseCode = selectedClass?.course_code || selectedClass?.courseCode;
      requestData.section = selectedClass?.section;
      requestData.instructorId = selectedClass?.instructor_id || selectedClass?.instructorId;
    }

    if (formValue.reportType === 'professor') {
      requestData.professorName = formValue.professorName;
    }

    if (parsedStudentIds.length > 0) requestData.studentIds = parsedStudentIds;
    if (formValue.statusFilter?.length > 0) requestData.statusFilter = formValue.statusFilter;

    Object.keys(requestData).forEach((key) => {
      if (requestData[key] === undefined || requestData[key] === null || requestData[key] === '') {
        delete requestData[key];
      }
    });

    return requestData;
  }

  private parseStudentIds(studentId: string, studentIds: string): number[] {
    const ids = new Set<number>();

    if (studentId) {
      const parsed = parseInt(studentId, 10);
      if (!Number.isNaN(parsed)) ids.add(parsed);
    }

    if (studentIds?.trim()) {
      studentIds
        .split(',')
        .map((id: string) => parseInt(id.trim(), 10))
        .filter((id: number) => !Number.isNaN(id))
        .forEach((id: number) => ids.add(id));
    }

    return Array.from(ids);
  }

  private getReportEndpoint(): string {
    return this.isProfessorReportType
      ? '/api/admin/attendance/export/professor'
      : '/api/admin/attendance/export';
  }

  private downloadFile(blob: Blob, format: string): void {
    const extensionMap: Record<string, string> = {
      csv: 'csv',
      excel: 'xlsx',
      pdf: 'pdf'
    };

    const extension = extensionMap[format.toLowerCase()] || 'txt';
    const reportType = this.reportForm.get('reportType')?.value || 'attendance';
    const dateStamp = new Date().toISOString().slice(0, 10);
    const filename = `${reportType}_attendance_report_${dateStamp}.${extension}`;

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  private getApiErrorMessage(error: any, fallback: string): string {
    const detail = error?.error?.detail || error?.message;
    return detail ? `${fallback} ${detail}` : fallback;
  }

  private getSelectedClass(classId: string | number | undefined): any | undefined {
    if (!classId) return undefined;

    const classIdNumber = typeof classId === 'number' ? classId : parseInt(classId, 10);
    if (Number.isNaN(classIdNumber)) return undefined;

    return this.myClasses.find((classItem: any) => {
      const candidateId = classItem?.id ?? classItem?.class_id;
      return Number(candidateId) === classIdNumber;
    });
  }

  private groupRecordsByDate(records: AttendanceRecord[]): DateGroup[] {
    const grouped = new Map<string, AttendanceRecord[]>();

    for (const record of records) {
      const dateKey = record.date || 'No date';
      if (!grouped.has(dateKey)) grouped.set(dateKey, []);
      grouped.get(dateKey)!.push(record);
    }

    return Array.from(grouped.entries())
      .map(([date, recordsForDate]) => ({
        date,
        records: recordsForDate.sort((a, b) => String(a.time_in || '').localeCompare(String(b.time_in || '')))
      }))
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }

  private buildSummaryTiles(summary: ClassSummary): SummaryTile[] {
    return [
      { label: 'Total Students', value: summary.total_students || 0, tone: 'primary' },
      { label: 'Present', value: summary.present_count || 0, tone: 'success' },
      { label: 'Absent', value: summary.absent_count || 0, tone: 'danger' },
      { label: 'Late', value: summary.late_count || 0, tone: 'warning' },
      { label: 'Excused', value: summary.excused_count || 0, tone: 'info' },
      { label: 'Attendance Rate', value: `${summary.attendance_percentage || 0}%`, tone: 'primary' }
    ];
  }

  private setDefaultDateRange(resetWholeForm = false): void {
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

    const defaults = {
      reportType: 'class',
      classId: '',
      professorName: '',
      dateFrom: firstDay.toISOString().split('T')[0],
      dateTo: lastDay.toISOString().split('T')[0],
      studentId: '',
      studentIds: '',
      statusFilter: [],
      exportFormat: 'json'
    };

    if (resetWholeForm) {
      this.reportForm.reset(defaults);
    } else {
      this.reportForm.patchValue({
        dateFrom: defaults.dateFrom,
        dateTo: defaults.dateTo
      });
    }
  }
}
