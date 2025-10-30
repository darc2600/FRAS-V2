import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { LoginService } from './login.service';

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

  constructor(private loginService: LoginService, private router: Router) {}

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
          // persist token/email for later API calls
          try {
            if (res?.token) {
              localStorage.setItem('authToken', res.token);
            }
            const returnedEmail = res?.email ?? this.email;
            localStorage.setItem('authEmail', returnedEmail);
          } catch (e) {
            // ignore storage errors
          }
          this.email = '';
          this.password = '';
          // navigate to webcam capture page
          this.router.navigate(['/webcam']);
        },
        error: err => {
          this.error = err?.error?.message || 'Invalid credentials';
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
