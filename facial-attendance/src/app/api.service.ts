import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  backendUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  recognizeFace(file: File, courseCode: string, section: string, room: string): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('course_code', courseCode);
    formData.append('section', section);
    formData.append('room', room);
    return this.http.post(`${this.backendUrl}/api/recognize`, formData);
  }

  getAttendance(courseCode: string, section: string, room: string) {
    return this.http.get<any>(`${this.backendUrl}/api/attendance?course_code=${courseCode}&section=${section}&room=${room}`);
  }

  getRooms(): Observable<string[]> {
    return this.http.get<string[]>(`${this.backendUrl}/api/rooms`);
  }

  getCourses(room: string): Observable<string[]> {
    return this.http.get<string[]>(`${this.backendUrl}/api/courses?room=${room}`);
  }

  getSections(room: string, course: string): Observable<string[]> {
    return this.http.get<string[]>(`${this.backendUrl}/api/sections?room=${room}&course=${course}`);
  }
}
