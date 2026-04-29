import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../api.service';
import { AuthService } from '../auth.service';

interface User {
  id: number;
  email: string;
  user_type: string;
  original_user_type?: string;
  can_change_role?: boolean;
  role_change_block_reason?: string;
  role?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  first_name?: string;
  last_name?: string;
}

interface ApiErrorPayload {
  detail?: string;
  message?: string;
  error?: string;
}

interface CreateUserRequest {
  email: string;
  password: string;
  user_type: string;
  first_name?: string;
  last_name?: string;
  employee_number?: string;
  dept_id?: number;
}

@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.css']
})
export class UserManagementComponent implements OnInit {
  users: User[] = [];
  filteredUsers: User[] = [];
  loading = false;
  error = '';
  success = '';

  // Search and filter
  searchTerm = '';
  selectedUserType = '';
  selectedStatus = '';
  showFilters = false;

  // Add user form
  showCreateForm = false;
  newUser: CreateUserRequest = {
    email: '',
    password: '',
    user_type: 'instructor',
    first_name: '',
    last_name: '',
    employee_number: '',
    dept_id: 1
  };

  // Bulk operations
  selectedUsers: Set<number> = new Set();
  selectAll = false;

  constructor(
    private apiService: ApiService,
    public authService: AuthService
  ) {}

  private getErrorMessage(err: any, fallback: string): string {
    const payload = (err?.error || {}) as ApiErrorPayload;
    return payload.detail || payload.message || payload.error || err?.message || fallback;
  }

  ngOnInit(): void {
    this.loadUsers();
    this.newUser.user_type = this.authService.getCurrentUser()?.user_type || 'instructor';
  }

  loadUsers(): void {
    this.loading = true;
    this.error = '';

    this.apiService.getUsers().subscribe({
      next: (users) => {
        this.users = users.map(user => ({
          ...user,
          original_user_type: user.user_type,
          role: user.user_type // Map user_type to role for consistency
        }));
        this.applyFilters();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load users: ' + this.getErrorMessage(err, 'Unknown error');
        this.loading = false;
        // Fallback to demo data for development
        this.users = [
          { id: 1, email: 'student1@example.com', user_type: 'regular', role: 'regular', is_active: true, first_name: 'John', last_name: 'Doe' },
          { id: 2, email: 'student2@example.com', user_type: 'regular', role: 'regular', is_active: true, first_name: 'Jane', last_name: 'Smith' },
          { id: 3, email: 'instructor1@example.com', user_type: 'regular', role: 'regular', is_active: true, first_name: 'Bob', last_name: 'Johnson' },
          { id: 4, email: 'admin@example.com', user_type: 'super_admin', role: 'super_admin', is_active: true, first_name: 'Super', last_name: 'Admin' },
          { id: 5, email: 'itadmin@example.com', user_type: 'it_admin', role: 'it_admin', is_active: true, first_name: 'IT', last_name: 'Admin' }
        ];
        this.applyFilters();
      }
    });
  }

  applyFilters(): void {
    let filtered = this.users.filter(user => {
      const matchesSearch = !this.searchTerm ||
        user.email.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        (user.first_name + ' ' + user.last_name).toLowerCase().includes(this.searchTerm.toLowerCase());

      const matchesType = !this.selectedUserType || user.user_type === this.selectedUserType;
      const matchesStatus = this.selectedStatus === '' ||
        (this.selectedStatus === 'active' && user.is_active) ||
        (this.selectedStatus === 'inactive' && !user.is_active);

      return matchesSearch && matchesType && matchesStatus;
    });

    // Sort by user_type alphabetically, then by name within each type
    filtered.sort((a, b) => {
      // First sort by user_type
      if (a.user_type !== b.user_type) {
        return a.user_type.localeCompare(b.user_type);
      }
      // Then sort by name (first_name + last_name)
      const nameA = `${a.first_name || ''} ${a.last_name || ''}`.trim();
      const nameB = `${b.first_name || ''} ${b.last_name || ''}`.trim();
      return nameA.localeCompare(nameB);
    });

    this.filteredUsers = filtered;
  }

  get activeFilterCount(): number {
    let count = 0;
    if (this.searchTerm.trim()) count++;
    if (this.selectedUserType) count++;
    if (this.selectedStatus) count++;
    return count;
  }

  toggleFilters(): void {
    this.showFilters = !this.showFilters;
  }

  clearFilters(): void {
    this.searchTerm = '';
    this.selectedUserType = '';
    this.selectedStatus = '';
    this.applyFilters();
  }

  onSearchChange(): void {
    this.applyFilters();
  }

  onFilterChange(): void {
    this.applyFilters();
  }

  createUser(): void {
    if (!this.validateNewUser()) return;

    this.error = '';
    this.success = '';

    this.apiService.createUser(this.newUser).subscribe({
      next: (response) => {
        this.success = `User ${this.newUser.email} added successfully`;
        this.showCreateForm = false;
        this.resetNewUserForm();
        this.loadUsers(); // Reload to show new user
      },
      error: (err) => {
        this.error = 'Failed to add user: ' + this.getErrorMessage(err, 'Unknown error');
      }
    });
  }

  private validateNewUser(): boolean {
    if (!this.newUser.email || !this.newUser.password || !this.newUser.user_type) {
      this.error = 'Email, password, and user type are required';
      return false;
    }

    if (this.newUser.password.length < 6) {
      this.error = 'Password must be at least 6 characters long';
      return false;
    }

    // Validate employee number for admin types
    if ((this.newUser.user_type === 'it_admin' || this.newUser.user_type === 'super_admin') && !this.newUser.employee_number) {
      this.error = 'Employee number is required for admin accounts';
      return false;
    }

    return true;
  }

  resetNewUserForm(): void {
    this.newUser = {
      email: '',
      password: '',
      user_type: this.authService.getCurrentUser()?.user_type || 'instructor',
      first_name: '',
      last_name: '',
      employee_number: '',
      dept_id: 1
    };
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
        user.original_user_type = newType;
        user.role = newType;
        this.success = `User ${user.email} updated to ${newType}`;
        this.applyFilters(); // Re-apply filters in case user type changed
      },
      error: (err) => {
        this.error = 'Failed to update user: ' + this.getErrorMessage(err, 'Unknown error');
      }
    });
  }

  deleteUser(user: User): void {
    if (!confirm(`Are you sure you want to delete user ${user.email}? This action cannot be undone.`)) {
      return;
    }

    this.error = '';
    this.success = '';

    this.apiService.deleteUser(user.id).subscribe({
      next: () => {
        this.success = `User ${user.email} deleted successfully`;
        this.loadUsers();
      },
      error: (err) => {
        this.error = 'Failed to delete user: ' + this.getErrorMessage(err, 'Unknown error');
      }
    });
  }

  resetPassword(email: string): void {
    const newPassword = prompt('Enter new password for ' + email + ':');
    if (!newPassword) return;

    if (newPassword.length < 6) {
      this.error = 'Password must be at least 6 characters long';
      return;
    }

    this.error = '';
    this.success = '';

    this.apiService.resetPassword(email, newPassword).subscribe({
      next: () => {
        this.success = `Password reset successfully for ${email}`;
      },
      error: (err) => {
        this.error = 'Failed to reset password: ' + this.getErrorMessage(err, 'Unknown error');
      }
    });
  }

  // Bulk operations
  toggleSelectAll(): void {
    if (this.selectAll) {
      this.selectedUsers.clear();
    } else {
      this.selectedUsers = new Set(this.filteredUsers.map(u => u.id));
    }
    this.selectAll = !this.selectAll;
  }

  toggleUserSelection(userId: number): void {
    if (this.selectedUsers.has(userId)) {
      this.selectedUsers.delete(userId);
    } else {
      this.selectedUsers.add(userId);
    }
    this.selectAll = this.selectedUsers.size === this.filteredUsers.length;
  }

  bulkDeactivate(): void {
    if (this.selectedUsers.size === 0) {
      this.error = 'No users selected';
      return;
    }

    if (!confirm(`Deactivate ${this.selectedUsers.size} selected users?`)) return;

    this.bulkOperation('deactivate', Array.from(this.selectedUsers));
  }

  bulkActivate(): void {
    if (this.selectedUsers.size === 0) {
      this.error = 'No users selected';
      return;
    }

    if (!confirm(`Activate ${this.selectedUsers.size} selected users?`)) return;

    this.bulkOperation('activate', Array.from(this.selectedUsers));
  }

  bulkDelete(): void {
    if (this.selectedUsers.size === 0) {
      this.error = 'No users selected';
      return;
    }

    if (!confirm(`Delete ${this.selectedUsers.size} selected users? This action cannot be undone.`)) return;

    this.bulkOperation('delete', Array.from(this.selectedUsers));
  }

  private bulkOperation(operation: string, userIds: number[]): void {
    this.error = '';
    this.success = '';

    this.apiService.bulkUserOperation(operation, userIds).subscribe({
      next: (response) => {
        this.success = `Bulk ${operation} completed successfully for ${userIds.length} users`;
        this.selectedUsers.clear();
        this.selectAll = false;
        this.loadUsers();
      },
      error: (err) => {
        this.error = 'Bulk operation failed: ' + this.getErrorMessage(err, 'Unknown error');
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
    if (!currentUser) return [currentType];

    let allowed: string[] = [];
    if (currentUser.user_type === 'super_admin') {
      allowed = ['instructor', 'it_admin', 'super_admin'];
    } else if (currentUser.user_type === 'it_admin') {
      allowed = ['instructor'];
    }

    if (!allowed.includes(currentType)) {
      allowed = [currentType, ...allowed];
    }
    return allowed;
  }

  onUserTypeChange(user: User, event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.updateUserType(user, target.value);
  }

  saveUserRole(user: User): void {
    const nextType = user.user_type;
    const originalType = user.original_user_type || user.user_type;

    if (!nextType || nextType === originalType) {
      return;
    }

    this.updateUserType(user, nextType);
  }

  hasPendingRoleChange(user: User): boolean {
    if (user.can_change_role === false) {
      return false;
    }
    return !!user.user_type && !!user.original_user_type && user.user_type !== user.original_user_type;
  }

  hasPermission(permission: string): boolean {
    return this.authService.hasPermission(permission);
  }

  getUserTypeDisplayName(userType: string): string {
    switch (userType) {
      case 'instructor': return 'Instructor';
      case 'it_admin': return 'Admin';
      case 'super_admin': return 'Super Admin';
      default: return userType;
    }
  }
}