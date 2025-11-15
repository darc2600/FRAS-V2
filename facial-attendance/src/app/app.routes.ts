import { Routes } from '@angular/router';
import { AttendanceMonitorComponent } from './attendance-monitor/attendance-monitor.component';
import { AttendanceLogsComponent } from './attendance-logs/attendance-logs.component';
import { RoomScheduleComponent } from './room-schedule/room-schedule.component';
import { RegisterStudentsComponent } from './register-students/register-students.component';
import { LoginComponent } from './login/login.component';
import { RegistrationComponent } from './registration/registration.component';
import { ScheduleUploadComponent } from './schedule-upload/schedule-upload.component';
import { RoomScheduleEditorComponent } from './room-schedule-editor/room-schedule-editor.component';
import { AuthGuard, AdminGuard } from './auth.guard';


export const routes: Routes = [
  { path: '', redirectTo: 'monitor', pathMatch: 'full' },
  { path: 'monitor', component: AttendanceMonitorComponent, canActivate: [AuthGuard] },
  { path: 'logs', component: AttendanceLogsComponent, canActivate: [AuthGuard] },
  { path: 'room-schedule', component: RoomScheduleComponent, canActivate: [AuthGuard] },
  { path: 'register-student', component: RegisterStudentsComponent, canActivate: [AuthGuard] },
  { path: 'upload-schedule', component: ScheduleUploadComponent, canActivate: [AdminGuard] },
  { path: 'room-schedule-editor', component: RoomScheduleEditorComponent, canActivate: [AdminGuard] },
  { path: 'login', component: LoginComponent },
  { path: 'registration', component: RegistrationComponent },

];
