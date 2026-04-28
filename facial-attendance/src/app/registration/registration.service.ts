import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface RegistrationPayload {
  courseCode: string;
  section: string;
  studentId: string;
  studentName: string;
  imageCount: number;
}

export interface SimpleRegistrationPayload {
  email: string;
  password: string;
}

@Injectable({ providedIn: 'root' })
export class RegistrationService {
  private readonly baseUrl = '/api';

  constructor(private http: HttpClient) {}

  // Simple user registration
  register(payload: SimpleRegistrationPayload): Observable<any> {
    return this.http.post(`${this.baseUrl}/user/register`, payload);
  }

  // Student registration with images and schedule
  registerStudent(formData: FormData): Observable<HttpEvent<any>> {
  return this.http.post(`${this.baseUrl}/register`, formData, {
      reportProgress: true,
      observe: 'events',
    });
  }
}