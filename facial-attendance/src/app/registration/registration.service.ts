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

  registerStudent(data: RegistrationPayload, blobs: Blob[]): Observable<HttpEvent<any>> {
    const fd = new FormData();
    fd.set('courseCode', data.courseCode.trim());
    fd.set('section', data.section.trim());
    fd.set('studentId', data.studentId.trim());
    fd.set('studentName', data.studentName.trim());
    fd.set('imageCount', String(data.imageCount));
    blobs.forEach((b, i) => fd.append('images', b, `img${i + 1}.jpg`));
    return this.http.post(`${this.baseUrl}/registration`, fd, {
      reportProgress: true,
      observe: 'events',
    });
  }
}