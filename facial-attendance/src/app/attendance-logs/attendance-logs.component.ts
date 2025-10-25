
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-attendance-logs',
  templateUrl: './attendance-logs.component.html',
  styleUrls: ['./attendance-logs.component.css'],
})
export class AttendanceLogsComponent implements OnInit {
  selectedDate: string = '';
  currentTime: string = '';
  availableFloors: number[] = [];
  selectedFloor: number | null = null;
  allRooms: any[] = [];
  availableRooms: string[] = [];
  room = '';
  
  // Course and section filtering
  courseCode = '';
  section = '';
  validCourses: any[] = [];
  availableSections: string[] = []; // Dynamic sections based on course/room
  filteredCourses: any[] = [];
  showCourseSuggestions = false;
  
  logs: any[] = [];
  message = '';
  loading = false;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.updateClock();
    setInterval(() => this.updateClock(), 1000);
    
    // Set default date to today
    const today = new Date();
    this.selectedDate = today.toISOString().split('T')[0];
    
    this.fetchFloors();
    this.loadValidationData();
  }

  updateClock() {
    this.currentTime = new Date().toLocaleTimeString();
  }

  fetchFloors() {
    this.api.getFloors().subscribe(
      (floors: number[]) => {
        this.availableFloors = floors;
        if (this.availableFloors.length > 0) {
          this.selectedFloor = this.availableFloors[0];
          this.onFloorChange();
        }
      },
      err => this.message = 'Error fetching floors.'
    );
  }

  onFloorChange() {
    if (this.selectedFloor == null) {
      this.availableRooms = [];
      this.room = '';
      return;
    }
    this.fetchRoomsByFloor();
  }

  fetchRoomsByFloor() {
    this.api.getRoomsByFloor(this.selectedFloor!).subscribe(
      (rooms: any[]) => {
        this.allRooms = rooms;
        this.availableRooms = rooms.map(r => r.room_number);
        if (this.availableRooms.length > 0) {
          this.room = this.availableRooms[0];
          this.onRoomChange();
        } else {
          this.room = '';
          this.availableSections = [];
          this.section = '';
        }
      },
      err => this.message = 'Error fetching rooms for floor.'
    );
  }

  onRoomChange() {
    this.loadAvailableSections();
  }

  onCourseChange() {
    this.loadAvailableSections();
  }

  loadAvailableSections() {
    if (!this.room || !this.courseCode) {
      this.availableSections = [];
      this.section = '';
      return;
    }

    // Find the room_id for the selected room
    const selectedRoom = this.allRooms.find(r => r.room_number === this.room);
    if (!selectedRoom) {
      this.availableSections = [];
      this.section = '';
      return;
    }

    // Get course sections for this room
    this.api.getCoursesSectionsByRoom(selectedRoom.room_id).subscribe(
      (coursesSections: any[]) => {
        // Filter sections for the selected course
        const courseSections = coursesSections.filter(cs => 
          cs.course_code === this.courseCode || cs.courseCode === this.courseCode
        );
        this.availableSections = courseSections.map(cs => cs.section);
        
        // Reset section if current selection is not available
        if (this.section && !this.availableSections.includes(this.section)) {
          this.section = this.availableSections.length > 0 ? this.availableSections[0] : '';
        } else if (!this.section && this.availableSections.length > 0) {
          this.section = this.availableSections[0];
        }
      },
      err => {
        console.error('Error fetching course sections:', err);
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
    if (!this.courseCode || !this.section || !this.room) {
      this.logs = [];
      this.message = 'Please select room, course, and section.';
      return;
    }
    
    this.loading = true;
    this.api.getAttendance(this.courseCode, this.section, this.room).subscribe(
      res => {
        this.logs = (res.attendance || []).map((log: any) => ({
          studentId: log[0],
          studentName: log[1],
          time: log[2],
          status: log[3] || 'Unknown'
        }));
        this.loading = false;
        if (!this.logs || this.logs.length === 0) {
          this.message = 'No records found.';
        } else {
          this.message = '';
        }
      },
      err => {
        this.message = 'Error fetching logs.';
        this.loading = false;
      }
    );
  }

  getStatusClass(status: string) {
    if (status.toLowerCase() === 'present') return 'present';
    if (status.toLowerCase() === 'late') return 'late';
    if (status.toLowerCase() === 'absent') return 'absent';
    return '';
  }

  formatDateTime(dt: string): string {
    const d = new Date(dt);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
  }
}
