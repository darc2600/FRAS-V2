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
  addSchedule() {
    this.message = 'Add button clicked. Implement logic as needed.';
  }
  room = '';
  message = '';
  days = DAYS;
  timeSlots = TIME_SLOTS;

  grid: ScheduleCell[][] = this.timeSlots.map(() => this.days.map(() => ({})));

  courseCode = '';
  section = '';
  professor = '';

  constructor(private http: HttpClient) {}

  loadSchedule() {
    if (!this.room) return;
  this.http.get<any>(`http://127.0.0.1:8000/api/schedule/${this.room}`)
      .subscribe(data => {
        // Reset grid
        this.grid = this.timeSlots.map(() => this.days.map(() => ({})));
        // Fill grid with loaded data
        const scheduleList = (data && data.schedule) ? data.schedule : [];
        scheduleList.forEach((entry: any) => {
          const col = this.days.findIndex(d => d === entry.day);
          if (col === -1) return;
          // Find all slots covered by this class
          let inRange = false;
          for (let row = 0; row < this.timeSlots.length; row++) {
            const [slotStart, slotEnd] = this.timeSlots[row].split(' - ');
            // If the slot matches the start or is within the range, fill it
            if (slotStart === entry.startTime) inRange = true;
            if (inRange) {
              this.grid[row][col] = {
                courseCode: entry.courseCode,
                section: entry.section,
                professor: entry.professor,
                room: this.room
              };
            }
            if (slotEnd === entry.endTime) {
              inRange = false;
            }
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
  // DELETE not supported in backend. Optionally, clear grid and show message.
  this.message = 'Delete not supported. Please clear cells manually and save.';
  this.grid = this.timeSlots.map(() => this.days.map(() => ({ })));
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
  this.http.post(`http://127.0.0.1:8000/api/schedule/${this.room}`, schedule)
      .subscribe({
        next: () => this.message = 'Schedule saved!',
        error: () => this.message = 'Failed to save schedule.'
      });
  }
}
