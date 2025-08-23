import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  backendUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  recognizeFace(file: File, courseCode: string, section: string): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('course_code', courseCode);
    formData.append('section', section);
    return this.http.post(`${this.backendUrl}/recognize`, formData);
  }

  getAttendance(courseCode: string, section: string) {
    return this.http.get<any>(`http://127.0.0.1:8000/attendance?course_code=${courseCode}&section=${section}`);
  }
}
