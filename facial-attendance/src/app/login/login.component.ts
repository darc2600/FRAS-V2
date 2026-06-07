import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { LoginService } from './login.service';
import { AuthService, User } from '../auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  email = '';
  password = '';
  showPassword = false;
  error = '';
  success = '';

  constructor(
    private loginService: LoginService,
    private router: Router,
    private authService: AuthService
  ) {}

  login() {
    if (this.email && this.password) {
      this.error = '';
      this.success = '';
      this.loginService.login({
        email: this.email,
        password: this.password
      }).subscribe({
        next: (res: any) => {
          this.success = 'Login successful!';
          // Create user object and login via AuthService
          const user: User = {
            email: this.email,
            user_type: res.user_type,
            userId: res.user_id,
            token: res.access_token,
            permissions: res.permissions || []
          };
          this.authService.login(user);

          this.email = '';
          this.password = '';
          const targetRoute = this.authService.isAdmin() ? '/admin/analytics' : '/v2/classes';
          this.router.navigate([targetRoute]);
        },
        error: err => {
          this.error = err?.error?.detail || err?.error?.message || 'Invalid credentials';
        }
      });
    } else {
      this.error = 'Email and password required';
    }
  }

  togglePasswordVisibility() {
    this.showPassword = !this.showPassword;
  }
}
