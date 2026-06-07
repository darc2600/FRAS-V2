import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../../api.service';
import { AuthService } from '../../../auth.service';
import {
  V2ClassCard,
  V2ProfessorSummary,
  V2ProfessorScheduleClass,
  V2ProfessorScheduleResponse,
  V2TodayClassesResponse
} from '../../models/v2-attendance.models';
import { V2StatusTone } from '../../components';

type V2TodayView = 'cards' | 'schedule';

const PROFESSOR_ID = 1;
const TEST_PROFESSOR_EMAIL = 'test.professor@mapua.test';
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const STANDARD_TIME_SLOTS = [
  '07:00 AM - 08:10 AM',
  '08:10 AM - 09:20 AM',
  '09:20 AM - 10:30 AM',
  '10:30 AM - 11:40 AM',
  '11:40 AM - 12:50 PM',
  '12:50 PM - 02:00 PM',
  '02:00 PM - 03:10 PM',
  '03:10 PM - 04:20 PM',
  '04:20 PM - 05:30 PM',
  '05:30 PM - 06:40 PM',
  '06:40 PM - 07:50 PM',
  '07:50 PM - 09:00 PM'
];

@Component({
  selector: 'app-v2-todays-classes',
  templateUrl: './todays-classes.component.html',
  styleUrls: ['./todays-classes.component.scss']
})
export class V2TodaysClassesComponent implements OnInit, OnDestroy {
  professorId = PROFESSOR_ID;
  selectedDate = this.toDateInputValue(new Date());
  view: V2TodayView = 'cards';
  todayData: V2TodayClassesResponse | null = null;
  scheduleData: V2ProfessorScheduleResponse | null = null;
  professors: V2ProfessorSummary[] = [];
  isLoading = false;
  isStartingSession = false;
  errorMessage = '';
  lastSessionId: number | null = null;
  now = new Date();
  private clockInterval: any;
  private routeSubscription: any;

  navItems = [
    { label: 'Classes', icon: '▣', href: '/v2/classes', active: true },
    { label: 'Session History', icon: '▤', href: '/v2/history' },
    { label: 'Schedule', icon: '□', href: '/v2/schedule' },
    { label: 'Settings', icon: '○', href: '/v2/settings' }
  ];

  days = DAYS;

  constructor(
    private api: ApiService,
    private authService: AuthService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.routeSubscription = this.route.url.subscribe(() => {
      this.view = this.router.url.startsWith('/v2/schedule') ? 'schedule' : 'cards';
    });
    this.loadProfessors();
    this.clockInterval = setInterval(() => this.now = new Date(), 60000);
  }

  ngOnDestroy(): void {
    if (this.clockInterval) {
      clearInterval(this.clockInterval);
    }
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
  }

  loadPageData(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.api.getV2TodayClasses(this.professorId, this.selectedDate).subscribe({
      next: (data) => {
        this.todayData = data;
        this.isLoading = false;
      },
      error: () => {
        this.errorMessage = 'Unable to load V2 classes.';
        this.isLoading = false;
      }
    });

    this.api.getV2ProfessorSchedule(this.professorId).subscribe({
      next: (data) => this.scheduleData = data,
      error: () => this.errorMessage = 'Unable to load V2 schedule.'
    });
  }

  loadProfessors(): void {
    this.api.getV2Professors().subscribe({
      next: (data) => {
        this.professors = data;
        const currentUser = this.authService.getCurrentUser();
        const matchedProfessor = data.find((professor) => professor.user_id === currentUser?.userId);
        if (matchedProfessor) {
          this.professorId = matchedProfessor.professor_id;
        }
        this.loadPageData();
      },
      error: () => {
        this.errorMessage = 'Unable to load V2 professors.';
        this.loadPageData();
      }
    });
  }

  onProfessorChange(value: number | string): void {
    if (!this.canBrowseProfessors) return;
    this.professorId = Number(value) || PROFESSOR_ID;
    this.loadPageData();
  }

  get selectedProfessor(): V2ProfessorSummary | null {
    return this.professors.find((professor) => professor.professor_id === this.professorId) || null;
  }

  get canBrowseProfessors(): boolean {
    const currentUser = this.authService.getCurrentUser();
    return this.authService.isAdmin() || currentUser?.email === TEST_PROFESSOR_EMAIL;
  }

  setView(view: V2TodayView): void {
    this.view = view;
    const target = view === 'schedule' ? '/v2/schedule' : '/v2/classes';
    if (!this.router.url.startsWith(target)) {
      this.router.navigate([target]);
    }
  }

  onDateChange(value: string): void {
    this.selectedDate = value;
    this.loadPageData();
  }

  startSession(classItem: V2ClassCard): void {
    this.startSessionByClassId(classItem.class_id);
  }

  handleClassPrimaryAction(classItem: V2ClassCard): void {
    if (classItem.status === 'completed') {
      this.lastSessionId = null;
      this.errorMessage = 'Session history is not available yet.';
      return;
    }
    this.startSession(classItem);
  }

  startScheduleSession(classItem: V2ProfessorScheduleClass): void {
    this.startSessionByClassId(classItem.class_id);
  }

  handleAssignedPrimaryAction(classItem: V2ProfessorScheduleClass): void {
    if (!this.canStartMonitorForAssignedClass(classItem)) return;
    this.startScheduleSession(classItem);
  }

  startSessionByClassId(classId: number): void {
    this.isStartingSession = true;
    this.errorMessage = '';

    this.api.startV2Session(classId, this.professorId, this.selectedDate).subscribe({
      next: (detail) => {
        this.lastSessionId = detail.session.session_id;
        this.isStartingSession = false;
        this.loadPageData();
        this.router.navigate(['/live-session', detail.session.session_id]);
      },
      error: () => {
        this.errorMessage = 'Unable to start the V2 session.';
        this.isStartingSession = false;
      }
    });
  }

  get allDayClasses(): V2ClassCard[] {
    if (!this.todayData) return [];
    return [...this.todayData.current, ...this.todayData.upcoming, ...this.todayData.completed]
      .sort((a, b) => a.start_time.localeCompare(b.start_time));
  }

  get focusClass(): V2ClassCard | null {
    return this.todayData?.current[0] || null;
  }

  get nextClass(): V2ClassCard | V2ProfessorScheduleClass | null {
    if (this.todayData?.upcoming.length) {
      return this.todayData.upcoming[0];
    }
    return this.nextScheduledClass;
  }

  get currentCount(): number {
    return this.todayData?.current.length || 0;
  }

  get upcomingCount(): number {
    return this.todayData?.upcoming.length || 0;
  }

  get completedCount(): number {
    return this.todayData?.completed.length || 0;
  }

  get totalStudents(): number {
    return this.allDayClasses.reduce((total, item) => total + item.student_count, 0);
  }

  get assignedClasses(): V2ProfessorScheduleClass[] {
    return [...(this.scheduleData?.classes || [])].sort((a, b) => {
      const dayDiff = DAYS.indexOf(a.day_of_week) - DAYS.indexOf(b.day_of_week);
      return dayDiff || this.timeToMinutes(a.start_time) - this.timeToMinutes(b.start_time);
    });
  }

  get assignedStudentCount(): number {
    return this.assignedClasses.reduce((total, item) => total + item.student_count, 0);
  }

  get scheduleRows(): string[] {
    return STANDARD_TIME_SLOTS;
  }

  slotStartLabel(slot: string): string {
    return slot.split(' - ')[0];
  }

  get nextScheduledClass(): V2ProfessorScheduleClass | null {
    const classes = this.assignedClasses;
    if (!classes.length) return null;

    const selected = new Date(`${this.selectedDate}T00:00:00`);
    let nearest: { item: V2ProfessorScheduleClass; occurrence: Date } | null = null;

    for (const item of classes) {
      const occurrence = this.nextOccurrenceFor(item, selected);
      if (!nearest || occurrence.getTime() < nearest.occurrence.getTime()) {
        nearest = { item, occurrence };
      }
    }

    return nearest?.item || null;
  }

  get nextScheduledLabel(): string {
    if (!this.nextScheduledClass) return '';
    const occurrence = this.nextOccurrenceFor(this.nextScheduledClass, new Date(`${this.selectedDate}T00:00:00`));
    const dateLabel = new Intl.DateTimeFormat('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric'
    }).format(occurrence);
    return `${dateLabel}, ${this.formatScheduleLike(this.nextScheduledClass)}`;
  }

  get selectedDateHeading(): string {
    return this.formatDateLabel(this.selectedDate);
  }

  get currentTimeLabel(): string {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit'
    }).format(this.now);
  }

  classesForSlotAndDay(slot: string, day: string): V2ProfessorScheduleClass[] {
    return (this.scheduleData?.classes || []).filter((item) =>
      item.day_of_week === day &&
      this.classCoversSlot(item, slot)
    );
  }

  isSelectedDay(day: string): boolean {
    const date = new Date(`${this.selectedDate}T00:00:00`);
    return DAYS[date.getDay() === 0 ? 6 : date.getDay() - 1] === day;
  }

  isTodayColumn(day: string): boolean {
    const currentDayIndex = this.now.getDay() === 0 ? 6 : this.now.getDay() - 1;
    return DAYS[currentDayIndex] === day;
  }

  isCurrentTimeSlot(slot: string): boolean {
    const [slotStartText, slotEndText] = slot.split(' - ');
    const currentMinutes = this.now.getHours() * 60 + this.now.getMinutes();
    return currentMinutes >= this.parseTimeLabel(slotStartText) && currentMinutes < this.parseTimeLabel(slotEndText);
  }

  isCurrentCell(slot: string, day: string): boolean {
    return this.isTodayColumn(day) && this.isCurrentTimeSlot(slot);
  }

  toCardStatus(status: V2ClassCard['status']): 'upcoming' | 'ongoing' | 'completed' | 'needs_review' {
    if (status === 'current') return 'ongoing';
    return status;
  }

  toneForStatus(status: V2ClassCard['status']): V2StatusTone {
    if (status === 'completed') return 'success';
    if (status === 'current') return 'warning';
    return 'info';
  }

  actionLabelFor(classItem: V2ClassCard): string {
    if (classItem.active_session_id) return 'Resume Session';
    if (classItem.status === 'completed') return 'View History';
    return 'Start Session';
  }

  formatSchedule(classItem: V2ClassCard): string {
    return this.formatScheduleLike(classItem);
  }

  formatScheduleLike(classItem: V2ClassCard | V2ProfessorScheduleClass): string {
    return `${this.formatTime(classItem.start_time)} - ${this.formatTime(classItem.end_time)}`;
  }

  courseSectionLabel(classItem: V2ClassCard | V2ProfessorScheduleClass): string {
    return `${classItem.course_code} · ${classItem.section}`;
  }

  statusForAssignedClass(classItem: V2ProfessorScheduleClass): 'upcoming' | 'ongoing' | 'completed' | 'needs_review' {
    const selectedDay = this.selectedDayName();
    if (classItem.day_of_week !== selectedDay) return 'upcoming';
    const nowMinutes = this.isSelectedDateToday() ? this.now.getHours() * 60 + this.now.getMinutes() : -1;
    const start = this.timeToMinutes(classItem.start_time);
    const end = this.timeToMinutes(classItem.end_time);
    if (nowMinutes >= start && nowMinutes <= end) return 'ongoing';
    if (nowMinutes > end) return 'completed';
    return 'upcoming';
  }

  actionLabelForAssignedClass(classItem: V2ProfessorScheduleClass): string {
    return 'Start Monitor';
  }

  canStartMonitorForAssignedClass(classItem: V2ProfessorScheduleClass): boolean {
    return this.statusForAssignedClass(classItem) === 'ongoing';
  }

  formatDateLabel(value: string): string {
    return new Intl.DateTimeFormat('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    }).format(new Date(`${value}T00:00:00`));
  }

  formatTime(value: string): string {
    const [hourText, minuteText] = value.split(':');
    const hour = Number(hourText);
    const minute = Number(minuteText || 0);
    const date = new Date();
    date.setHours(hour, minute, 0, 0);
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit'
    }).format(date);
  }

  private toDateInputValue(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  private parseSlotStart(slot: string): number {
    const [time, period] = slot.split(' - ')[0].split(' ');
    const [hourText, minuteText] = time.split(':');
    let hour = Number(hourText);
    const minute = Number(minuteText);
    if (period === 'PM' && hour !== 12) hour += 12;
    if (period === 'AM' && hour === 12) hour = 0;
    return hour * 60 + minute;
  }

  private selectedDayName(): string {
    const date = new Date(`${this.selectedDate}T00:00:00`);
    return DAYS[date.getDay() === 0 ? 6 : date.getDay() - 1];
  }

  private isSelectedDateToday(): boolean {
    return this.selectedDate === this.toDateInputValue(new Date());
  }

  private classCoversSlot(classItem: V2ProfessorScheduleClass, slot: string): boolean {
    const [slotStartText, slotEndText] = slot.split(' - ');
    const slotStart = this.parseTimeLabel(slotStartText);
    const slotEnd = this.parseTimeLabel(slotEndText);
    const classStart = this.timeToMinutes(classItem.start_time);
    const classEnd = this.timeToMinutes(classItem.end_time);
    return classStart < slotEnd && classEnd > slotStart;
  }

  private timeToMinutes(value: string): number {
    const [hourText, minuteText] = value.split(':');
    return Number(hourText) * 60 + Number(minuteText || 0);
  }

  private parseTimeLabel(label: string): number {
    const [time, period] = label.trim().split(' ');
    const [hourText, minuteText] = time.split(':');
    let hour = Number(hourText);
    const minute = Number(minuteText);
    if (period === 'PM' && hour !== 12) hour += 12;
    if (period === 'AM' && hour === 12) hour = 0;
    return hour * 60 + minute;
  }

  private nextOccurrenceFor(classItem: V2ProfessorScheduleClass, baseDate: Date): Date {
    const targetDay = DAYS.indexOf(classItem.day_of_week);
    const baseDay = baseDate.getDay() === 0 ? 6 : baseDate.getDay() - 1;
    let dayOffset = (targetDay - baseDay + 7) % 7;
    const occurrence = new Date(baseDate);
    occurrence.setDate(baseDate.getDate() + dayOffset);
    const startMinutes = this.timeToMinutes(classItem.start_time);
    occurrence.setHours(Math.floor(startMinutes / 60), startMinutes % 60, 0, 0);

    if (dayOffset === 0 && this.isSelectedDateToday() && occurrence.getTime() < this.now.getTime()) {
      occurrence.setDate(occurrence.getDate() + 7);
    }

    return occurrence;
  }
}
