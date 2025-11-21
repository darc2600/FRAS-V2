import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="analytics-container">
      <h2>System Analytics</h2>

      <div class="stats-grid" *ngIf="analyticsData">
        <div class="stat-card">
          <h3>Total Students</h3>
          <div class="stat-number">{{ analyticsData.total_students }}</div>
        </div>

        <div class="stat-card">
          <h3>Total Instructors</h3>
          <div class="stat-number">{{ analyticsData.total_instructors }}</div>
        </div>

        <div class="stat-card">
          <h3>Attendance Records</h3>
          <div class="stat-number">{{ analyticsData.total_attendance_records }}</div>
        </div>

        <div class="stat-card">
          <h3>Recent Attendance</h3>
          <div class="stat-number">{{ analyticsData.recent_attendance }}</div>
          <small>Last 7 days</small>
        </div>
      </div>

      <div class="loading" *ngIf="!analyticsData">
        Loading analytics...
      </div>
    </div>
  `,
  styles: [`
    .analytics-container {
      padding: 20px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }

    .stat-card {
      background: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      text-align: center;
    }

    .stat-card h3 {
      margin: 0 0 10px 0;
      color: #2c3e50;
      font-size: 1.1rem;
    }

    .stat-number {
      font-size: 2.5rem;
      font-weight: bold;
      color: #3498db;
      margin-bottom: 5px;
    }

    .stat-card small {
      color: #7f8c8d;
      font-size: 0.9rem;
    }

    .loading {
      text-align: center;
      padding: 40px;
      color: #7f8c8d;
    }
  `]
})
export class AnalyticsComponent implements OnInit {
  analyticsData: any = null;

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    this.loadAnalytics();
  }

  loadAnalytics(): void {
    this.apiService.getAnalytics().subscribe({
      next: (data) => {
        this.analyticsData = data;
      },
      error: (error) => {
        console.error('Error loading analytics:', error);
      }
    });
  }
}