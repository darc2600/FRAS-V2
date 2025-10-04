import { Component } from '@angular/core';

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

  register() {
    if (this.username && this.password && this.email) {
      this.error = '';
      // Registration logic here
      alert('Registration successful!');
    } else {
      this.error = 'All fields are required';
    }
  }
}
