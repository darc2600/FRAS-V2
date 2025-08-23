import { Component } from '@angular/core';
import { ApiService } from '../api.service';
import { FormsModule } from '@angular/forms';
import { WebcamModule } from 'ngx-webcam';
import { CommonModule } from '@angular/common';


@Component({
  standalone: true,
  selector: 'app-attendance-logs',
  templateUrl: './attendance-logs.component.html',
  styleUrls: ['./attendance-logs.component.css'],
  imports: [FormsModule, WebcamModule, CommonModule],
})
export class AttendanceLogsComponent {
  courseCode = '';
  section = '';
  logs: any[] = [];
  message = '';

  constructor(private api: ApiService) {}

  fetchLogs() {
    if (!this.courseCode || !this.section) {
      this.message = 'Please enter course code and section.';
      return;
    }
    this.api.getAttendance(this.courseCode, this.section).subscribe(
      res => {
        this.logs = res.attendance;
        if (!this.logs || this.logs.length === 0) {
          this.message = 'No records found.';
        } else {
          this.message = '';
        }
      },
      err => this.message = 'Error fetching logs.'
    );
  }
}
