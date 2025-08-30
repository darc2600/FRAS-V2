import { Component, OnInit } from '@angular/core';
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
export class AttendanceLogsComponent implements OnInit {
  room = '';
  availableRooms: string[] = [];
  courseCode = '';
  section = '';
  logs: any[] = [];
  message = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getRooms().subscribe(
      (rooms: string[]) => {
        this.availableRooms = rooms;
        if (rooms.length > 0) {
          this.room = rooms[0];
        }
      },
      err => this.message = 'Error fetching rooms.'
    );
  }

  fetchLogs() {
    if (!this.room || !this.courseCode || !this.section) {
      this.message = 'Please enter room, course code, and section.';
      return;
    }
    this.api.getAttendance(this.courseCode, this.section, this.room).subscribe(
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
