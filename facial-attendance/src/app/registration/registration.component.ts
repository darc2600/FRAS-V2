import { Component } from '@angular/core';
import { RegistrationService } from './registration.service';
import { Router } from '@angular/router';
import { AuthService, User } from '../auth.service';

@Component({
  selector: 'app-registration',
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css'],
})
export class RegistrationComponent {
  // Simple registration fields
  password = '';
  email = '';
  error = '';
  success = '';
  showPassword = false;

  constructor(
    private regSvc: RegistrationService,
    private router: Router,
    private authService: AuthService
  ) {}

  // Simple JSON registration
  register() {
    this.error = '';
    this.success = '';
    if (!this.password || !this.email) {
      this.error = 'Email and password are required';
      return;
    }
    // Password validation: at least 1 uppercase, 1 number, or 1 special character
    const hasUpper = /[A-Z]/.test(this.password);
    const hasNumber = /\d/.test(this.password);
    const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(this.password);
    if (!hasUpper && !hasNumber && !hasSpecial) {
      this.error = 'Password must contain at least one uppercase letter, number, or special character';
      return;
    }
    this.regSvc.register({ email: this.email, password: this.password }).subscribe({
      next: (res: any) => {
        if (res.error) {
          this.error = res.error;
          return;
        }
        this.success = 'Registration successful! User saved.';
        this.password = '';
        this.email = '';
        // Do not auto-login, let user login separately
      },
      error: (err: any) => {
        this.error = err?.error?.message || 'Registration failed.';
      }
    });
  }
}