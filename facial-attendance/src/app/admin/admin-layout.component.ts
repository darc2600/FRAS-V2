import { Component, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { CommonModule, TitleCasePipe } from '@angular/common';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule, TitleCasePipe],
  templateUrl: './admin-layout.component.html',
  styleUrls: ['./admin-layout.component.css']
})
export class AdminLayoutComponent implements OnInit {
  currentUser: any = null;
  isSuperAdmin = false;
  canManageUsers = false;
  canConfigureSystem = false;
  canViewAllData = false;

  constructor(private authService: AuthService, private router: Router) { }

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      if (user) {
        this.isSuperAdmin = user.user_type === 'super_admin';
        this.canManageUsers = user.permissions.includes('manage_users');
        this.canConfigureSystem = user.permissions.includes('system_admin') || user.permissions.includes('manage_content');
        this.canViewAllData = user.permissions.includes('view_analytics');
      }
    });
  }

  menuItems = [
    {
      label: 'User Management',
      route: '/admin/users',
      icon: 'fas fa-users',
      permission: 'manage_users',
      show: () => this.canManageUsers
    },
    {
      label: 'System Settings',
      route: '/admin/settings',
      icon: 'fas fa-cogs',
      permission: 'system_admin',
      show: () => this.canConfigureSystem
    },
    {
      label: 'Analytics',
      route: '/admin/analytics',
      icon: 'fas fa-chart-bar',
      permission: 'view_analytics',
      show: () => this.canViewAllData
    },
    {
      label: 'Attendance Reports',
      route: '/admin/attendance-reports',
      icon: 'fas fa-file-alt',
      permission: 'view_analytics',
      show: () => this.canViewAllData
    }
  ];

  get visibleMenuItems() {
    return this.menuItems.filter(item => item.show());
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}