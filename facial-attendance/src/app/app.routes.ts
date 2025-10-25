import { Routes } from '@angular/router';
import { WebcamCaptureComponent } from './webcam-capture/webcam-capture.component';
import { AttendanceMonitorComponent } from './attendance-monitor/attendance-monitor.component';
import { AttendanceLogsComponent } from './attendance-logs/attendance-logs.component';
import { RoomScheduleComponent } from './room-schedule/room-schedule.component';
import { RegisterStudentsComponent } from './register-students/register-students.component';
import { LoginComponent } from './login/login.component';
import { RegistrationComponent } from './registration/registration.component';
import { ScheduleUploadComponent } from './schedule-upload/schedule-upload.component';
import { RoomScheduleEditorComponent } from './room-schedule-editor/room-schedule-editor.component';


export const routes: Routes = [
  { path: '', redirectTo: 'monitor', pathMatch: 'full' },
  { path: 'webcam', component: WebcamCaptureComponent },
  { path: 'monitor', component: AttendanceMonitorComponent },
  { path: 'logs', component: AttendanceLogsComponent },
  { path: 'room-schedule', component: RoomScheduleComponent },
  { path: 'register-student', component: RegisterStudentsComponent },
  { path: 'upload-schedule', component: ScheduleUploadComponent },
  { path: 'room-schedule-editor', component: RoomScheduleEditorComponent },
  { path: 'login', component: LoginComponent },
  { path: 'registration', component: RegistrationComponent },
  
];
