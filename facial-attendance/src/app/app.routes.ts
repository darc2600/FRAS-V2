import { Routes } from '@angular/router';
import { WebcamCaptureComponent } from './webcam-capture/webcam-capture.component';
import { AttendanceMonitorComponent } from './attendance-monitor/attendance-monitor.component';
import { AttendanceLogsComponent } from './attendance-logs/attendance-logs.component';
import { RoomScheduleComponent } from './room-schedule/room-schedule.component';
import { RegistrationComponent } from './registration/registration.component';

export const routes: Routes = [
  { path: '', redirectTo: 'webcam', pathMatch: 'full' },
  { path: 'webcam', component: WebcamCaptureComponent },
  { path: 'monitor', component: AttendanceMonitorComponent },
  { path: 'logs', component: AttendanceLogsComponent },
  { path: 'room-schedule', component: RoomScheduleComponent },
  { path: 'register-student', component: RegistrationComponent }
];
