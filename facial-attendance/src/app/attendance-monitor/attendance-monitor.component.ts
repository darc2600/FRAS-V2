
import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, Observable } from 'rxjs';
import { WebcamImage, WebcamModule } from 'ngx-webcam';
import { ApiService } from '../api.service';
import { CommonModule } from '@angular/common';
import { NavbarComponent } from '../components/navbar/navbar.component';

@Component({
  selector: 'app-attendance-monitor',
  templateUrl: './attendance-monitor.component.html',
  styleUrls: ['./attendance-monitor.component.css'],
})
export class AttendanceMonitorComponent implements OnInit, OnDestroy {
  courseCode = '';
  section = '';
  room = '';
  availableRooms: string[] = [];
  allRooms: any[] = [];
  availableFloors: number[] = [];
  selectedFloor: number | null = null;
  currentTime = '';
  message = '';
  webcamImage: WebcamImage | null = null;
  attendanceLogs: any[] = [];
  private trigger: Subject<void> = new Subject<void>();

  // --- New properties for improved UX ---
  courseSection = '';
  availableCourseSections: string[] = [];

  // --- Auto recognition properties ---
  autoRecognitionActive = false;
  autoRecognitionInterval: any = null;
  lastRecognizedId: string | null = null;
  lastRecognizedTime: number = 0;

  // --- New properties for UI improvements ---
  isCapturing = false;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.updateClock();
    setInterval(() => this.updateClock(), 1000);
    this.fetchFloors();

    // Add keyboard event listener for spacebar
    document.addEventListener('keydown', this.handleKeyDown);
  }

  ngOnDestroy() {
    // Clean up the keyboard event listener
    document.removeEventListener('keydown', this.handleKeyDown);
  }

  private handleKeyDown = (event: KeyboardEvent) => {
    if (event.code === 'Space' && !event.repeat) {
      event.preventDefault();
      this.captureAndMarkAttendance();
    }
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
      this.availableCourseSections = [];
      this.courseSection = '';
      return;
    }
    this.fetchRoomsByFloor();
  }

  fetchRoomsByFloor() {
    this.api.getRoomsByFloor(this.selectedFloor!).subscribe(
      (rooms: any[]) => {
        this.allRooms = rooms; // Store the full room objects
        this.availableRooms = rooms.map(r => r.room_number);
        if (this.availableRooms.length > 0) {
          this.room = this.availableRooms[0];
          this.fetchCourseSections();
        } else {
          this.room = '';
          this.availableCourseSections = [];
          this.courseSection = '';
        }
      },
      err => this.message = 'Error fetching rooms for floor.'
    );
  }

  onRoomChange() {
    this.fetchCourseSections();
  }

  fetchCourseSections() {
    if (!this.room) {
      this.availableCourseSections = [];
      this.courseSection = '';
      return;
    }
    
    // Find the room_id for the selected room
    const selectedRoom = this.allRooms.find(r => r.room_number === this.room);
    console.log('Selected room:', this.room, 'Found room object:', selectedRoom);
    if (!selectedRoom) {
      this.availableCourseSections = [];
      this.courseSection = '';
      return;
    }
    
    console.log('Fetching course sections for room_id:', selectedRoom.room_id);
    this.api.getCoursesSectionsByRoom(selectedRoom.room_id).subscribe(
      (coursesSections: any[]) => {
        this.availableCourseSections = coursesSections.map(cs => cs.course_section);
        console.log('Available course sections:', this.availableCourseSections);
        this.courseSection = this.availableCourseSections[0] || '';
        console.log('Selected course section:', this.courseSection);
        this.fetchLogs();
      },
      err => {
        console.error('Error fetching course-sections:', err);
        this.message = 'Error fetching course-sections.';
      }
    );
  }

  onCourseSectionChange() {
    console.log('Course section changed to:', this.courseSection);
    this.fetchLogs();
  }

  updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    const dateString = now.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
    this.currentTime = `${dateString}\n${timeString}`;
  }

  public get triggerObservable(): Observable<void> {
    return this.trigger.asObservable();
  }

  public triggerSnapshot(): void {
    this.trigger.next();
  }

  toggleAutoRecognition() {
    if (this.autoRecognitionActive) {
      this.stopAutoRecognition();
    } else {
      this.startAutoRecognition();
    }
  }

  startAutoRecognition() {
    if (this.autoRecognitionActive) return;
    this.autoRecognitionActive = true;
    this.autoRecognitionInterval = setInterval(() => {
      this.triggerSnapshot();
    }, 2000); // every 2 seconds
  }

  stopAutoRecognition() {
    this.autoRecognitionActive = false;
    if (this.autoRecognitionInterval) {
      clearInterval(this.autoRecognitionInterval);
      this.autoRecognitionInterval = null;
    }
  }

  public handleImage(webcamImage: WebcamImage): void {
    this.webcamImage = webcamImage;
    this.isCapturing = false; // Reset capturing status

    if (this.autoRecognitionActive) {
      this.autoMarkAttendance();
    } else {
      // For manual capture, automatically mark attendance
      this.performAttendanceRecognition();
    }
  }

  autoMarkAttendance() {
    if (!this.webcamImage || !this.courseSection || !this.room) return;
    const [courseCode, section] = this.courseSection.split('-');
    const blob = this.dataURLtoBlob(this.webcamImage.imageAsDataUrl);
    const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
    this.api.recognizeFace(file, courseCode, section, this.room).subscribe(
      res => {
        if (res.status === 'success') {
          // Avoid duplicate marking within 10 seconds
          if (this.lastRecognizedId !== res.student_id || Date.now() - this.lastRecognizedTime > 10000) {
            this.message = `Attendance marked for ${res.student_id}`;
            this.lastRecognizedId = res.student_id;
            this.lastRecognizedTime = Date.now();
            this.fetchLogs();
          }
        } else {
          this.message = res.message;
        }
      },
      err => this.message = 'Error connecting to backend.'
    );
  }

  performAttendanceRecognition() {
    if (!this.webcamImage) {
      this.message = 'Please capture an image first.';
      return;
    }
    if (!this.courseSection || !this.room) {
      this.message = 'Please select a room and course-section.';
      return;
    }
    const [courseCode, section] = this.courseSection.split('-');
    const blob = this.dataURLtoBlob(this.webcamImage.imageAsDataUrl);
    const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
    this.api.recognizeFace(file, courseCode, section, this.room).subscribe(
      res => {
        this.message = res.status === 'success'
          ? `Attendance marked for ${res.student_id}`
          : res.message;
        this.fetchLogs();
      },
      err => this.message = 'Error connecting to backend.'
    );
  }

  captureAndMarkAttendance() {
    if (!this.courseSection || !this.room) {
      this.message = 'Please select a room and course-section.';
      return;
    }

    this.isCapturing = true;
    this.triggerSnapshot();
  }

  fetchLogs() {
    if (!this.courseSection) {
      this.attendanceLogs = [];
      return;
    }
    const [courseCode, section] = this.courseSection.split('-');
    // Get today's date for filtering attendance to current day
    const today = new Date().toISOString().split('T')[0];
    console.log('Fetching logs for:', courseCode, section, today);
    // For now, don't filter by room to show all attendance for the course-section
    this.api.getAttendance(courseCode, section, undefined, today, today).subscribe(
      res => {
        this.attendanceLogs = (res.attendance || []).map((log: any) => ({
          studentId: log[0],
          studentName: log[1],
          time: log[2],
          status: log[3] || 'Unknown'
        }));
        console.log('Attendance logs loaded:', this.attendanceLogs.length, 'records');
      },
      err => {
        console.error('Error fetching logs:', err);
        this.message = 'Error fetching logs.';
      }
    );
  }

  getStatusClass(status: string) {
    if (status.toLowerCase() === 'present') return 'present';
    if (status.toLowerCase() === 'late') return 'late';
    if (status.toLowerCase() === 'absent') return 'absent';
    return '';
  }

  dataURLtoBlob(dataurl: string) {
    const arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)![1],
      bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    for (let i = 0; i < n; i++) u8arr[i] = bstr.charCodeAt(i);
    return new Blob([u8arr], { type: mime });
  }
}
