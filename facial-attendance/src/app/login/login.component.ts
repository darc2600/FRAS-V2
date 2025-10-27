import { Component } from '@angular/core';
import { LoginService } from './login.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  email = '';
  password = '';
  error = '';
  success = '';

  constructor(private loginService: LoginService) {}

  login() {
    if (this.email && this.password) {
      this.error = '';
      this.success = '';
      this.loginService.login({
        email: this.email,
        password: this.password
      }).subscribe({
        next: () => {
          this.success = 'Login successful!';
          this.email = '';
          this.password = '';
        },
        error: err => {
          this.error = err?.error?.message || 'Invalid credentials';
        }
      });
    } else {
      this.error = 'Email and password required';
    }
  }
}
