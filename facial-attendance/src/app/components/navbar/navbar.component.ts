import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../auth.service';
import { Router } from '@angular/router';
import { Input } from '@angular/core';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent implements OnInit {
  @Input() isOpen = true;
  userName = 'Prof. Maria Santos';
  userRole = 'SOIT';
  userInitials = 'MS';

  // Permission-based flags
  canMonitor = false;
  canViewLogs = false;
  canRegister = false;
  canViewSchedule = false;
  canEditSchedule = false;
  canManageUsers = false;
  canResetPasswords = false;
  canConfigureSystem = false;
  canViewAnalytics = false;
  canViewReports = false;
  canSubmitSupport = false;
  canManageSupport = false;

  constructor(private authService: AuthService, private router: Router) {}

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.userName = this.displayNameFromEmail(user.email);
        this.userRole = user.user_type === 'super_admin' ? 'System Administrator' : user.user_type === 'it_admin' ? 'IT Administrator' : 'SOIT';
        this.userInitials = this.initialsFromName(this.userName);

        const permissions = user.permissions || [];
        const isSuperAdmin = user.user_type === 'super_admin';

        // Check specific permissions based on database permissions or super admin status
        this.canMonitor = permissions.includes('mark_attendance');
        this.canViewLogs = permissions.includes('view_attendance_logs');
        this.canRegister = permissions.includes('register_students');
        this.canViewSchedule = permissions.includes('view_own_schedule');
        this.canEditSchedule = permissions.includes('manage_rooms_schedule') || isSuperAdmin;
        this.canManageUsers = permissions.includes('manage_users') || isSuperAdmin;
        this.canResetPasswords = permissions.includes('reset_passwords') || permissions.includes('manage_users') || isSuperAdmin;
        this.canConfigureSystem = (permissions.includes('system_admin') || permissions.includes('manage_content')) || isSuperAdmin;
        this.canViewAnalytics = permissions.includes('view_analytics') || permissions.includes('view_all_data') || isSuperAdmin;
        this.canViewReports = permissions.includes('view_all_data') || this.canViewAnalytics || isSuperAdmin;
        this.canSubmitSupport = permissions.includes('submit_support');
        this.canManageSupport = permissions.includes('manage_support') || isSuperAdmin;
      } else {
        this.userName = 'Prof. Maria Santos';
        this.userRole = 'SOIT';
        this.userInitials = 'MS';

        // Reset all permissions
        this.canMonitor = false;
        this.canViewLogs = false;
        this.canRegister = false;
        this.canViewSchedule = false;
        this.canEditSchedule = false;
        this.canManageUsers = false;
        this.canResetPasswords = false;
        this.canConfigureSystem = false;
        this.canViewAnalytics = false;
        this.canViewReports = false;
        this.canSubmitSupport = false;
        this.canManageSupport = false;
      }
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  private displayNameFromEmail(email: string): string {
    if (!email) return 'Prof. Maria Santos';
    if (email.toLowerCase().includes('maria.santos')) return 'Prof. Maria Santos';
    const localPart = email.split('@')[0] || email;
    const words = localPart.split(/[._-]+/).filter(Boolean);
    const name = words.map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    return name ? `Prof. ${name}` : 'Prof. Maria Santos';
  }

  private initialsFromName(name: string): string {
    const words = name.replace(/^Prof\.\s*/i, '').split(/\s+/).filter(Boolean);
    return words.slice(0, 2).map(word => word.charAt(0).toUpperCase()).join('') || 'MS';
  }
}
