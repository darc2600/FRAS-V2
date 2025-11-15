
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

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
  availableSections: string[] = []; // Dynamic sections based on course/room
  filteredCourses: any[] = [];
  showCourseSuggestions = false;
  
  logs: any[] = [];
  groupedLogs: { [date: string]: any[] } = {};
  message = '';
  loading = false;

  constructor(private api: ApiService) {}

  ngOnInit() {
    // Set default date to today
    const today = new Date();
    this.selectedDate = today.toISOString().split('T')[0];
    this.startDate = today.toISOString().split('T')[0];
    this.endDate = today.toISOString().split('T')[0];
    
    // this.fetchFloors();
    this.loadValidationData();
  }

  // fetchFloors() {
  //   this.api.getFloors().subscribe(
  //     (floors: number[]) => {
  //       this.availableFloors = floors;
  //       if (this.availableFloors.length > 0) {
  //         this.selectedFloor = this.availableFloors[0];
  //         this.onFloorChange();
  //       }
  //     },
  //     err => this.message = 'Error fetching floors.'
  //   );
  // }

  // onFloorChange() {
  //   if (this.selectedFloor == null) {
  //     this.availableRooms = [];
  //     this.room = '';
  //     return;
  //   }
  //   this.fetchRoomsByFloor();
  // }

  // fetchRoomsByFloor() {
  //   this.api.getRoomsByFloor(this.selectedFloor!).subscribe(
  //     (rooms: any[]) => {
  //       this.allRooms = rooms;
  //       this.availableRooms = rooms.map(r => r.room_number);
  //       if (this.availableRooms.length > 0) {
  //         this.room = this.availableRooms[0];
  //         this.onRoomChange();
  //       } else {
  //         this.room = '';
  //         this.availableSections = [];
  //         this.section = '';
  //       }
  //     },
  //     err => this.message = 'Error fetching rooms for floor.'
  //   );
  // }

  // onRoomChange() {
  //   this.loadAvailableSections();
  // }

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
    // Since we don't have room filtering, we need to get sections differently
    // For now, let's use a simple approach - get all courses and find sections for the selected course
    this.api.getCourses().subscribe(
      (courses: any[]) => {
        const selectedCourse = courses.find(c => c.code === this.courseCode);
        if (selectedCourse) {
          // For simplicity, let's assume sections are AM1, PM1, etc. or we can hardcode some common sections
          // In a real implementation, we'd need a backend endpoint to get sections for a course
          this.availableSections = ['AM1', 'PM1', 'AM2', 'PM2']; // Common sections
          if (!this.section && this.availableSections.length > 0) {
            this.section = this.availableSections[0];
          }
        } else {
          this.availableSections = [];
          this.section = '';
        }
      },
      err => {
        console.error('Error fetching courses:', err);
        this.availableSections = [];
        this.section = '';
      }
    );
  }

  loadValidationData() {
    // Load valid courses
    this.api.getCourses().subscribe({
      next: (courses: any[]) => {
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
    
    // Pass undefined for room since we're not using room filtering
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
      const date = log.time.split(' ')[0]; // Extract date part directly from timestamp
      if (!this.groupedLogs[date]) {
        this.groupedLogs[date] = [];
      }
      this.groupedLogs[date].push(log);
    });
  }

  get objectKeys() {
    return Object.keys;
  }

  toggleDateMode() {
    this.isDateRangeMode = !this.isDateRangeMode;
    // Reset dates when switching modes
    const today = new Date().toISOString().split('T')[0];
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
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
  }
}
