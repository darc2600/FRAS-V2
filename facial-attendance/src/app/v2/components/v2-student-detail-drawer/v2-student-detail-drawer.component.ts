import { Component, EventEmitter, Input, Output } from '@angular/core';
import { V2ManualAttendanceStatus } from '../../models/v2-attendance.models';
import { V2StatusTone } from '../v2-status-badge/v2-status-badge.component';

@Component({
  selector: 'app-v2-student-detail-drawer',
  templateUrl: './v2-student-detail-drawer.component.html',
  styleUrls: ['./v2-student-detail-drawer.component.scss']
})
export class V2StudentDetailDrawerComponent {
  @Input() open = false;
  @Input() studentName = '';
  @Input() studentNumber = '';
  @Input() currentStatus = '';
  @Input() currentStatusTone: V2StatusTone = 'neutral';
  @Input() timeIn = '';
  @Input() presenceDuration = '';
  @Input() outsideDuration = '';
  @Input() breakCount = 0;
  @Input() breakLimitMinutes = 10;
  @Input() activeBreakTimerLabel = '';
  @Input() isStudentOut = false;
  @Input() eventLog: Array<{ time: string; label: string }> = [];
  @Output() closeDrawer = new EventEmitter<void>();
  @Output() markExcused = new EventEmitter<void>();
  @Output() bathroomBreak = new EventEmitter<void>();
  @Output() breakLimitMinutesChange = new EventEmitter<number>();
  @Output() overrideStatus = new EventEmitter<V2ManualAttendanceStatus>();
  @Output() updateStatus = new EventEmitter<void>();
  overrideOpen = false;

  toggleOverride(): void {
    this.overrideOpen = !this.overrideOpen;
  }

  selectOverride(status: V2ManualAttendanceStatus): void {
    this.overrideStatus.emit(status);
    this.overrideOpen = false;
  }
}
