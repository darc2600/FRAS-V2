import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
export interface RegisterStudentsPayload {
  courseCode: string;
  section: string;
  studentId: string;
  studentName: string;
  imageCount: number;
}
@Injectable({ providedIn: 'root' })
export class RegisterStudentsService {
  private readonly baseUrl = '/api';
  constructor(private http: HttpClient) {}
  registerStudent(formData: FormData): Observable<any> {
    return this.http.post(`${this.baseUrl}/register`, formData, {
      reportProgress: true,
      observe: 'events',
    });
  }

  getStudentByNumber(studentNumber: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/students/${studentNumber}`);
  }
}
