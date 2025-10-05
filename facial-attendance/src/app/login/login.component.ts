import { Component } from '@angular/core';
import { LoginService } from './login.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  username = '';
  password = '';
  error = '';
  success = '';

  constructor(private loginService: LoginService) {}

  login() {
    if (this.username && this.password) {
      this.error = '';
      this.success = '';
      this.loginService.login({
        username: this.username,
        password: this.password
      }).subscribe({
        next: () => {
          this.success = 'Login successful!';
          this.username = '';
          this.password = '';
        },
        error: err => {
          this.error = err?.error?.message || 'Invalid credentials';
        }
      });
    } else {
      this.error = 'Username and password required';
    }
  }
}
