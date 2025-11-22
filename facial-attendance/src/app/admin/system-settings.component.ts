import { Component, OnInit } from '@angular/core';
import { CommonModule, KeyValuePipe, TitleCasePipe } from '@angular/common';
import { ApiService } from '../api.service';
import { AuthService } from '../auth.service';

interface SystemSetting {
  key: string;
  value: string;
  type: string;
}

@Component({
  selector: 'app-system-settings',
  standalone: true,
  imports: [CommonModule, KeyValuePipe, TitleCasePipe],
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
        // Convert the settings object to the expected format
        this.settings = {};
        Object.keys(settings).forEach(key => {
          this.settings[key] = {
            key: key,
            value: settings[key].value,
            type: settings[key].type
          };
        });
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Failed to load system settings: ' + (err.error?.message || err.message);
        this.loading = false;
        // Fallback to demo data for development
        this.settings = {
          'max_attendance_retention_days': { key: 'max_attendance_retention_days', value: '365', type: 'number' },
          'enable_face_recognition': { key: 'enable_face_recognition', value: 'true', type: 'boolean' },
          'session_timeout_minutes': { key: 'session_timeout_minutes', value: '1440', type: 'number' },
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
      error: (err: any) => {
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

  // Helper methods for organized display
  getSettingsByCategory(category: string): SystemSetting[] {
    const categoryMappings: { [key: string]: string[] } = {
      'attendance': [
        'absent_threshold_minutes',
        'late_threshold_minutes',
        'attendance_grace_period_minutes',
        'auto_absent_delay_hours',
        'duplicate_prevention_window_minutes',
        'allow_makeup_attendance',
        'makeup_deadline_hours'
      ],
      'recognition': [
        'recognition_threshold',
        'min_face_confidence',
        'face_detection_model',
        'max_recognition_attempts',
        'image_compression_quality',
        'image_max_size'
      ],
      'automation': [
        'auto_absent_enabled'
      ],
      'system': [
        'system_name',
        'theme_primary_color',
        'theme_secondary_color',
        'system_logo_url',
        'welcome_message',
        'user_guide'
      ]
    };

    const settingKeys = categoryMappings[category] || [];
    return Object.values(this.settings).filter(setting => settingKeys.includes(setting.key));
  }

  getSettingsByType(type: string): SystemSetting[] {
    return Object.values(this.settings).filter(setting => setting.type === type);
  }

  getSettingDisplayName(key: string): string {
    const displayNames: { [key: string]: string } = {
      // Attendance settings
      'absent_threshold_minutes': 'Absent Threshold (minutes)',
      'late_threshold_minutes': 'Late Threshold (minutes)',
      'attendance_grace_period_minutes': 'Attendance Grace Period (minutes)',
      'auto_absent_delay_hours': 'Auto-Absent Delay (hours)',
      'duplicate_prevention_window_minutes': 'Duplicate Prevention Window (minutes)',
      'allow_makeup_attendance': 'Allow Makeup Attendance',
      'makeup_deadline_hours': 'Makeup Deadline (hours)',

      // Recognition settings
      'recognition_threshold': 'Recognition Threshold',
      'min_face_confidence': 'Minimum Face Confidence',
      'face_detection_model': 'Face Detection Model',
      'max_recognition_attempts': 'Max Recognition Attempts',
      'image_compression_quality': 'Image Compression Quality (%)',
      'image_max_size': 'Image Max Size (pixels)',

      // Automation settings
      'auto_absent_enabled': 'Auto-Absent Enabled',

      // System settings
      'system_name': 'System Name',
      'theme_primary_color': 'Primary Theme Color',
      'theme_secondary_color': 'Secondary Theme Color',
      'system_logo_url': 'System Logo URL',
      'welcome_message': 'Welcome Message',
      'user_guide': 'User Guide'
    };
    return displayNames[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  getSettingDescription(key: string): string {
    const descriptions: { [key: string]: string } = {
      // Attendance settings
      'absent_threshold_minutes': 'Minutes after class start to mark as absent',
      'late_threshold_minutes': 'Minutes after class start to mark as late',
      'attendance_grace_period_minutes': 'Extra time before class starts for early attendance',
      'auto_absent_delay_hours': 'Hours after class end to wait before marking unenrolled students as absent',
      'duplicate_prevention_window_minutes': 'Minutes to prevent duplicate attendance marks',
      'allow_makeup_attendance': 'Allow marking attendance after class has ended',
      'makeup_deadline_hours': 'Hours after class end when makeup attendance is allowed',

      // Recognition settings
      'recognition_threshold': 'Minimum confidence score for face recognition (0.0-1.0)',
      'min_face_confidence': 'Minimum confidence for face detection (0.0-1.0)',
      'face_detection_model': 'Algorithm used for detecting faces in images',
      'max_recognition_attempts': 'Maximum failed recognition attempts before fallback',
      'image_compression_quality': 'JPEG compression quality for stored face images (1-100)',
      'image_max_size': 'Maximum dimension for face images in pixels',

      // Automation settings
      'auto_absent_enabled': 'Automatically mark unenrolled students as absent',

      // System settings
      'system_name': 'Display name for the FRAS system',
      'theme_primary_color': 'Primary color for the user interface',
      'theme_secondary_color': 'Secondary color for the user interface',
      'system_logo_url': 'URL path to the system logo image',
      'welcome_message': 'Message displayed on the login/welcome page',
      'user_guide': 'Instructions for users on how to use the system'
    };
    return descriptions[key] || '';
  }

  getSettingMin(key: string): number | null {
    const mins: { [key: string]: number } = {
      'absent_threshold_minutes': 1,
      'late_threshold_minutes': 1,
      'attendance_grace_period_minutes': 0,
      'auto_absent_delay_hours': 0,
      'duplicate_prevention_window_minutes': 1,
      'makeup_deadline_hours': 1,
      'recognition_threshold': 0.1,
      'min_face_confidence': 0.1,
      'max_recognition_attempts': 1,
      'image_compression_quality': 1,
      'image_max_size': 100
    };
    return mins[key] || null;
  }

  getSettingMax(key: string): number | null {
    const maxs: { [key: string]: number } = {
      'absent_threshold_minutes': 480,
      'late_threshold_minutes': 480,
      'attendance_grace_period_minutes': 60,
      'auto_absent_delay_hours': 168,
      'duplicate_prevention_window_minutes': 60,
      'makeup_deadline_hours': 168,
      'recognition_threshold': 1.0,
      'min_face_confidence': 1.0,
      'max_recognition_attempts': 10,
      'image_compression_quality': 100,
      'image_max_size': 2048
    };
    return maxs[key] || null;
  }

  getSettingStep(key: string): number {
    const steps: { [key: string]: number } = {
      'recognition_threshold': 0.1,
      'min_face_confidence': 0.1,
      'image_compression_quality': 5
    };
    return steps[key] || 1;
  }
}