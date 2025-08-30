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
  availableCourses: string[] = ['IT123', 'IT164', 'IT164L', 'MALU', 'SW123']; // You can fetch from backend if needed
  availableSections: string[] = ['AM1', 'AM3', 'AM4', 'PET']; // You can fetch from backend if needed
  currentTime = '';
  message = '';
  webcamImage: WebcamImage | null = null;
  attendanceLogs: any[] = [];
  private trigger: Subject<void> = new Subject<void>();

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.updateClock();
    setInterval(() => this.updateClock(), 1000);
    // Optionally set defaults
    this.courseCode = this.availableCourses[0];
    this.section = this.availableSections[0];
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

  public handleImage(webcamImage: WebcamImage): void {
    this.webcamImage = webcamImage;
  }

  markAttendance() {
    if (!this.webcamImage) {
      this.message = 'Please capture an image first.';
      return;
    }
    if (!this.courseCode || !this.section) {
      this.message = 'Please select a course and section.';
      return;
    }
    const blob = this.dataURLtoBlob(this.webcamImage.imageAsDataUrl);
    const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
    this.api.recognizeFace(file, this.courseCode, this.section).subscribe(
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
    if (!this.courseCode || !this.section) {
      this.attendanceLogs = [];
      return;
    }
    this.api.getAttendance(this.courseCode, this.section).subscribe(
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
