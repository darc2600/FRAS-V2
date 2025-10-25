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

  getRooms(): Observable<any[]> {
    return this.http.get<any[]>(`${this.backendUrl}/api/rooms`);
  }

  getFloors(): Observable<number[]> {
    return this.http.get<number[]>(`${this.backendUrl}/api/floors`);
  }

  getRoomsByFloor(floorLevel: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.backendUrl}/api/floors/${floorLevel}/rooms`);
  }

  getCoursesSectionsByRoom(roomId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.backendUrl}/api/rooms/${roomId}/courses-sections`);
  }

  getRoomSchedule(roomId: string): Observable<any> {
    return this.http.get<any>(`${this.backendUrl}/api/schedule/${roomId}`);
  }

  updateRoomSchedule(roomId: string, data: any): Observable<any> {
    return this.http.post<any>(`${this.backendUrl}/api/schedule/${roomId}`, data);
  }

  registerStudent(formData: FormData): Observable<any> {
    return this.http.post(`${this.backendUrl}/api/register`, formData);
  }

  captureImage(formData: FormData): Observable<any> {
    return this.http.post(`${this.backendUrl}/api/capture`, formData);
  }
}
