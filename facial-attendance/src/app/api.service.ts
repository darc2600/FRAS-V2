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

  getClasses(): Observable<any[]> {
    return this.http.get<any[]>(`${this.backendUrl}/api/classes`);
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

  getStudents(): Observable<any[]> {
    return this.http.get<any[]>(`${this.backendUrl}/api/students`);
  }

  // Admin API methods
  getUsers(): Observable<any[]> {
    return this.http.get<any[]>(`${this.backendUrl}/api/admin/users`);
  }

  createUser(userData: any): Observable<any> {
    return this.http.post(`${this.backendUrl}/api/admin/users`, userData);
  }

  updateUser(userId: number, userData: any): Observable<any> {
    return this.http.put(`${this.backendUrl}/api/admin/users/${userId}`, userData);
  }

  deleteUser(userId: number): Observable<any> {
    return this.http.delete(`${this.backendUrl}/api/admin/users/${userId}`);
  }

  resetPassword(email: string, newPassword?: string): Observable<any> {
    const payload = newPassword ? { email, new_password: newPassword } : { email };
    return this.http.post(`${this.backendUrl}/api/admin/reset-password`, payload);
  }

  bulkUserOperation(operation: string, userIds: number[]): Observable<any> {
    return this.http.post(`${this.backendUrl}/api/admin/users/bulk`, { operation, user_ids: userIds });
  }

  getSystemSettings(): Observable<any> {
    const timestamp = new Date().getTime();
    return this.http.get<any>(`${this.backendUrl}/api/admin/system-settings?t=${timestamp}`, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
  }

  updateSystemSetting(key: string, value: string): Observable<any> {
    return this.http.put(`${this.backendUrl}/api/admin/system-settings`, { setting_key: key, setting_value: value });
  }

  updateSettings(updates: { key: string; value: any }[]): Observable<any> {
    return this.http.put(`${this.backendUrl}/api/admin/system-settings/bulk`, updates);
  }

  getAnalytics(): Observable<any> {
    return this.http.get<any>(`${this.backendUrl}/api/admin/analytics`);
  }

  markAutomaticAbsents(): Observable<any> {
    return this.http.post(`${this.backendUrl}/api/admin/mark-automatic-absents`, {});
  }

  // Support ticket methods
  getSupportTickets(status?: string, priority?: string): Observable<any[]> {
    let url = `${this.backendUrl}/api/admin/support/tickets`;
    const params: string[] = [];
    if (status) params.push(`status=${status}`);
    if (priority) params.push(`priority=${priority}`);
    if (params.length > 0) url += '?' + params.join('&');
    return this.http.get<any[]>(url);
  }

  updateSupportTicket(ticketId: number, updates: any): Observable<any> {
    return this.http.put(`${this.backendUrl}/api/admin/support/tickets/${ticketId}`, updates);
  }

  getTicketReplies(ticketId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.backendUrl}/api/admin/support/tickets/${ticketId}/replies`);
  }

  addTicketReply(ticketId: number, reply: any): Observable<any> {
    return this.http.post(`${this.backendUrl}/api/admin/support/tickets/${ticketId}/replies`, reply);
  }

  submitSupportTicket(ticket: any): Observable<any> {
    return this.http.post(`${this.backendUrl}/api/support/tickets`, ticket);
  }

  // Generic methods for API calls
  post(endpoint: string, data: any): Observable<any> {
    return this.http.post(`${this.backendUrl}${endpoint}`, data);
  }

  // Generic methods for file downloads
  postBlob(endpoint: string, data: any): Observable<Blob> {
    return this.http.post(`${this.backendUrl}${endpoint}`, data, {
      responseType: 'blob'
    });
  }
}
