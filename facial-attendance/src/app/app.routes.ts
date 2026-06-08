import { Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import { V2TodaysClassesComponent } from './v2/pages/todays-classes/todays-classes.component';
import { V2LiveSessionComponent } from './v2/pages/live-session/live-session.component';
import { AuthGuard, SessionBreakGuard } from './auth.guard';


export const routes: Routes = [
  { path: '', redirectTo: 'v2/classes', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'v2/classes', component: V2TodaysClassesComponent, canActivate: [AuthGuard, SessionBreakGuard] },
  { path: 'v2/today', redirectTo: 'v2/classes', pathMatch: 'full' },
  { path: 'v2/schedule', component: V2TodaysClassesComponent, canActivate: [AuthGuard, SessionBreakGuard] },
  { path: 'live-session/:sessionId', component: V2LiveSessionComponent, canActivate: [AuthGuard, SessionBreakGuard], canDeactivate: [SessionBreakGuard] },
  {
    path: 'session-review',
    canActivate: [AuthGuard, SessionBreakGuard],
    loadChildren: () => import('./v2/pages/post-session-review/post-session-review.module').then(m => m.V2PostSessionReviewModule)
  },
  {
    path: 'student-evidence',
    canActivate: [AuthGuard, SessionBreakGuard],
    loadChildren: () => import('./v2/pages/student-evidence/student-evidence.module').then(m => m.V2StudentEvidenceModule)
  },
  {
    path: 'classes/:classId/session-history',
    canActivate: [AuthGuard, SessionBreakGuard],
    loadChildren: () => import('./v2/pages/session-history/session-history.module').then(m => m.V2SessionHistoryModule)
  },
  {
    path: 'classes/:classId/students',
    canActivate: [AuthGuard, SessionBreakGuard],
    loadChildren: () => import('./v2/pages/class-roster/class-roster.module').then(m => m.V2ClassRosterModule)
  },
  {
    path: 'classes/:classId/students/:studentId/history',
    canActivate: [AuthGuard, SessionBreakGuard],
    loadChildren: () => import('./v2/pages/student-class-history/student-class-history.module').then(m => m.V2StudentClassHistoryModule)
  },
  {
    path: 'classes/:classId/students/:studentId/face-profile',
    canActivate: [AuthGuard, SessionBreakGuard],
    loadChildren: () => import('./v2/pages/face-profile/face-profile.module').then(m => m.V2FaceProfileModule)
  },
  {
    path: 'v2/classes/:classId/students',
    canActivate: [AuthGuard, SessionBreakGuard],
    loadChildren: () => import('./v2/pages/class-roster/class-roster.module').then(m => m.V2ClassRosterModule)
  },
  {
    path: 'v2/classes/:classId/students/:studentId/history',
    canActivate: [AuthGuard, SessionBreakGuard],
    loadChildren: () => import('./v2/pages/student-class-history/student-class-history.module').then(m => m.V2StudentClassHistoryModule)
  },
  {
    path: 'v2/classes/:classId/students/:studentId/face-profile',
    canActivate: [AuthGuard, SessionBreakGuard],
    loadChildren: () => import('./v2/pages/face-profile/face-profile.module').then(m => m.V2FaceProfileModule)
  },
  {
    path: 'session-history',
    canActivate: [AuthGuard, SessionBreakGuard],
    loadChildren: () => import('./v2/pages/session-history/session-history.module').then(m => m.V2SessionHistoryModule)
  },
  { path: 'v2/history', redirectTo: '/session-history' },
  { path: 'v2/sessions/:sessionId/review', redirectTo: '/session-review/:sessionId' },
  { path: '**', redirectTo: 'v2/classes' },
];
