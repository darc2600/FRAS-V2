import { Component, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
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

  constructor(private authService: AuthService) { }

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      if (user) {
        this.isSuperAdmin = user.user_type === 'super_admin';
        this.canManageUsers = user.permissions.includes('manage_users');
        this.canConfigureSystem = user.permissions.includes('system_config');
        this.canViewAllData = user.permissions.includes('view_all_data');
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
      permission: 'system_config',
      show: () => this.canConfigureSystem
    },
    {
      label: 'Analytics',
      route: '/admin/analytics',
      icon: 'fas fa-chart-bar',
      permission: 'view_all_data',
      show: () => this.canViewAllData
    }
  ];

  get visibleMenuItems() {
    return this.menuItems.filter(item => item.show());
  }

  logout() {
    this.authService.logout();
  }
}