import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  V2CreateEventRequest,
  V2ClassRosterResponse,
  V2FaceProfileContextResponse,
  V2FaceProfileSaveResponse,
  V2ManualAttendanceRequest,
  V2ProfessorScheduleResponse,
  V2ProfessorSummary,
  V2RecognitionMatchResponse,
  V2SessionHistoryResponse,
  V2SessionReviewResponse,
  V2SessionDetailResponse,
  V2StudentClassHistoryResponse,
  V2TodayClassesResponse
} from './v2/models/v2-attendance.models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  backendUrl = '';

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

  getV2TodayClasses(professorId: number, targetDate?: string): Observable<V2TodayClassesResponse> {
    let url = `${this.backendUrl}/api/v2/professors/${professorId}/today/classes`;
    if (targetDate) {
      url += `?target_date=${encodeURIComponent(targetDate)}`;
    }
    return this.http.get<V2TodayClassesResponse>(url);
  }

  getV2Professors(): Observable<V2ProfessorSummary[]> {
    return this.http.get<V2ProfessorSummary[]>(`${this.backendUrl}/api/v2/professors`);
  }

  getV2ProfessorSchedule(professorId: number): Observable<V2ProfessorScheduleResponse> {
    return this.http.get<V2ProfessorScheduleResponse>(`${this.backendUrl}/api/v2/professors/${professorId}/schedule`);
  }

  getV2ClassSessionHistory(classId: number): Observable<V2SessionHistoryResponse> {
    return this.http.get<V2SessionHistoryResponse>(`${this.backendUrl}/api/v2/classes/${classId}/session-history`);
  }

  getV2ClassRoster(classId: number): Observable<V2ClassRosterResponse> {
    return this.http.get<V2ClassRosterResponse>(`${this.backendUrl}/api/v2/classes/${classId}/students`);
  }

  getV2StudentClassHistory(classId: number, studentId: number): Observable<V2StudentClassHistoryResponse> {
    return this.http.get<V2StudentClassHistoryResponse>(`${this.backendUrl}/api/v2/classes/${classId}/students/${studentId}/history`);
  }

  getV2FaceProfileContext(classId: number, studentId: number): Observable<V2FaceProfileContextResponse> {
    return this.http.get<V2FaceProfileContextResponse>(`${this.backendUrl}/api/v2/classes/${classId}/students/${studentId}/face-profile`);
  }

  saveV2FaceProfile(classId: number, studentId: number, formData: FormData): Observable<V2FaceProfileSaveResponse> {
    return this.http.post<V2FaceProfileSaveResponse>(`${this.backendUrl}/api/v2/classes/${classId}/students/${studentId}/face-profile`, formData);
  }

  recognizeV2Face(classId: number, image: File): Observable<V2RecognitionMatchResponse> {
    const formData = new FormData();
    formData.append('image', image);
    return this.http.post<V2RecognitionMatchResponse>(`${this.backendUrl}/api/v2/classes/${classId}/recognize`, formData);
  }

  startV2Session(classId: number, professorId: number, sessionDate?: string): Observable<V2SessionDetailResponse> {
    return this.http.post<V2SessionDetailResponse>(`${this.backendUrl}/api/v2/classes/${classId}/sessions/start`, {
      professor_id: professorId,
      session_date: sessionDate || null
    });
  }

  getV2Session(sessionId: number): Observable<V2SessionDetailResponse> {
    return this.http.get<V2SessionDetailResponse>(`${this.backendUrl}/api/v2/sessions/${sessionId}`);
  }

  createV2SessionEvent(sessionId: number, payload: V2CreateEventRequest): Observable<V2SessionDetailResponse> {
    return this.http.post<V2SessionDetailResponse>(`${this.backendUrl}/api/v2/sessions/${sessionId}/events`, payload);
  }

  saveV2ManualAttendance(sessionId: number, payload: V2ManualAttendanceRequest): Observable<V2SessionDetailResponse> {
    return this.http.post<V2SessionDetailResponse>(`${this.backendUrl}/api/v2/sessions/${sessionId}/manual-attendance`, payload);
  }

  startV2SessionBreak(sessionId: number): Observable<V2SessionDetailResponse> {
    return this.http.post<V2SessionDetailResponse>(`${this.backendUrl}/api/v2/sessions/${sessionId}/break/start`, {});
  }

  endV2SessionBreak(sessionId: number): Observable<V2SessionDetailResponse> {
    return this.http.post<V2SessionDetailResponse>(`${this.backendUrl}/api/v2/sessions/${sessionId}/break/end`, {});
  }

  endV2Session(sessionId: number): Observable<V2SessionReviewResponse> {
    return this.http.post<V2SessionReviewResponse>(`${this.backendUrl}/api/v2/sessions/${sessionId}/end`, {});
  }

  getV2SessionReview(sessionId: number): Observable<V2SessionReviewResponse> {
    return this.http.get<V2SessionReviewResponse>(`${this.backendUrl}/api/v2/sessions/${sessionId}/review`);
  }

  finalizeV2Session(sessionId: number): Observable<V2SessionReviewResponse> {
    return this.http.post<V2SessionReviewResponse>(`${this.backendUrl}/api/v2/sessions/${sessionId}/finalize`, {});
  }

  confirmV2StudentRecord(sessionId: number, studentId: number): Observable<V2SessionReviewResponse> {
    return this.http.post<V2SessionReviewResponse>(`${this.backendUrl}/api/v2/sessions/${sessionId}/students/${studentId}/confirm`, {});
  }

  reauthenticate(email: string, password: string): Observable<any> {
    return this.http.post<any>(`${this.backendUrl}/api/login`, { email, password });
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
    return this.http.post(`${this.backendUrl}/api/registration`, formData);
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

  getFaceEmbeddingCoverage(): Observable<any> {
    return this.http.get<any>(`${this.backendUrl}/api/admin/face-embedding-coverage`);
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
