
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

const MANILA_TIME_ZONE = 'Asia/Manila';

@Component({
  selector: 'app-attendance-logs',
  templateUrl: './attendance-logs.component.html',
  styleUrls: ['./attendance-logs.component.css', '../shared/status-styles.css'],
})
export class AttendanceLogsComponent implements OnInit {
  startDate: string = '';
  endDate: string = '';
  selectedDate: string = ''; // For single date mode
  isDateRangeMode: boolean = false; // Toggle between single date and date range
  
  // currentTime: string = '';
  // availableFloors: number[] = [];
  // selectedFloor: number | null = null;
  // allRooms: any[] = [];
  // availableRooms: string[] = [];
  // room = '';
  
  // Course and section filtering
  courseCode = '';
  section = '';
  validCourses: any[] = [];
  availableSections: string[] = []; // Dynamic sections based on course
  filteredCourses: any[] = [];
  showCourseSuggestions = false;
  
  logs: any[] = [];
  groupedLogs: { [date: string]: any[] } = {};
  groupedDateKeys: string[] = [];
  message = '';
  loading = false;

  constructor(private api: ApiService) {}

  ngOnInit() {
    // Set default date to today
    const today = new Date();
    const localToday = this.toLocalDateString(today);
    this.selectedDate = localToday;
    this.startDate = localToday;
    this.endDate = localToday;
    
    this.loadValidationData();
  }

  onCourseChange() {
    this.loadAvailableSections();
  }

  onSectionChange() {
    // Section changed - user can now click Search Logs button
    // Auto-fetch removed to give user control
  }

  loadAvailableSections() {
    if (!this.courseCode) {
      this.availableSections = [];
      this.section = '';
      return;
    }

    // Get all sections for the selected course across all rooms
    this.getAllSectionsForCourse();
  }

  getAllSectionsForCourse() {
    console.log('getAllSectionsForCourse called with courseCode:', this.courseCode);
    if (!this.courseCode) {
      this.availableSections = [];
      this.section = '';
      return;
    }

    // Fetch sections from backend for the selected course
    this.api.getSectionsForCourse(this.courseCode).subscribe(
      (sections: string[]) => {
        console.log('Sections fetched:', sections);
        this.availableSections = sections;
        if (!this.section && this.availableSections.length > 0) {
          this.section = this.availableSections[0];
        }
      },
      (err: any) => {
        console.error('Error fetching sections:', err);
        this.availableSections = [];
        this.section = '';
      }
    );
  }

  loadValidationData() {
    // Load valid courses
    this.api.getCourses().subscribe({
      next: (courses: any[]) => {
        console.log('Courses loaded:', courses);
        this.validCourses = courses;
      },
      error: (error) => {
        console.error('Error loading courses:', error);
      }
    });
  }

  onCourseInputChange() {
    if (this.courseCode.trim().length === 0) {
      this.filteredCourses = [];
      this.showCourseSuggestions = false;
      return;
    }

    const searchTerm = this.courseCode.trim().toLowerCase();
    this.filteredCourses = this.validCourses.filter(course =>
      course.code.toLowerCase().includes(searchTerm) ||
      course.name.toLowerCase().includes(searchTerm)
    ).slice(0, 10); // Limit to 10 suggestions

    this.showCourseSuggestions = this.filteredCourses.length > 0;

    // If exact match, load sections
    const exactMatch = this.validCourses.find(c => c.code.toLowerCase() === searchTerm);
    if (exactMatch) {
      this.courseCode = exactMatch.code; // normalize case
      this.getAllSectionsForCourse();
    }
  }

  selectCourse(course: any) {
    this.courseCode = course.code;
    this.showCourseSuggestions = false;
    this.onCourseChange();
  }

  hideSuggestions() {
    setTimeout(() => {
      this.showCourseSuggestions = false;
    }, 150);
  }

  fetchLogs() {
    if (!this.courseCode || !this.section) {
      this.logs = [];
      this.groupedLogs = {};
      this.message = 'Please select course and section.';
      return;
    }
    
    this.loading = true;
    
    // Set dates based on mode
    let startDate = this.startDate;
    let endDate = this.endDate;
    
    if (!this.isDateRangeMode) {
      // Single date mode - use selected date for both start and end
      startDate = this.selectedDate;
      endDate = this.selectedDate;
    }
    
    // Pass room for filtering
    this.api.getAttendance(this.courseCode, this.section, undefined, startDate, endDate).subscribe(
      res => {
        this.logs = (res.attendance || []).map((log: any) => ({
          studentNumber: log[0],
          studentName: log[1],
          time: log[2],
          status: (log[3] || 'Unknown').toLowerCase()
        }));
        this.groupLogsByDate();
        this.loading = false;
        if (!this.logs || this.logs.length === 0) {
          const dateRange = this.isDateRangeMode ? 
            `from ${startDate} to ${endDate}` : 
            `for ${startDate}`;
          this.message = `No attendance records found for ${this.courseCode} ${this.section} ${dateRange}.`;
        } else {
          const dateRange = this.isDateRangeMode ? 
            `${startDate} - ${endDate}` : 
            startDate;
          this.message = `Found ${this.logs.length} attendance record${this.logs.length === 1 ? '' : 's'} for ${dateRange}.`;
        }
      },
      err => {
        this.message = 'Error fetching logs.';
        this.loading = false;
      }
    );
  }

  groupLogsByDate() {
    this.groupedLogs = {};
    this.logs.forEach(log => {
      const date = this.getDateKey(log.time);
      if (!this.groupedLogs[date]) {
        this.groupedLogs[date] = [];
      }
      this.groupedLogs[date].push(log);
    });
    this.groupedDateKeys = Object.keys(this.groupedLogs).sort((a, b) => b.localeCompare(a));
  }

  get objectKeys() {
    return Object.keys;
  }

  private getDateKey(timestamp: string): string {
    if (!timestamp) {
      return '';
    }

    const normalized = timestamp.trim();
    const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(normalized);
    if (isDateOnly) {
      return normalized;
    }

    const parsedDate = new Date(normalized);
    if (!Number.isNaN(parsedDate.getTime())) {
      return this.toManilaDateString(parsedDate);
    }

    return normalized;
  }

  private toLocalDateString(date: Date): string {
    return this.toManilaDateString(date);
  }

  private toManilaDateString(date: Date): string {
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: MANILA_TIME_ZONE,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).formatToParts(date);
    const values = Object.fromEntries(parts.map(part => [part.type, part.value]));
    return `${values['year']}-${values['month']}-${values['day']}`;
  }

  private formatManilaTime(date: Date): string {
    return date.toLocaleTimeString('en-US', {
      timeZone: MANILA_TIME_ZONE,
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  toggleDateMode() {
    this.isDateRangeMode = !this.isDateRangeMode;
    if (this.isDateRangeMode) {
      // Switching to date range - keep current selectedDate as startDate
      this.startDate = this.selectedDate;
      this.endDate = this.selectedDate;
    } else {
      // Switching to single date - use startDate as selectedDate
      this.selectedDate = this.startDate;
    }
  }

  formatDateTime(dt: string): string {
    const d = new Date(dt);
    return `${this.toManilaDateString(d)} ${this.formatManilaTime(d)}`;
  }

  exportToCSV() {
    if (this.logs.length === 0) {
      alert('No attendance records to export.');
      return;
    }

    // Create CSV header
    const headers = ['#', 'Student Number', 'Name', 'Date', 'Time', 'Status'];
    const csvContent: string[] = [headers.join(',')];

    // Add data rows
    let rowNumber = 1;
    Object.keys(this.groupedLogs).forEach(date => {
      this.groupedLogs[date].forEach(log => {
        const time = this.formatDateTime(log.time);
        const [dateStr, ...timeParts] = time.split(' ');
        const timeStr = timeParts.join(' ');
        const row = [
          rowNumber++,
          log.studentNumber,
          `"${log.studentName || log.name}"`, // Wrap in quotes to handle commas in names
          dateStr,
          timeStr,
          log.status.charAt(0).toUpperCase() + log.status.slice(1)
        ];
        csvContent.push(row.join(','));
      });
    });

    // Create blob and download
    const csvString = csvContent.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    // Generate filename with course, section, and date range
    const dateRange = this.isDateRangeMode
      ? `${this.startDate}_to_${this.endDate}`
      : this.selectedDate;
    const filename = `Attendance_${this.courseCode}_${this.section}_${dateRange}.csv`;

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
