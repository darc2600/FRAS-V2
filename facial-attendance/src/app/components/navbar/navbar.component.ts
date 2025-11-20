import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../auth.service';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent implements OnInit {
  isAdmin = false;
  isInstructor = false;
  isSuperAdmin = false;
  canManageUsers = false;
  canConfigureSystem = false;

  constructor(private authService: AuthService) {}

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.isAdmin = user.user_type === 'it_admin' || user.user_type === 'super_admin';
        this.isSuperAdmin = user.user_type === 'super_admin';
        this.isInstructor = user.user_type === 'instructor' || user.user_type === 'regular';
        this.canManageUsers = user.permissions.includes('manage_users');
        this.canConfigureSystem = user.permissions.includes('system_config');
      } else {
        this.isAdmin = false;
        this.isInstructor = false;
        this.isSuperAdmin = false;
        this.canManageUsers = false;
        this.canConfigureSystem = false;
      }
    });
  }
}
