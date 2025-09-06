import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface ScheduleCell {
  courseCode?: string;
  section?: string;
  professor?: string;
  room?: string;
}

const TIME_SLOTS = [
  "07:00AM - 08:10AM", "08:10AM - 09:20AM", "09:20AM - 10:30AM", "10:30AM - 11:40AM",
  "11:40AM - 12:50PM", "12:50PM - 02:00PM", "02:00PM - 03:10PM", "03:10PM - 04:20PM",
  "04:20PM - 05:30PM", "05:30PM - 06:40PM", "06:40PM - 07:50PM", "07:50PM - 09:00PM"
];
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

@Component({
  selector: 'app-room-schedule-editor',
  templateUrl: './room-schedule-editor.component.html',
  styleUrls: ['./room-schedule-editor.component.css'],
})
export class RoomScheduleEditorComponent {
  room = '';
  message = '';
  days = DAYS;
  timeSlots = TIME_SLOTS;

  // 2D grid: [timeSlot][day]
  grid: ScheduleCell[][] = this.timeSlots.map(() => this.days.map(() => ({})));

  // Input fields for new entry
  courseCode = '';
  section = '';
  professor = '';

  constructor(private http: HttpClient) {}

  loadSchedule() {
    if (!this.room) return;
    this.http.get<any>(`http://127.0.0.1:8000/api/room-schedule/${this.room}`)
      .subscribe(data => {
        // Reset grid
        this.grid = this.timeSlots.map(() => this.days.map(() => ({})));
        // Fill grid with loaded data
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
              professor: entry.professor,
              room: this.room
            };
          }
        });
        console.log('Loaded schedule:', data);
      });
  }

  fillCell(row: number, col: number) {
    if (!this.courseCode || !this.section || !this.professor) {
      this.message = 'Please enter Course, Section, and Professor first.';
      return;
    }
    console.log('Filling cell:', row, col, this.courseCode, this.section, this.professor);
    this.grid[row][col] = {
      courseCode: this.courseCode,
      section: this.section,
      professor: this.professor,
      room: this.room
    };
    this.message = '';
  }

  clearCell(row: number, col: number) {
    this.grid[row][col] = {};
  }

  deleteSchedule() {
    if (!this.room) return;
    if (!confirm('Are you sure you want to delete this room schedule?')) return;
    this.http.delete(`http://127.0.0.1:8000/api/room-schedule/${this.room}`, { responseType: 'text' })
      .subscribe({
        next: () => {
          this.message = 'Schedule deleted!';
          this.grid = this.timeSlots.map(() => this.days.map(() => ({})));
        },
        error: () => this.message = 'Failed to delete schedule.'
      });
  }

  saveSchedule() {
    // Flatten grid to array of entries
    const schedule: any[] = [];
    for (let row = 0; row < this.timeSlots.length; row++) {
      for (let col = 0; col < this.days.length; col++) {
        const cell = this.grid[row][col];
        if (cell && cell.courseCode && cell.section) {
          const [startTime, endTime] = this.timeSlots[row].split(' - ');
          schedule.push({
            courseCode: cell.courseCode,
            section: cell.section,
            professor: cell.professor,
            day: this.days[col],
            startTime,
            endTime
          });
        }
      }
    }
    console.log('Saving schedule:', schedule);
    this.http.post(`http://127.0.0.1:8000/api/room-schedule/${this.room}`, schedule)
      .subscribe({
        next: () => this.message = 'Schedule saved!',
        error: () => this.message = 'Failed to save schedule.'
      });
  }
}
