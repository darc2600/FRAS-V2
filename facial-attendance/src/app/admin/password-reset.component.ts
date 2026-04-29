import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../api.service';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-password-reset',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './password-reset.component.html',
  styleUrls: ['./password-reset.component.css']
})
export class PasswordResetComponent {
  email = '';
  loading = false;
  error = '';
  success = '';

  constructor(
    private apiService: ApiService,
    public authService: AuthService
  ) {}

  resetPassword(): void {
    if (!this.email) {
      this.error = 'Please enter an email address';
      return;
    }

    this.loading = true;
    this.error = '';
    this.success = '';

    this.apiService.resetPassword(this.email, 'Reset1234!').subscribe({
      next: () => {
        this.success = `Password for ${this.email} has been reset to Reset1234!`;
        this.email = '';
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to reset password: ' + (err.error?.message || err.message);
        this.loading = false;
      }
    });
  }

  hasPermission(permission: string): boolean {
    const currentUser = this.authService.getCurrentUser();
    return currentUser ? (this.authService.hasPermission(permission) || currentUser.user_type === 'super_admin') : false;
  }
}