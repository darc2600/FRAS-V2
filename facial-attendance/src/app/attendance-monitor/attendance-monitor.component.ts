
import { Component, OnInit } from '@angular/core';
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
export class AttendanceMonitorComponent implements OnInit {
  courseCode = '';
  section = '';
  room = '';
  availableCourses: string[] = [];
  availableSections: string[] = [];
  availableRooms: string[] = [];
  allRooms: any[] = [];
  availableFloors: number[] = [];
  selectedFloor: number | null = null;
  // Room type for clarity
  private getRoomLabel(room: any): string {
    if (!room) return '';
    if (typeof room === 'string') return room;
    return room.room_id || room.id || room.name || '';
  }
  currentTime = '';
  message = '';
  webcamImage: WebcamImage | null = null;
  attendanceLogs: any[] = [];
  private trigger: Subject<void> = new Subject<void>();

  // --- New properties for improved UX ---
  roomSearch = '';
  filteredRooms: string[] = [];
  courseSection = '';
  availableCourseSections: string[] = [];
  showRoomDropdown = false;

  // --- Auto recognition properties ---
  autoRecognitionActive = false;
  autoRecognitionInterval: any = null;
  lastRecognizedId: string | null = null;
  lastRecognizedTime: number = 0;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.updateClock();
    setInterval(() => this.updateClock(), 1000);
    this.fetchRooms();
  }

  fetchRooms() {
    this.api.getRooms().subscribe(
      (rooms: any[]) => {
        this.allRooms = rooms;
        // If rooms have floor_level, extract unique floors
        this.availableFloors = Array.from(new Set(rooms.map(r => r.floor_level).filter(f => f != null))).sort((a, b) => a - b);
        if (this.availableFloors.length > 0) {
          this.selectedFloor = this.availableFloors[0];
          this.filterRoomsByFloor();
        } else {
          this.availableRooms = rooms.map(r => r.room_id || r.id || r.name);
          this.filteredRooms = this.availableRooms;
        }
      },
      err => this.message = 'Error fetching rooms.'
    );
  }

  filterRoomsByFloor() {
    if (this.selectedFloor == null) {
      this.availableRooms = [];
      this.filteredRooms = [];
      return;
    }
    const roomsOnFloor = this.allRooms.filter(r => r.floor_level === this.selectedFloor).map(r => r.room_id);
    this.availableRooms = roomsOnFloor;
    this.filteredRooms = roomsOnFloor;
    if (roomsOnFloor.length > 0) {
      this.room = roomsOnFloor[0];
      this.fetchCourseSections();
    } else {
      this.room = '';
      this.availableCourseSections = [];
      this.courseSection = '';
    }
  }

  onRoomSearchChange() {
    if (!this.roomSearch) {
      this.filteredRooms = this.availableRooms;
      this.showRoomDropdown = false;
      return;
    }
    // Simple client-side filter
    this.filteredRooms = this.availableRooms.filter(r =>
      this.getRoomLabel(r).toLowerCase().includes(this.roomSearch.toLowerCase())
    );
    this.showRoomDropdown = true;
  }

  selectRoom(room: string) {
    this.room = room;
    this.roomSearch = room;
    this.showRoomDropdown = false;
    this.fetchCourseSections();
  }

  onRoomInputBlur() {
    setTimeout(() => {
      this.showRoomDropdown = false;
    }, 200);
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
    this.api.getRoomSchedule(this.room).subscribe(
      (result: any) => {
        if (result && Array.isArray(result.schedule)) {
          const pairs = result.schedule.map((cls: any) => `${cls.course_code || cls.courseCode} - ${cls.section}`);
          this.availableCourseSections = Array.from(new Set(pairs));
          this.courseSection = this.availableCourseSections[0] || '';
        } else {
          this.availableCourseSections = [];
          this.courseSection = '';
        }
        this.fetchLogs();
      },
      err => this.message = 'Error fetching course-sections.'
    );
  }

  onCourseSectionChange() {
    this.fetchLogs();
  }

  updateClock() {
    this.currentTime = new Date().toLocaleTimeString();
  }

  public get triggerObservable(): Observable<void> {
    return this.trigger.asObservable();
  }

  public triggerSnapshot(): void {
    this.trigger.next();
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
    if (this.autoRecognitionActive) {
      this.autoMarkAttendance();
    }
  }

  autoMarkAttendance() {
    if (!this.webcamImage || !this.courseSection || !this.room) return;
    const [courseCode, section] = this.courseSection.split(' - ');
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

  markAttendance() {
    if (!this.webcamImage) {
      this.message = 'Please capture an image first.';
      return;
    }
    if (!this.courseSection || !this.room) {
      this.message = 'Please select a room and course-section.';
      return;
    }
    const [courseCode, section] = this.courseSection.split(' - ');
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

  fetchLogs() {
    if (!this.courseSection || !this.room) {
      this.attendanceLogs = [];
      return;
    }
    const [courseCode, section] = this.courseSection.split(' - ');
    this.api.getAttendance(courseCode, section, this.room).subscribe(
      res => {
        this.attendanceLogs = (res.attendance || []).map((log: any) => ({
          studentId: log[0],
          studentName: log[1],
          time: log[2],
          status: log[3] || 'Unknown'
        }));
      },
      err => this.message = 'Error fetching logs.'
    );
  }

  getStatusClass(status: string) {
    if (status === 'Present') return 'present';
    if (status === 'Late') return 'late';
    if (status === 'Absent') return 'absent';
    return '';
  }

  dataURLtoBlob(dataurl: string) {
    const arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)![1],
      bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    for (let i = 0; i < n; i++) u8arr[i] = bstr.charCodeAt(i);
    return new Blob([u8arr], { type: mime });
  }
}
