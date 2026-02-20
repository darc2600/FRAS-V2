import { Routes } from '@angular/router';
import { AttendanceMonitorComponent } from './attendance-monitor/attendance-monitor.component';
import { AttendanceLogsComponent } from './attendance-logs/attendance-logs.component';
import { RoomScheduleComponent } from './room-schedule/room-schedule.component';
import { RegisterStudentsComponent } from './register-students/register-students.component';
import { LoginComponent } from './login/login.component';
import { RegistrationComponent } from './registration/registration.component';
import { ScheduleUploadComponent } from './schedule-upload/schedule-upload.component';
import { RoomScheduleEditorComponent } from './room-schedule-editor/room-schedule-editor.component';
import { UserManagementComponent } from './admin/user-management.component';
import { PasswordResetComponent } from './admin/password-reset.component';
import { SystemSettingsComponent } from './admin/system-settings.component';
import { AnalyticsComponent } from './admin/analytics.component';
import { SupportTicketsComponent } from './admin/support-tickets.component';
import { AttendanceReportsComponent } from './admin/attendance-reports/attendance-reports.component';
import { SubmitSupportComponent } from './submit-support.component';
import { AuthGuard, AdminGuard, AnalyticsGuard } from './auth.guard';
import { SuperAdminGuard } from './super-admin.guard';


export const routes: Routes = [
  { path: '', redirectTo: 'monitor', pathMatch: 'full' },
  { path: 'monitor', component: AttendanceMonitorComponent, canActivate: [AuthGuard] },
  { path: 'logs', component: AttendanceLogsComponent, canActivate: [AuthGuard] },
  { path: 'room-schedule', component: RoomScheduleComponent, canActivate: [AuthGuard] },
  { path: 'register-student', component: RegisterStudentsComponent, canActivate: [AuthGuard] },
  { path: 'login', component: LoginComponent },
  { path: 'registration', component: RegistrationComponent },

  // Admin routes (no longer using AdminLayoutComponent)
  { path: 'admin/users', component: UserManagementComponent, canActivate: [AdminGuard] },
  { path: 'admin/password-reset', component: PasswordResetComponent, canActivate: [AdminGuard] },
  { path: 'admin/analytics', component: AnalyticsComponent, canActivate: [AnalyticsGuard] },
  { path: 'admin/settings', component: SystemSettingsComponent, canActivate: [SuperAdminGuard] },
  { path: 'admin/support-tickets', component: SupportTicketsComponent, canActivate: [AdminGuard] },
  { path: 'admin/attendance-reports', component: AttendanceReportsComponent, canActivate: [AnalyticsGuard] },

  // User support routes
  { path: 'submit-support', component: SubmitSupportComponent, canActivate: [AuthGuard] },

  // Admin-only routes (keeping these for backward compatibility)
  { path: 'upload-schedule', component: ScheduleUploadComponent, canActivate: [AdminGuard] },
  { path: 'room-schedule-editor', component: RoomScheduleEditorComponent, canActivate: [AdminGuard] },
];
