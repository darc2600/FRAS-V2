import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../auth.service';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent implements OnInit {
  // Permission-based flags
  canMonitor = false;
  canViewLogs = false;
  canRegister = false;
  canViewSchedule = false;
  canEditSchedule = false;
  canManageUsers = false;
  canConfigureSystem = false;
  canViewAnalytics = false;

  constructor(private authService: AuthService) {}

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        const permissions = user.permissions || [];

        // Check specific permissions based on database permissions
        this.canMonitor = permissions.includes('mark_attendance');
        this.canViewLogs = permissions.includes('view_attendance_logs');
        this.canRegister = permissions.includes('register_students');
        this.canViewSchedule = permissions.includes('view_own_schedule');
        this.canEditSchedule = permissions.includes('manage_rooms_schedule');
        this.canManageUsers = permissions.includes('manage_users');
        this.canConfigureSystem = permissions.includes('system_admin') || permissions.includes('manage_content');
        this.canViewAnalytics = permissions.includes('view_analytics');
      } else {
        // Reset all permissions
        this.canMonitor = false;
        this.canViewLogs = false;
        this.canRegister = false;
        this.canViewSchedule = false;
        this.canEditSchedule = false;
        this.canManageUsers = false;
        this.canConfigureSystem = false;
        this.canViewAnalytics = false;
      }
    });
  }
}
