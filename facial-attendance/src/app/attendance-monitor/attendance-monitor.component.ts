
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
  styleUrls: ['./attendance-monitor.component.css', '../shared/status-styles.css'],
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
  availableCourseSectionObjects: any[] = [];
  selectedClassId: number | null = null;

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
        const filteredCourseSections = coursesSections.filter(cs => cs.course_section && cs.course_section.toString().trim().length > 0);
        this.availableCourseSectionObjects = filteredCourseSections;
        this.availableCourseSections = filteredCourseSections.map(cs => cs.course_section);
        console.log('Available course sections:', this.availableCourseSections);
        this.courseSection = this.availableCourseSections.length > 0 ? this.availableCourseSections[0] : '';
        console.log('Selected course section:', this.courseSection);
        this.updateSelectedClassId();
        this.fetchLogs();
      },
      err => {
        console.error('Error fetching course-sections:', err);
        this.message = 'Error fetching course-sections.';
      }
    );
  }

  onCourseSectionChange() {
    console.log('onCourseSectionChange: Course section changed to:', this.courseSection);
    this.updateSelectedClassId();
    console.log('onCourseSectionChange: Updated classId to:', this.selectedClassId);
    this.fetchLogs();
  }

  updateSelectedClassId() {
    const selectedObject = this.availableCourseSectionObjects.find(cs => cs.course_section === this.courseSection);
    this.selectedClassId = selectedObject ? selectedObject.class_id : null;
    console.log('Selected class_id:', this.selectedClassId);
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
    if (!this.webcamImage || !this.selectedClassId) {
      console.log('autoMarkAttendance: Missing webcam image or classId');
      return;
    }
    const blob = this.dataURLtoBlob(this.webcamImage.imageAsDataUrl);
    const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
    console.log('autoMarkAttendance: Calling recognize API with classId:', this.selectedClassId);
    this.api.recognizeFace(file, this.selectedClassId).subscribe(
      res => {
        console.log('autoMarkAttendance: API response:', res);
        if (res.status === 'success') {
          // Avoid duplicate marking within 10 seconds
          if (this.lastRecognizedId !== res.student_id || Date.now() - this.lastRecognizedTime > 10000) {
            this.message = `Attendance marked for ${res.student_name || 'Unknown'}: ${res.attendance_status || 'Unknown'}`;
            this.lastRecognizedId = res.student_id;
            this.lastRecognizedTime = Date.now();
            console.log('autoMarkAttendance: Calling fetchLogs after successful recognition');
            this.fetchLogs();
          } else {
            console.log('autoMarkAttendance: Duplicate recognition, skipping');
          }
        } else {
          console.log('autoMarkAttendance: Recognition failed:', res.message);
          this.message = res.message;
        }
      },
      err => {
        console.log('autoMarkAttendance: API error:', err);
        this.message = 'Error connecting to backend.';
      }
    );
  }

  performAttendanceRecognition() {
    if (!this.webcamImage) {
      console.log('performAttendanceRecognition: No webcam image');
      this.message = 'Please capture an image first.';
      return;
    }
    if (!this.selectedClassId) {
      console.log('performAttendanceRecognition: No classId selected');
      this.message = 'Please select a room and course-section.';
      return;
    }
    const blob = this.dataURLtoBlob(this.webcamImage.imageAsDataUrl);
    const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
    console.log('performAttendanceRecognition: Calling recognize API with classId:', this.selectedClassId);
    this.api.recognizeFace(file, this.selectedClassId).subscribe(
      res => {
        console.log('performAttendanceRecognition: API response:', res);
        this.message = res.status === 'success'
          ? `Attendance marked for ${res.student_name || 'Unknown'}: ${res.attendance_status || 'Unknown'}`
          : res.message;
        if (res.status === 'success') {
          console.log('performAttendanceRecognition: Calling fetchLogs after successful recognition');
          this.fetchLogs();
        }
      },
      err => {
        console.log('performAttendanceRecognition: API error:', err);
        this.message = 'Error connecting to backend.';
      }
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
      console.log('fetchLogs: No courseSection selected');
      this.attendanceLogs = [];
      return;
    }
    const [courseCode, section] = this.courseSection.split('-');
    // Get today's date in local timezone (not UTC)
    const today = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD format in local timezone
    console.log('fetchLogs: Fetching logs for:', courseCode, section, 'date:', today, 'class_id:', this.selectedClassId);
    
    this.api.getAttendance(courseCode, section, undefined, today, today).subscribe(
      res => {
        console.log('fetchLogs: API response:', res);
        this.attendanceLogs = (res.attendance || []).map((log: any) => ({
          studentId: log[0],
          studentName: log[1],
          time: log[2],
          status: (log[3] || 'Unknown').toLowerCase()
        }));
        console.log('fetchLogs: Loaded', this.attendanceLogs.length, 'records');
      },
      err => {
        console.error('fetchLogs: Error fetching logs:', err);
        this.message = 'Error fetching logs.';
      }
    );
  }

  getStatusClass(status: string) {
    if (status.toLowerCase() === 'present') return 'status-present';
    if (status.toLowerCase() === 'late') return 'status-late';
    if (status.toLowerCase() === 'absent') return 'status-absent';
    if (status.toLowerCase() === 'excused absence') return 'status-excused';
    return '';
  }

  dataURLtoBlob(dataurl: string) {
    const arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)![1],
      bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    for (let i = 0; i < n; i++) u8arr[i] = bstr.charCodeAt(i);
    return new Blob([u8arr], { type: mime });
  }
}
