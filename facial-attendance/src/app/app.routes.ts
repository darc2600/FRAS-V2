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
import { V2TodaysClassesComponent } from './v2/pages/todays-classes/todays-classes.component';
import { V2LiveSessionComponent } from './v2/pages/live-session/live-session.component';
import { V2PostSessionReviewPlaceholderComponent } from './v2/pages/post-session-review-placeholder/post-session-review-placeholder.component';
import { AuthGuard, AdminGuard, AnalyticsGuard } from './auth.guard';
import { SuperAdminGuard } from './super-admin.guard';


export const routes: Routes = [
  { path: '', redirectTo: 'v2/classes', pathMatch: 'full' },
  { path: 'monitor', component: AttendanceMonitorComponent, canActivate: [AuthGuard] },
  { path: 'logs', component: AttendanceLogsComponent, canActivate: [AuthGuard] },
  { path: 'room-schedule', component: RoomScheduleComponent, canActivate: [AuthGuard] },
  { path: 'register-student', component: RegisterStudentsComponent, canActivate: [AuthGuard] },
  { path: 'login', component: LoginComponent },
  { path: 'registration', component: RegistrationComponent },
  { path: 'v2/classes', component: V2TodaysClassesComponent, canActivate: [AuthGuard] },
  { path: 'v2/today', redirectTo: 'v2/classes', pathMatch: 'full' },
  { path: 'v2/schedule', component: V2TodaysClassesComponent, canActivate: [AuthGuard] },
  { path: 'live-session/:sessionId', component: V2LiveSessionComponent, canActivate: [AuthGuard] },
  { path: 'v2/sessions/:sessionId/review', component: V2PostSessionReviewPlaceholderComponent, canActivate: [AuthGuard] },

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
