import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../api.service';
import { forkJoin } from 'rxjs';

interface MonthPoint {
  month: string;
  count: number;
}

interface StatusPoint {
  status: string;
  count: number;
}

interface ClassPoint {
  class_label: string;
  count: number;
}

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="analytics-container">
      <div class="analytics-header">
        <div>
          <p class="eyebrow">FRAS Insights</p>
          <h2>System Analytics</h2>
          <p class="subtitle">
            Visual overview of user growth, attendance activity, and face registration readiness.
          </p>
        </div>

        <div class="year-badge" *ngIf="analyticsData?.chart_year">
          <span>Chart Year</span>
          <strong>{{ analyticsData.chart_year }}</strong>
        </div>
      </div>

      <div class="alert error" *ngIf="errorMessage">
        {{ errorMessage }}
      </div>

      <div class="loading-card" *ngIf="isLoading">
        Loading analytics...
      </div>

      <ng-container *ngIf="!isLoading && analyticsData">
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-label">Total Students</span>
            <strong>{{ analyticsData.total_students || 0 }}</strong>
            <small>Registered learners</small>
          </div>

          <div class="stat-card">
            <span class="stat-label">Total Instructors</span>
            <strong>{{ analyticsData.total_instructors || 0 }}</strong>
            <small>Active teaching users</small>
          </div>

          <div class="stat-card">
            <span class="stat-label">Attendance Records</span>
            <strong>{{ analyticsData.total_attendance_records || 0 }}</strong>
            <small>All captured logs</small>
          </div>

          <div class="stat-card">
            <span class="stat-label">Recent Attendance</span>
            <strong>{{ analyticsData.recent_attendance || 0 }}</strong>
            <small>Last 7 days</small>
          </div>
        </div>

        <section class="chart-grid">
          <article class="chart-card wide">
            <div class="card-heading">
              <div>
                <h3>Student Registrations by Month</h3>
                <p>Monthly student growth from January to December.</p>
              </div>
              <span class="pill">{{ getTotal(analyticsData.monthly_student_registrations) }} total</span>
            </div>

            <div class="bar-chart" *ngIf="hasData(analyticsData.monthly_student_registrations); else noStudentData">
              <div
                class="bar-item"
                *ngFor="let point of analyticsData.monthly_student_registrations"
                [title]="point.month + ': ' + point.count"
              >
                <div class="bar-track">
                  <div class="bar-fill student" [style.height.%]="getBarHeight(point.count, analyticsData.monthly_student_registrations)"></div>
                </div>
                <span>{{ point.month }}</span>
                <strong>{{ point.count }}</strong>
              </div>
            </div>

            <ng-template #noStudentData>
              <div class="empty-state">No student registration data available for this chart year.</div>
            </ng-template>
          </article>

          <article class="chart-card wide">
            <div class="card-heading">
              <div>
                <h3>Instructor Registrations by Month</h3>
                <p>Monthly instructor account growth from January to December.</p>
              </div>
              <span class="pill">{{ getTotal(analyticsData.monthly_instructor_registrations) }} total</span>
            </div>

            <div class="bar-chart" *ngIf="hasData(analyticsData.monthly_instructor_registrations); else noInstructorData">
              <div
                class="bar-item"
                *ngFor="let point of analyticsData.monthly_instructor_registrations"
                [title]="point.month + ': ' + point.count"
              >
                <div class="bar-track">
                  <div class="bar-fill instructor" [style.height.%]="getBarHeight(point.count, analyticsData.monthly_instructor_registrations)"></div>
                </div>
                <span>{{ point.month }}</span>
                <strong>{{ point.count }}</strong>
              </div>
            </div>

            <ng-template #noInstructorData>
              <div class="empty-state">No instructor registration data available for this chart year.</div>
            </ng-template>
          </article>

          <article class="chart-card wide">
            <div class="card-heading">
              <div>
                <h3>Attendance Records by Month</h3>
                <p>Monthly attendance activity captured by the system.</p>
              </div>
              <span class="pill">{{ getTotal(analyticsData.monthly_attendance_records) }} logs</span>
            </div>

            <div class="bar-chart" *ngIf="hasData(analyticsData.monthly_attendance_records); else noAttendanceData">
              <div
                class="bar-item"
                *ngFor="let point of analyticsData.monthly_attendance_records"
                [title]="point.month + ': ' + point.count"
              >
                <div class="bar-track">
                  <div class="bar-fill attendance" [style.height.%]="getBarHeight(point.count, analyticsData.monthly_attendance_records)"></div>
                </div>
                <span>{{ point.month }}</span>
                <strong>{{ point.count }}</strong>
              </div>
            </div>

            <ng-template #noAttendanceData>
              <div class="empty-state">No attendance records available for this chart year.</div>
            </ng-template>
          </article>

          <article class="chart-card">
            <div class="card-heading">
              <div>
                <h3>Attendance Status Breakdown</h3>
                <p>Present, absent, late, and excused records.</p>
              </div>
            </div>

            <div class="status-list" *ngIf="hasStatusData(); else noStatusData">
              <div class="status-row" *ngFor="let item of analyticsData.attendance_status_distribution">
                <div class="status-info">
                  <span>{{ item.status }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
                <div class="progress-track">
                  <div class="progress-fill" [style.width.%]="getStatusPercent(item.count)"></div>
                </div>
              </div>
            </div>

            <ng-template #noStatusData>
              <div class="empty-state">No attendance status records available yet.</div>
            </ng-template>
          </article>

          <article class="chart-card">
            <div class="card-heading">
              <div>
                <h3>Face Registration Completion</h3>
                <p>
                  Shows how many students have completed face registration and are ready
                  for face recognition attendance.
                </p>
              </div>
            </div>

            <div class="face-readiness" *ngIf="embeddingCoverage">
              <div class="donut" [style.--value.%]="faceRegistrationPercent">
                <span>{{ faceRegistrationPercent }}%</span>
              </div>

              <div class="face-stats">
                <div>
                  <strong>{{ embeddingCoverage.students_with_any_face_data || 0 }}</strong>
                  <span>Students Ready for Face Recognition</span>
                </div>
                <div>
                  <strong>{{ embeddingCoverage.students_missing_all_face_data || 0 }}</strong>
                  <span>Students Without Registered Face</span>
                </div>
                <div>
                  <strong>{{ embeddingCoverage.total_students || 0 }}</strong>
                  <span>Total Students Checked</span>
                </div>
              </div>
            </div>
          </article>

          <article class="chart-card">
            <div class="card-heading">
              <div>
                <h3>Top Classes by Attendance Logs</h3>
                <p>Classes with the most recorded attendance activity.</p>
              </div>
            </div>

            <div class="status-list" *ngIf="hasTopClassData(); else noTopClassData">
              <div class="status-row" *ngFor="let item of analyticsData.top_classes_by_attendance">
                <div class="status-info">
                  <span>{{ item.class_label }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
                <div class="progress-track">
                  <div class="progress-fill class" [style.width.%]="getClassPercent(item.count)"></div>
                </div>
              </div>
            </div>

            <ng-template #noTopClassData>
              <div class="empty-state">No class attendance data available yet.</div>
            </ng-template>
          </article>
        </section>
      </ng-container>
    </div>
  `,
  styles: [`
    .analytics-container {
      padding: 24px;
      color: #1f2937;
      background: #f4f7fb;
      min-height: 100vh;
    }

    .analytics-header {
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
      margin-bottom: 22px;
    }

    .eyebrow {
      margin: 0 0 6px;
      color: #b91c1c;
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    h2 {
      margin: 0;
      font-size: clamp(1.8rem, 3vw, 2.5rem);
      color: #111827;
    }

    .subtitle {
      margin: 8px 0 0;
      color: #6b7280;
      max-width: 720px;
      line-height: 1.55;
    }

    .year-badge {
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 18px;
      padding: 14px 18px;
      min-width: 130px;
      text-align: center;
      box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
    }

    .year-badge span {
      display: block;
      color: #6b7280;
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .year-badge strong {
      display: block;
      color: #b91c1c;
      font-size: 1.65rem;
      margin-top: 2px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }

    .stat-card,
    .chart-card,
    .loading-card,
    .alert {
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 22px;
      box-shadow: 0 16px 35px rgba(15, 23, 42, 0.08);
    }

    .stat-card {
      padding: 20px;
    }

    .stat-label {
      color: #6b7280;
      font-size: 0.85rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .stat-card strong {
      display: block;
      color: #111827;
      font-size: 2.25rem;
      line-height: 1;
      margin: 10px 0 6px;
    }

    .stat-card small {
      color: #6b7280;
    }

    .chart-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }

    .chart-card {
      padding: 20px;
      overflow: hidden;
    }

    .chart-card.wide {
      grid-column: 1 / -1;
    }

    .card-heading {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
      margin-bottom: 18px;
    }

    .card-heading h3 {
      margin: 0 0 5px;
      color: #111827;
      font-size: 1.1rem;
    }

    .card-heading p {
      margin: 0;
      color: #6b7280;
      line-height: 1.45;
      font-size: 0.92rem;
    }

    .pill {
      white-space: nowrap;
      border-radius: 999px;
      padding: 7px 11px;
      background: #fee2e2;
      color: #991b1b;
      font-weight: 800;
      font-size: 0.8rem;
    }

    .bar-chart {
      display: grid;
      grid-template-columns: repeat(12, minmax(34px, 1fr));
      gap: 10px;
      align-items: end;
      min-height: 260px;
    }

    .bar-item {
      display: grid;
      grid-template-rows: 1fr auto auto;
      justify-items: center;
      gap: 7px;
      height: 260px;
      min-width: 0;
    }

    .bar-track {
      width: 100%;
      height: 190px;
      display: flex;
      align-items: end;
      justify-content: center;
      border-radius: 14px;
      background: #f3f4f6;
      overflow: hidden;
      border: 1px solid #e5e7eb;
    }

    .bar-fill {
      width: 100%;
      min-height: 4px;
      border-radius: 14px 14px 0 0;
      transition: height 0.25s ease;
    }

    .bar-fill.student {
      background: linear-gradient(180deg, #ef4444, #991b1b);
    }

    .bar-fill.instructor {
      background: linear-gradient(180deg, #f59e0b, #b45309);
    }

    .bar-fill.attendance {
      background: linear-gradient(180deg, #2563eb, #1e40af);
    }

    .bar-item span {
      color: #6b7280;
      font-size: 0.78rem;
      font-weight: 700;
    }

    .bar-item strong {
      color: #111827;
      font-size: 0.82rem;
    }

    .status-list {
      display: grid;
      gap: 14px;
    }

    .status-row {
      display: grid;
      gap: 8px;
    }

    .status-info {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      color: #374151;
      font-weight: 700;
    }

    .status-info span {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .progress-track {
      height: 12px;
      background: #f3f4f6;
      border-radius: 999px;
      overflow: hidden;
      border: 1px solid #e5e7eb;
    }

    .progress-fill {
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, #ef4444, #991b1b);
    }

    .progress-fill.class {
      background: linear-gradient(90deg, #2563eb, #1e40af);
    }

    .face-readiness {
      display: grid;
      grid-template-columns: 180px 1fr;
      gap: 18px;
      align-items: center;
    }

    .donut {
      --value: 0%;
      width: 160px;
      height: 160px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background:
        radial-gradient(circle at center, #ffffff 0 58%, transparent 59%),
        conic-gradient(#16a34a var(--value), #e5e7eb 0);
      border: 1px solid #e5e7eb;
      box-shadow: inset 0 0 0 10px #f9fafb;
    }

    .donut span {
      color: #14532d;
      font-size: 1.8rem;
      font-weight: 900;
    }

    .face-stats {
      display: grid;
      gap: 10px;
    }

    .face-stats div {
      border: 1px solid #e5e7eb;
      background: #f9fafb;
      border-radius: 14px;
      padding: 12px;
    }

    .face-stats strong {
      display: block;
      color: #111827;
      font-size: 1.35rem;
    }

    .face-stats span {
      color: #6b7280;
      font-size: 0.88rem;
    }

    .empty-state,
    .loading-card,
    .alert {
      padding: 24px;
      text-align: center;
      color: #6b7280;
    }

    .alert.error {
      border-color: #fecaca;
      background: #fef2f2;
      color: #991b1b;
      margin-bottom: 16px;
      text-align: left;
    }

    @media (max-width: 900px) {
      .analytics-header {
        flex-direction: column;
      }

      .chart-grid {
        grid-template-columns: 1fr;
      }

      .bar-chart {
        overflow-x: auto;
        grid-template-columns: repeat(12, 54px);
        padding-bottom: 6px;
      }

      .face-readiness {
        grid-template-columns: 1fr;
        justify-items: center;
      }
    }
  `]
})
export class AnalyticsComponent implements OnInit {
  analyticsData: any = null;
  embeddingCoverage: any = null;
  isLoading = true;
  errorMessage = '';
  faceRegistrationPercent = 0;

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    this.loadAnalytics();
  }

  loadAnalytics(): void {
    this.isLoading = true;
    this.errorMessage = '';

    forkJoin({
      analytics: this.apiService.getAnalytics(),
      embeddingCoverage: this.apiService.getFaceEmbeddingCoverage()
    }).subscribe({
      next: (result) => {
        this.analyticsData = result.analytics;
        this.embeddingCoverage = result.embeddingCoverage;
        this.faceRegistrationPercent = this.calculateFaceRegistrationPercent();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading analytics:', error);
        this.errorMessage = error?.error?.detail || 'Unable to load analytics. Please try again or check the backend connection.';
        this.isLoading = false;
      }
    });
  }

  getTotal(points?: MonthPoint[]): number {
    return (points || []).reduce((sum, point) => sum + Number(point.count || 0), 0);
  }

  hasData(points?: MonthPoint[]): boolean {
    return this.getTotal(points) > 0;
  }

  getBarHeight(value: number, points?: MonthPoint[]): number {
    const maxValue = Math.max(...(points || []).map((point) => Number(point.count || 0)), 0);
    if (!maxValue) return 0;
    return Math.max((Number(value || 0) / maxValue) * 100, value > 0 ? 6 : 0);
  }

  hasStatusData(): boolean {
    return (this.analyticsData?.attendance_status_distribution || []).some((item: StatusPoint) => Number(item.count || 0) > 0);
  }

  getStatusPercent(value: number): number {
    const total = (this.analyticsData?.attendance_status_distribution || [])
      .reduce((sum: number, item: StatusPoint) => sum + Number(item.count || 0), 0);

    if (!total) return 0;
    return Math.round((Number(value || 0) / total) * 100);
  }

  hasTopClassData(): boolean {
    return (this.analyticsData?.top_classes_by_attendance || []).some((item: ClassPoint) => Number(item.count || 0) > 0);
  }

  getClassPercent(value: number): number {
    const maxValue = Math.max(
      ...(this.analyticsData?.top_classes_by_attendance || []).map((item: ClassPoint) => Number(item.count || 0)),
      0
    );

    if (!maxValue) return 0;
    return Math.round((Number(value || 0) / maxValue) * 100);
  }

  private calculateFaceRegistrationPercent(): number {
    const totalStudents = Number(this.embeddingCoverage?.total_students || 0);
    const readyStudents = Number(this.embeddingCoverage?.students_with_any_face_data || 0);

    if (!totalStudents) return 0;
    return Math.round((readyStudents / totalStudents) * 100);
  }
}
