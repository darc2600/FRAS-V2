
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { WebcamModule, WebcamImage, WebcamInitError } from 'ngx-webcam';
import { Subject, Observable } from 'rxjs';
import { ApiService } from '../api.service';
import { CommonModule } from '@angular/common';

@Component({
  standalone: true,
  selector: 'app-webcam-capture',
  templateUrl: './webcam-capture.component.html',
  styleUrls: ['./webcam-capture.component.css'],
  imports: [FormsModule, WebcamModule, CommonModule], // ✅ Add required modules
})
export class WebcamCaptureComponent {
  courseCode = '';
  section = '';
  message = '';
  webcamImage: WebcamImage | null = null;
  private trigger: Subject<void> = new Subject<void>();

  constructor(private api: ApiService) {}

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
    if (!this.webcamImage || !this.courseCode || !this.section) {
      this.message = 'Please provide all fields and capture an image.';
      return;
    }
    const blob = this.dataURLtoBlob(this.webcamImage.imageAsDataUrl);
    const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
    this.api.recognizeFace(file, this.courseCode, this.section).subscribe(
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
