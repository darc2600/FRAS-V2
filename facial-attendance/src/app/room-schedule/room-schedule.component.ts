import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

interface ClassSchedule {
  courseCode: string;
  section: string;
  startTime: string;
  endTime: string;
  present: number;
  late: number;
  absent: number;
}

@Component({
  selector: 'app-room-schedule',
  standalone: true,
  templateUrl: './room-schedule.component.html',
  styleUrls: ['./room-schedule.component.css'],
  imports: [CommonModule]
})
export class RoomScheduleComponent implements OnInit {
  roomNumber = "RO 305";
  currentDateTime: Date = new Date();

  schedules: ClassSchedule[] = [
    { courseCode: 'IT123L', section: 'AM-8', startTime: '10:00', endTime: '13:30', present: 34, late: 12, absent: 5 },
    { courseCode: 'IT124L', section: 'PM-2', startTime: '14:00', endTime: '17:30', present: 28, late: 6, absent: 10 },
    { courseCode: 'IT200L', section: 'AM-9', startTime: '09:00', endTime: '12:00', present: 40, late: 4, absent: 2 }
  ];

  selectedClass?: ClassSchedule;

  ngOnInit() {
    this.updateDateTime();
    setInterval(() => this.updateDateTime(), 1000);

    this.highlightCurrentClass();
  }

  updateDateTime() {
    this.currentDateTime = new Date();
    this.highlightCurrentClass();
  }

  highlightCurrentClass() {
    const now = this.getTimeInMinutes(this.currentDateTime);
    this.selectedClass = this.schedules.find(cls => {
      const start = this.getTimeInMinutesFromStr(cls.startTime);
      const end = this.getTimeInMinutesFromStr(cls.endTime);
      return now >= start && now <= end;
    });
  }

  selectClass(cls: ClassSchedule) {
    this.selectedClass = cls;
  }

  private getTimeInMinutes(date: Date): number {
    return date.getHours() * 60 + date.getMinutes();
  }

  private getTimeInMinutesFromStr(time: string): number {
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
  }
}
