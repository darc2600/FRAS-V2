import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class LoginService {
  private apiUrl = '/api/login';

  constructor(private http: HttpClient) {}

  // Accepts an email + password and forwards it to the backend
  login(data: { email: string; password: string }): Observable<any> {
    // Use the full backend URL during development to avoid proxy configuration
    const fullUrl = 'http://127.0.0.1:8000/api/login';
    return this.http.post(fullUrl, data);
  }
}
