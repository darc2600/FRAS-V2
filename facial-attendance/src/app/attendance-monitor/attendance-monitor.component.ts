
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, Observable } from 'rxjs';
import { WebcamImage, WebcamModule } from 'ngx-webcam';
import { ApiService } from '../api.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-attendance-monitor',
  standalone: true, // <-- Add this if using standalone components
  templateUrl: './attendance-monitor.component.html',
  styleUrls: ['./attendance-monitor.component.css'],
  imports: [WebcamModule, CommonModule, FormsModule], // <-- Add required modules here
})
export class AttendanceMonitorComponent implements OnInit {
  courseCode = '';
  section = '';
  room = '';
  availableCourses: string[] = [];
  availableSections: string[] = [];
  availableRooms: string[] = [];
  currentTime = '';
  message = '';
  webcamImage: WebcamImage | null = null;
  attendanceLogs: any[] = [];
  private trigger: Subject<void> = new Subject<void>();

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.updateClock();
    setInterval(() => this.updateClock(), 1000);
    this.fetchRooms();
  }

  fetchRooms() {
    this.api.getRooms().subscribe(
      (rooms: string[]) => {
        this.availableRooms = rooms;
        if (rooms.length > 0) {
          this.room = rooms[0];
          this.fetchCourses();
        }
      },
      err => this.message = 'Error fetching rooms.'
    );
  }

  onRoomChange() {
    this.fetchCourses();
  }

  fetchCourses() {
    if (!this.room) {
      this.availableCourses = [];
      this.availableSections = [];
      return;
    }
    this.api.getCourses(this.room).subscribe(
      (courses: string[]) => {
        this.availableCourses = courses;
        this.courseCode = courses[0] || '';
        this.fetchSections();
      },
      err => this.message = 'Error fetching courses.'
    );
  }

  onCourseChange() {
    this.fetchSections();
  }

  fetchSections() {
    if (!this.room || !this.courseCode) {
      this.availableSections = [];
      return;
    }
    this.api.getSections(this.room, this.courseCode).subscribe(
      (sections: string[]) => {
        this.availableSections = sections;
        this.section = sections[0] || '';
        this.fetchLogs();
      },
      err => this.message = 'Error fetching sections.'
    );
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

  public handleImage(webcamImage: WebcamImage): void {
    this.webcamImage = webcamImage;
  }

  markAttendance() {
    if (!this.webcamImage) {
      this.message = 'Please capture an image first.';
      return;
    }
    if (!this.courseCode || !this.section || !this.room) {
      this.message = 'Please select a room, course, and section.';
      return;
    }
    const blob = this.dataURLtoBlob(this.webcamImage.imageAsDataUrl);
    const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
    this.api.recognizeFace(file, this.courseCode, this.section, this.room).subscribe(
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
    if (!this.courseCode || !this.section || !this.room) {
      this.attendanceLogs = [];
      return;
    }
    this.api.getAttendance(this.courseCode, this.section, this.room).subscribe(
      res => {
        // Adjust this mapping as needed for your backend response
        this.attendanceLogs = (res.attendance || []).map((log: any) => ({
          studentName: log[0], // or log.studentName if your backend returns named fields
          time: log[1],
          status: 'Present' // You can enhance this logic
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
