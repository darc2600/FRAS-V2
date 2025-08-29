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

@Injectable({ providedIn: 'root' })
export class RegistrationService {
  private readonly baseUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) {}

  registerStudent(formData: FormData): Observable<HttpEvent<any>> {
    return this.http.post(`${this.baseUrl}/registration`, formData, {
      reportProgress: true,
      observe: 'events',
    });
  }
}