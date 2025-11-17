import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  backendUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  recognizeFace(file: File, classId: number): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('class_id', classId.toString());
    return this.http.post(`${this.backendUrl}/api/recognize`, formData);
  }

  getAttendance(courseCode: string, section: string, room?: string, startDate?: string, endDate?: string) {
    let url = `${this.backendUrl}/api/attendance?course_code=${courseCode}&section=${section}`;
    if (room) {
      url += `&room=${room}`;
    }
    if (startDate) {
      url += `&start_date=${startDate}`;
    }
    if (endDate) {
      url += `&end_date=${endDate}`;
    }
    return this.http.get<any>(url);
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
    return this.http.get<any>(`${this.backendUrl}/api/room-schedule/${roomId}`);
  }

  updateRoomSchedule(roomId: string, data: any): Observable<any> {
    return this.http.post<any>(`${this.backendUrl}/api/room-schedule/${roomId}`, data);
  }

  deleteRoomSchedule(roomId: string): Observable<any> {
    return this.http.delete<any>(`${this.backendUrl}/api/room-schedule/${roomId}`);
  }

  getCourses(): Observable<any[]> {
    return this.http.get<any[]>(`${this.backendUrl}/api/courses`);
  }

  getSectionsForCourse(courseCode: string): Observable<string[]> {
    return this.http.get<string[]>(`${this.backendUrl}/api/courses/${courseCode}/sections`);
  }

  getSectionsForCourseAndRoom(roomId: number, courseCode: string): Observable<string[]> {
    return this.http.get<string[]>(`${this.backendUrl}/api/rooms/${roomId}/courses/${courseCode}/sections`);
  }

  getInstructors(): Observable<string[]> {
    return this.http.get<string[]>(`${this.backendUrl}/api/instructors`);
  }

  registerStudent(formData: FormData): Observable<any> {
    return this.http.post(`${this.backendUrl}/api/register`, formData);
  }

  captureImage(formData: FormData): Observable<any> {
    return this.http.post(`${this.backendUrl}/api/capture`, formData);
  }

  getStudentByNumber(studentNumber: string): Observable<any> {
    return this.http.get(`${this.backendUrl}/api/students/${studentNumber}`);
  }
}
