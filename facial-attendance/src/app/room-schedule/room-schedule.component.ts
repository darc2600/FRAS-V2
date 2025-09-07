import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

const TIME_SLOTS = [
  "07:00AM - 08:10AM", "08:10AM - 09:20AM", "09:20AM - 10:30AM", "10:30AM - 11:40AM",
  "11:40AM - 12:50PM", "12:50PM - 02:00PM", "02:00PM - 03:10PM", "03:10PM - 04:20PM",
  "04:20PM - 05:30PM", "05:30PM - 06:40PM", "06:40PM - 07:50PM", "07:50PM - 09:00PM"
];
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

@Component({
  selector: 'app-room-schedule',
  templateUrl: './room-schedule.component.html',
  styleUrls: ['./room-schedule.component.css'],
})
export class RoomScheduleComponent implements OnInit {
  room = '';
  days = DAYS;
  timeSlots = TIME_SLOTS;
  grid: any[][] = this.timeSlots.map(() => this.days.map(() => null));
  message = '';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.loadSchedule();
  }

  loadSchedule() {
  if (!this.room) return;
  this.http.get<any>(`http://127.0.0.1:8000/api/schedule/${this.room}`)
      .subscribe({
        next: (data) => {
          this.grid = this.timeSlots.map(() => this.days.map(() => null));
          const scheduleList = (data && data.schedule) ? data.schedule : [];
          scheduleList.forEach((entry: any) => {
            const row = this.timeSlots.findIndex(
              t => t === `${entry.startTime} - ${entry.endTime}`
            );
            const col = this.days.findIndex(d => d === entry.day);
            if (row !== -1 && col !== -1) {
              this.grid[row][col] = {
                courseCode: entry.courseCode,
                section: entry.section,
                professor: entry.professor
              };
            }
          });
          this.message = scheduleList.length ? '' : 'No schedule found for this room.';
        },
        error: () => {
          this.grid = this.timeSlots.map(() => this.days.map(() => null));
          this.message = 'Room schedule not found.';
        }
      });
  }
}
