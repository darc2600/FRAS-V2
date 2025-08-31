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

  selectedFloor: number | null = null;
  availableFloors: number[] = [1, 2, 3, 4, 5, 6, 7];
  floorRooms: { [floor: number]: string[] } = {
    1: ['101', '102', '103', '104', '105'],
    2: ['201', '202', '203', '204', '205'],
    3: ['301', '302', '303', '304', '305'],
    4: ['401', '402', '403', '404', '405'],
    5: ['501', '502', '503', '504', '505'],
    6: ['601', '602', '603', '604', '605'],
    7: ['701', '702', '703', '704', '705'],
  };
  filteredRooms: string[] = [];
  availableCourseSections: string[] = [];
  courseSection = '';
  loading = false;
  roomsWithFloors: any[] = [];
  dynamicFloors: number[] = [1, 2, 3, 4, 5, 6, 7];
  dynamicRooms: any[] = [];

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getRoomsWithFloors().subscribe(
      (rooms: any[]) => {
        this.roomsWithFloors = rooms;
        // Always show floors 1-7
        this.selectedFloor = this.dynamicFloors[0];
        this.onFloorChange();
      },
      err => this.message = 'Error fetching rooms/floors.'
    );
  }

  onFloorChange() {
    if (this.selectedFloor) {
      this.dynamicRooms = this.roomsWithFloors.filter(r => r.floor === this.selectedFloor);
      this.room = this.dynamicRooms[0]?.room || '';
      this.onRoomChange();
    }
  }

  onRoomChange() {
    if (!this.room) {
      this.availableCourseSections = [];
      this.courseSection = '';
      return;
    }
    this.api.getCourseSections(this.room).subscribe(
      (pairs: string[]) => {
        this.availableCourseSections = pairs;
        this.courseSection = pairs[0] || '';
        this.logs = [];
      },
      err => this.message = 'Error fetching course-sections.'
    );
  }

  onCourseSectionChange() {
    this.fetchLogs();
  }

  fetchLogs() {
    if (!this.courseSection || !this.room) {
      this.logs = [];
      this.message = 'Please select room and course-section.';
      return;
    }
    const [courseCode, section] = this.courseSection.split(' - ');
    this.loading = true;
    this.api.getAttendance(courseCode, section, this.room).subscribe(
      res => {
        this.logs = res.attendance;
        this.loading = false;
        if (!this.logs || this.logs.length === 0) {
          this.message = 'No records found.';
        } else {
          this.message = '';
        }
      },
      err => {
        this.message = 'Error fetching logs.';
        this.loading = false;
      }
    );
  }

  // Helper to format date/time
  formatDateTime(dt: string): string {
    const d = new Date(dt);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
  }

  // Helper to get status (for now, always 'Present')
  getStatus(log: any): string {
    // You can enhance this logic if you have more status info
    return 'Present';
  }
}
