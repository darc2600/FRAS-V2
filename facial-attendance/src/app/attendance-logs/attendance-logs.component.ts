
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-attendance-logs',
  templateUrl: './attendance-logs.component.html',
  styleUrls: ['./attendance-logs.component.css'],
})
export class AttendanceLogsComponent implements OnInit {
  availableFloors: number[] = [];
  selectedFloor: number | null = null;
  allRooms: any[] = [];
  availableRooms: string[] = [];
  filteredRooms: string[] = [];
  roomSearch = '';
  showRoomDropdown = false;
  room = '';
  availableCourseSections: string[] = [];
  courseSection = '';
  logs: any[] = [];
  message = '';
  loading = false;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getRooms().subscribe(
      (rooms: any[]) => {
        this.allRooms = rooms;
        this.availableFloors = Array.from(new Set(rooms.map(r => r.floor_level).filter(f => f != null))).sort((a, b) => a - b);
        if (this.availableFloors.length > 0) {
          this.selectedFloor = this.availableFloors[0];
          this.filterRoomsByFloor();
        } else {
          this.availableRooms = rooms.map(r => r.room_id || r.id || r.name);
          this.filteredRooms = this.availableRooms;
        }
      },
      err => this.message = 'Error fetching rooms.'
    );
  }

  filterRoomsByFloor() {
    if (this.selectedFloor == null) {
      this.availableRooms = [];
      this.filteredRooms = [];
      return;
    }
    const roomsOnFloor = this.allRooms.filter(r => r.floor_level === this.selectedFloor).map(r => r.room_id);
    this.availableRooms = roomsOnFloor;
    this.filteredRooms = roomsOnFloor;
    if (roomsOnFloor.length > 0) {
      this.room = roomsOnFloor[0];
      this.fetchCourseSections();
    } else {
      this.room = '';
      this.availableCourseSections = [];
      this.courseSection = '';
    }
  }

  onRoomSearchChange() {
    if (!this.roomSearch) {
      this.filteredRooms = this.availableRooms;
      this.showRoomDropdown = false;
      return;
    }
    this.filteredRooms = this.availableRooms.filter(r =>
      (r || '').toLowerCase().includes(this.roomSearch.toLowerCase())
    );
    this.showRoomDropdown = true;
  }

  selectRoom(room: string) {
    this.room = room;
    this.roomSearch = room;
    this.showRoomDropdown = false;
    this.fetchCourseSections();
  }

  onRoomInputBlur() {
    setTimeout(() => {
      this.showRoomDropdown = false;
    }, 200);
  }

  fetchCourseSections() {
    if (!this.room) {
      this.availableCourseSections = [];
      this.courseSection = '';
      return;
    }
    this.api.getRoomSchedule(this.room).subscribe(
      (result: any) => {
        if (result && Array.isArray(result.schedule)) {
          const pairs = result.schedule.map((cls: any) => `${cls.course_code || cls.courseCode} - ${cls.section}`);
          this.availableCourseSections = Array.from(new Set(pairs));
          this.courseSection = this.availableCourseSections[0] || '';
        } else {
          this.availableCourseSections = [];
          this.courseSection = '';
        }
        this.fetchLogs();
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
        this.logs = (res.attendance || []).map((log: any) => ({
          studentId: log[0],
          studentName: log[1],
          time: log[2],
          status: log[3] || 'Unknown'
        }));
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

  getStatusClass(status: string) {
    if (status === 'Present') return 'present';
    if (status === 'Late') return 'late';
    if (status === 'Absent') return 'absent';
    return '';
  }

  formatDateTime(dt: string): string {
    const d = new Date(dt);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
  }
}
