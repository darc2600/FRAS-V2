import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { AuthService } from '../auth.service';

interface SystemSetting {
  key: string;
  value: string;
  type: string;
}

@Component({
  selector: 'app-system-settings',
  templateUrl: './system-settings.component.html',
  styleUrls: ['./system-settings.component.css']
})
export class SystemSettingsComponent implements OnInit {
  settings: { [key: string]: SystemSetting } = {};
  loading = false;
  error = '';
  success = '';

  constructor(
    private apiService: ApiService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadSettings();
  }

  loadSettings(): void {
    this.loading = true;
    this.error = '';

    this.apiService.getSystemSettings().subscribe({
      next: (settings) => {
        this.settings = settings;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load system settings: ' + (err.error?.message || err.message);
        this.loading = false;
        // Fallback to demo data for development
        this.settings = {
          'max_attendance_retention_days': { key: 'max_attendance_retention_days', value: '365', type: 'number' },
          'enable_face_recognition': { key: 'enable_face_recognition', value: 'true', type: 'boolean' },
          'session_timeout_minutes': { key: 'session_timeout_minutes', value: '1440', type: 'number' },
          'backup_frequency_hours': { key: 'backup_frequency_hours', value: '24', type: 'number' }
        };
      }
    });
  }

  updateSetting(key: string, value: string): void {
    this.error = '';
    this.success = '';

    this.apiService.updateSystemSetting(key, value).subscribe({
      next: () => {
        this.settings[key].value = value;
        this.success = `Setting ${key} updated successfully`;
      },
      error: (err) => {
        this.error = 'Failed to update setting: ' + (err.error?.message || err.message);
      }
    });
  }

  getAnalytics(): void {
    this.error = '';
    this.success = '';

    this.apiService.getAnalytics().subscribe({
      next: (analytics) => {
        this.success = `Analytics loaded: ${JSON.stringify(analytics, null, 2)}`;
      },
      error: (err) => {
        this.error = 'Failed to load analytics: ' + (err.error?.message || err.message);
      }
    });
  }

  hasPermission(permission: string): boolean {
    const currentUser = this.authService.getCurrentUser();
    return currentUser ? currentUser.permissions.includes(permission) : false;
  }

  isBooleanSetting(setting: SystemSetting): boolean {
    return setting.type === 'boolean';
  }

  isNumberSetting(setting: SystemSetting): boolean {
    return setting.type === 'number';
  }

  onBooleanSettingChange(key: string, event: Event): void {
    const target = event.target as HTMLInputElement;
    this.updateSetting(key, target.checked ? 'true' : 'false');
  }

  onTextSettingChange(key: string, event: Event): void {
    const target = event.target as HTMLInputElement;
    this.updateSetting(key, target.value);
  }

  isTextSetting(setting: SystemSetting): boolean {
    return setting.type === 'text' || setting.type === 'string';
  }
}