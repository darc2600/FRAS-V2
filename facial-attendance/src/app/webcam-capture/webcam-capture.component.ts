
import { Component } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { WebcamModule, WebcamImage, WebcamInitError } from 'ngx-webcam';
import { Subject, Observable } from 'rxjs';
import { ApiService } from '../api.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-webcam-capture',
  templateUrl: './webcam-capture.component.html',
  styleUrls: ['./webcam-capture.component.css']
})
export class WebcamCaptureComponent {
  courseCode = '';
  section = '';
  courseCodeSection = '';
  message = '';
  webcamImage: WebcamImage | null = null;
  private trigger: Subject<void> = new Subject<void>();

  availableRooms: string[] = [];
  selectedRoom: string = '';
  availableCourseSections: string[] = [];

  constructor(private api: ApiService) {
    this.loadRooms();
  }

  loadRooms() {
    this.api.getRooms().subscribe(rooms => {
      this.availableRooms = rooms;
      if (rooms.length > 0) {
        this.selectedRoom = rooms[0];
        this.onRoomChange();
      }
    });
  }

  onRoomChange() {
    if (!this.selectedRoom) {
      this.availableCourseSections = [];
      this.courseCodeSection = '';
      return;
    }
    this.api.getRoomSchedule(this.selectedRoom).subscribe(result => {
      if (result && Array.isArray(result.schedule)) {
        const pairs = result.schedule.map((cls: any) => `${cls.courseCode}-${cls.section}`);
        this.availableCourseSections = Array.from(new Set(pairs));
        // Reset selection if not in new list
        if (!this.availableCourseSections.includes(this.courseCodeSection)) {
          this.courseCodeSection = '';
        }
      } else {
        this.availableCourseSections = [];
        this.courseCodeSection = '';
      }
    });
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
    // Split courseCodeSection into courseCode and section
    if (this.courseCodeSection) {
      const [code, ...sectionParts] = this.courseCodeSection.split('-');
      this.courseCode = code;
      this.section = sectionParts.join('-');
    }
    if (!this.webcamImage || !this.courseCode || !this.section) {
      this.message = 'Please provide all fields and capture an image.';
      return;
    }
    const blob = this.dataURLtoBlob(this.webcamImage.imageAsDataUrl);
    const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
    this.api.recognizeFace(file, this.courseCode, this.section, this.selectedRoom).subscribe(
      res => this.message = res.status === 'success'
        ? `Attendance marked for ${res.student_id}`
        : res.message,
      err => this.message = 'Error connecting to backend.'
    );
  }

  dataURLtoBlob(dataurl: string) {
    const arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)![1],
      bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    for (let i = 0; i < n; i++) u8arr[i] = bstr.charCodeAt(i);
    return new Blob([u8arr], { type: mime });
  }
}
