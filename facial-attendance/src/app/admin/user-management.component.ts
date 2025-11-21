import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../api.service';
import { AuthService } from '../auth.service';

interface User {
  id: number;
  email: string;
  user_type: string;
  is_active: boolean;
  created_at?: string;
}

@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.css']
})
export class UserManagementComponent implements OnInit {
  users: User[] = [];
  loading = false;
  error = '';
  success = '';

  constructor(
    private apiService: ApiService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.loading = true;
    this.error = '';

    this.apiService.getUsers().subscribe({
      next: (users) => {
        this.users = users;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load users: ' + (err.error?.message || err.message);
        this.loading = false;
        // Fallback to demo data for development
        this.users = [
          { id: 1, email: 'student1@example.com', user_type: 'regular', is_active: true },
          { id: 2, email: 'student2@example.com', user_type: 'regular', is_active: true },
          { id: 3, email: 'instructor1@example.com', user_type: 'regular', is_active: true },
          { id: 4, email: 'admin@example.com', user_type: 'super_admin', is_active: true }
        ];
      }
    });
  }

  updateUserType(user: User, newType: string): void {
    if (!this.canModifyUser(user, newType)) {
      this.error = 'Insufficient permissions to modify this user type';
      return;
    }

    this.error = '';
    this.success = '';

    this.apiService.updateUser(user.id, { user_type: newType }).subscribe({
      next: () => {
        user.user_type = newType;
        this.success = `User ${user.email} updated to ${newType}`;
      },
      error: (err) => {
        this.error = 'Failed to update user: ' + (err.error?.message || err.message);
      }
    });
  }

  resetPassword(email: string): void {
    this.error = '';
    this.success = '';

    this.apiService.resetPassword(email).subscribe({
      next: () => {
        this.success = `Password reset initiated for ${email}`;
      },
      error: (err) => {
        this.error = 'Failed to reset password: ' + (err.error?.message || err.message);
      }
    });
  }

  private canModifyUser(user: User, newType: string): boolean {
    const currentUser = this.authService.getCurrentUser();
    if (!currentUser) return false;

    // Super admin can do anything
    if (currentUser.user_type === 'super_admin') return true;

    // IT admin can modify regular users but not other admins
    if (currentUser.user_type === 'it_admin') {
      return user.user_type === 'regular' && newType === 'regular';
    }

    return false;
  }

  getUserTypeOptions(currentType: string): string[] {
    const currentUser = this.authService.getCurrentUser();
    if (!currentUser) return [];

    if (currentUser.user_type === 'super_admin') {
      return ['regular', 'it_admin', 'super_admin'];
    } else if (currentUser.user_type === 'it_admin') {
      return ['regular'];
    }
    return [];
  }

  onUserTypeChange(user: User, event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.updateUserType(user, target.value);
  }

  hasPermission(permission: string): boolean {
    const currentUser = this.authService.getCurrentUser();
    return currentUser ? currentUser.permissions.includes(permission) : false;
  }
}