import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-schedule-upload',
  standalone: true,
  templateUrl: './schedule-upload.component.html',
  styleUrls: ['./schedule-upload.component.css'],
  imports: [FormsModule, CommonModule],
})
export class ScheduleUploadComponent {
  studentId = '';
  file?: File;
  message = '';
  extractedText = '';

  constructor(private http: HttpClient) {}

  onFileChange(event: any) {
    this.file = event.target.files[0];
  }

  upload() {
    if (!this.studentId || !this.file) {
      this.message = 'Please enter your student number and select an image file.';
      return;
    }
    const formData = new FormData();
    formData.set('student_id', this.studentId);
    formData.set('file', this.file);
    this.http.post<any>('http://127.0.0.1:8000/api/upload-schedule-image', formData)
      .subscribe({
        next: (res) => {
          if (res.status === 'success') {
            this.message = `Uploaded! ${res.count} schedule entries saved.`;
          } else {
            this.message = res.message || 'Upload failed.';
          }
          this.extractedText = res.extracted_text || '';
        },
        error: () => this.message = 'Upload failed.'
      });
  }
}
