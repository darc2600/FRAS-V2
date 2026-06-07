export type V2ClassStatus = 'current' | 'upcoming' | 'completed';

export interface V2ClassCard {
  class_id: number;
  course_code: string;
  course_name: string;
  section: string;
  room: string;
  day_of_week: string;
  start_time: string;
  end_time: string;
  student_count: number;
  status: V2ClassStatus;
  active_session_id?: number | null;
}

export interface V2TodayClassesResponse {
  professor_id: number;
  date: string;
  current: V2ClassCard[];
  upcoming: V2ClassCard[];
  completed: V2ClassCard[];
}

export interface V2ProfessorScheduleClass {
  class_id: number;
  course_code: string;
  course_name: string;
  section: string;
  room: string;
  day_of_week: string;
  start_time: string;
  end_time: string;
  student_count: number;
}

export interface V2ProfessorScheduleResponse {
  professor_id: number;
  classes: V2ProfessorScheduleClass[];
}

export interface V2ProfessorSummary {
  professor_id: number;
  user_id?: number | null;
  faculty_number?: string | null;
  professor_name: string;
  email: string;
  total_units: number;
  lecture_units: number;
  lab_units: number;
}

export interface V2SessionDetailResponse {
  session: {
    session_id: number;
    class_id: number;
    professor_id: number;
    scheduled_start: string;
    scheduled_end: string;
    actual_start?: string | null;
    actual_end?: string | null;
    session_status: string;
    student_record_count: number;
  };
  roster: V2StudentRecord[];
  events: V2AttendanceEvent[];
}

export interface V2StudentRecord {
  record_id: number;
  student_id: number;
  student_number: string;
  student_name: string;
  final_status: string;
  system_assessment: string;
  time_in?: string | null;
  time_out?: string | null;
  total_presence_minutes: number;
  total_outside_minutes: number;
  break_count: number;
  late_minutes: number;
  requires_review: boolean;
  review_reason?: string | null;
}

export interface V2AttendanceEvent {
  event_id: number;
  session_id: number;
  record_id?: number | null;
  student_id?: number | null;
  event_type: string;
  event_time: string;
  event_source: string;
  recognition_confidence?: number | null;
  notes?: string | null;
  is_voided: boolean;
}

export interface V2CreateEventRequest {
  student_id: number;
  event_type:
    | 'time_in'
    | 'break_out'
    | 'break_in'
    | 'time_out'
    | 'manual_attendance'
    | 'manual_capture'
    | 'false_recognition'
    | 'missed_recognition'
    | 'camera_failure'
    | 'network_failure';
  event_source?: 'facial_recognition' | 'manual_professor' | 'system';
  event_time?: string | null;
  recognition_confidence?: number | null;
  notes?: string | null;
}

export type V2ManualAttendanceStatus = 'present' | 'absent' | 'late' | 'excused';

export interface V2ManualAttendanceRequest {
  professor_id?: number;
  records: Array<{
    record_id: number;
    student_id: number;
    status: V2ManualAttendanceStatus;
  }>;
  notes?: string | null;
}

export interface V2SessionReviewResponse {
  session: V2SessionDetailResponse['session'];
  summary: {
    present_count: number;
    late_count: number;
    partial_count: number;
    absent_count: number;
    excused_count: number;
    students_requiring_review: number;
    total_students: number;
    presence_validation_rate: number;
  };
  roster: V2StudentRecord[];
}

export type V2HistorySessionStatus = 'completed' | 'needs_review' | 'in_progress';

export interface V2SessionHistoryResponse {
  class_context?: {
    class_id: number;
    course_code: string;
    course_name: string;
    section: string;
    room: string;
    professor_name: string;
  } | null;
  summary: {
    total_sessions: number;
    average_attendance_rate: number;
    average_presence_minutes: number;
    sessions_requiring_review: number;
    excused_students: number;
  };
  sessions: Array<{
    session_id: number;
    date: string;
    scheduled_start: string;
    scheduled_end: string;
    attendance_count: number;
    total_students: number;
    attendance_rate: number;
    average_presence_minutes: number;
    warning_count: number;
    excused_count: number;
    status: V2HistorySessionStatus;
  }>;
}

export type V2FaceProfileStatus = 'registered' | 'needs_update' | 'no_face_profile';
export type V2RecognitionStatus = 'active' | 'low_confidence' | 'not_recognized_recently' | 'not_available';

export interface V2ClassRosterResponse {
  class_context: {
    class_id: number;
    course_code: string;
    course_name: string;
    section: string;
    room: string;
    professor_name: string;
    student_count: number;
  };
  students: V2ClassRosterStudent[];
}

export interface V2ClassRosterStudent {
  student_id: number;
  student_number: string;
  student_name: string;
  email?: string | null;
  face_profile_status: V2FaceProfileStatus;
  recognition_status: V2RecognitionStatus;
  attendance_rate: number;
  last_face_update?: string | null;
  recognition_confidence?: number | null;
  total_sessions: number;
  present_sessions: number;
  late_sessions: number;
  partial_sessions: number;
  absent_sessions: number;
  excused_sessions: number;
  recent_history: Array<{
    session_id: number;
    session_date: string;
    status: string;
    note: string;
  }>;
}

export interface V2StudentClassHistoryResponse {
  header: {
    class_id: number;
    student_id: number;
    student_name: string;
    student_number: string;
    course_code: string;
    course_name: string;
    section: string;
    room: string;
    attendance_rate: number;
  };
  summary: {
    total_sessions: number;
    present_sessions: number;
    late_sessions: number;
    partial_sessions: number;
    absent_sessions: number;
    excused_sessions: number;
    attendance_rate: number;
  };
  records: V2StudentClassHistoryRecord[];
}

export interface V2StudentClassHistoryRecord {
  session_id: number;
  session_date: string;
  scheduled_start: string;
  scheduled_end: string;
  attendance_status: string;
  presence_duration_minutes: number;
  outside_duration_minutes: number;
  break_count: number;
  system_assessment: string;
}

export interface V2FaceProfileContextResponse {
  class_id: number;
  student_id: number;
  student_name: string;
  student_number: string;
  course_code: string;
  course_name: string;
  section: string;
  room: string;
  face_profile_status: V2FaceProfileStatus;
  last_face_update?: string | null;
}

export interface V2FaceProfileSaveResponse {
  status: string;
  message: string;
  student_id: number;
  face_profile_status: V2FaceProfileStatus;
  saved_angles: string[];
  image_paths: string[];
}

export interface V2RecognitionMatchResponse {
  status: 'success' | 'failed' | 'error';
  message?: string | null;
  student_id?: number | null;
  student_name?: string | null;
  confidence?: number | null;
}
