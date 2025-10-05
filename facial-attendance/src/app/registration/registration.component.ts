import { Component } from '@angular/core';
import { RegistrationService } from './registration.service';

@Component({
  selector: 'app-registration',
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css']
})
export class RegistrationComponent {
  username = '';
  password = '';
  email = '';
  error = '';
  success = '';

  constructor(private registrationService: RegistrationService) {}

  register() {
    if (this.username && this.password && this.email) {
      this.error = '';
      this.success = '';
      this.registrationService.register({
        username: this.username,
        password: this.password,
        email: this.email
      }).subscribe({
        next: () => {
          this.success = 'Registration successful!';
          this.username = '';
          this.password = '';
          this.email = '';
        },
        error: err => {
          this.error = err?.error?.message || 'Registration failed.';
        }
      });
    } else {
      this.error = 'All fields are required';
    }
  }
}
