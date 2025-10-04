import { Component } from '@angular/core';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  username = '';
  password = '';
  error = '';

  login() {
    if (this.username === 'admin' && this.password === 'admin') {
      this.error = '';
      // Redirect or show success
      alert('Login successful!');
    } else {
      this.error = 'Invalid credentials';
    }
  }
}
