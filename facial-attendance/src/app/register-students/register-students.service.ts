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
  private readonly baseUrl = 'http://127.0.0.1:8000/api';
  constructor(private http: HttpClient) {}
  registerStudent(formData: FormData): Observable<any> {
    return this.http.post(`${this.baseUrl}/registration`, formData, {
      reportProgress: true,
      observe: 'events',
    });
  }

  getStudentByNumber(studentNumber: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/students/${studentNumber}`);
  }
}
