import { Component } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-attendance-logs',
  templateUrl: './attendance-logs.component.html',
  styleUrls: ['./attendance-logs.component.css']
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
      res => this.logs = res.attendance,
      err => this.message = 'Error fetching logs.'
    );
  }
}
