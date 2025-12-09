import { Component, OnInit } from '@angular/core';
import { CommonModule, KeyValuePipe, TitleCasePipe } from '@angular/common';
import { ApiService } from '../api.service';
import { AuthService } from '../auth.service';

interface SystemSetting {
  key: string;
  value: string;
  type: string;
  category?: string;
  options?: string[];
  min?: number;
  max?: number;
  step?: number;
  display_name?: string;
}

interface CategorizedSettings {
  [category: string]: { [key: string]: SystemSetting };
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
  categorizedSettings: CategorizedSettings = {};
  loading = false;
  error = '';
  success = '';

  // Pending changes system
  pendingChanges: { [key: string]: string } = {};
  showConfirmModal = false;
  savingChanges = false;
  markingAbsents = false;

  // Category definitions with display names
  categories = {
    facial_recognition: 'Facial Recognition',
    attendance: 'Attendance Logic',
    image_processing: 'Image Processing',
    performance: 'Performance',
    security: 'Security & Privacy',
    ux: 'User Experience',
    hardware: 'Hardware & Devices',
    system: 'System Configuration',
    theme: 'Theme & Appearance',
    content: 'Content & Messages',
    logo: 'Branding',
    config: 'General Configuration'
  };

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
        this.categorizeSettings();
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
        this.categorizeSettings();
      }
    });
  }

  categorizeSettings(): void {
    this.categorizedSettings = {};

    Object.keys(this.settings).forEach(key => {
      const setting = this.settings[key];
      const category = setting.category || 'config'; // Default to 'config' if no category

      if (!this.categorizedSettings[category]) {
        this.categorizedSettings[category] = {};
      }

      this.categorizedSettings[category][key] = setting;
    });
  }

  updateSetting(key: string, value: string): void {
    this.error = '';
    this.success = '';

    // Stage the change instead of saving immediately
    const currentValue = this.settings[key]?.value;
    if (currentValue !== value) {
      this.pendingChanges[key] = value;
    } else {
      // If setting back to original value, remove from pending changes
      delete this.pendingChanges[key];
    }
  }

  hasPendingChanges(): boolean {
    return Object.keys(this.pendingChanges).length > 0;
  }

  getPendingChangesCount(): number {
    return Object.keys(this.pendingChanges).length;
  }

  getPendingChangeValue(key: string): string {
    return this.pendingChanges[key] || this.settings[key]?.value || '';
  }

  isSettingModified(key: string): boolean {
    return key in this.pendingChanges;
  }

  savePendingChanges(): void {
    console.log('savePendingChanges called');
    if (!this.hasPendingChanges()) {
      console.log('No pending changes');
      return;
    }

    console.log('Pending changes:', this.pendingChanges);
    this.savingChanges = true;
    this.error = '';
    this.success = '';

    // Save all pending changes in bulk
    const updates = Object.entries(this.pendingChanges).map(([key, value]) => ({
      key: key,
      value: value
    }));

    console.log('Updates to send:', updates);
    this.apiService.updateSettings(updates).subscribe({
      next: (response) => {
        console.log('API response:', response);
        this.success = `Successfully updated ${this.getPendingChangesCount()} setting(s)`;
        this.pendingChanges = {};
        this.showConfirmModal = false;
        // Refresh settings to get updated values
        this.loadSettings();
      },
      error: (err) => {
        console.error('API error:', err);
        this.error = 'Failed to save settings: ' + (err.error?.message || err.message);
      },
      complete: () => {
        this.savingChanges = false;
      }
    });
  }

  cancelPendingChanges(): void {
    this.pendingChanges = {};
    this.showConfirmModal = false;
    this.error = '';
    this.success = '';
  }

  openConfirmModal(): void {
    console.log('openConfirmModal called');
    if (this.hasPendingChanges()) {
      console.log('Has pending changes, showing modal');
      this.showConfirmModal = true;
      console.log('showConfirmModal set to:', this.showConfirmModal);
    } else {
      console.log('No pending changes, not showing modal');
    }
  }

  closeConfirmModal(): void {
    console.log('closeConfirmModal called');
    this.showConfirmModal = false;
    console.log('showConfirmModal set to:', this.showConfirmModal);
  }

  getPendingChangesList(): any[] {
    return Object.keys(this.pendingChanges).map(key => {
      const setting = this.settings[key];
      return {
        key: key,
        displayName: setting ? setting.display_name || key : key,
        currentValue: setting ? this.formatSettingValue(setting) : '',
        newValue: this.formatSettingValue({ ...setting, value: this.pendingChanges[key] })
      };
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

  onBooleanSettingChange(key: string, event: Event): void {
    const target = event.target as HTMLInputElement;
    this.updateSetting(key, target.checked ? 'true' : 'false');
  }

  onTextSettingChange(key: string, event: Event): void {
    const target = event.target as HTMLInputElement;
    this.updateSetting(key, target.value);
  }

  isBooleanSetting(setting: SystemSetting): boolean {
    return setting.type === 'boolean';
  }

  isNumberSetting(setting: SystemSetting): boolean {
    return setting.type === 'number';
  }

  isSelectSetting(setting: SystemSetting): boolean {
    return setting.type === 'select';
  }

  isTextSetting(setting: SystemSetting): boolean {
    return !setting.type || setting.type === 'text' || setting.type === 'string' || setting.type === 'config' || setting.type === 'theme' || setting.type === 'content' || setting.type === 'logo';
  }

  getCategoryKeys(): string[] {
    return Object.keys(this.categorizedSettings).sort((a, b) => {
      // Define priority order for categories
      const priorityOrder = ['facial_recognition', 'attendance', 'system', 'performance', 'security', 'ux', 'hardware', 'image_processing'];
      const aIndex = priorityOrder.indexOf(a);
      const bIndex = priorityOrder.indexOf(b);

      if (aIndex !== -1 && bIndex !== -1) {
        return aIndex - bIndex;
      }
      if (aIndex !== -1) return -1;
      if (bIndex !== -1) return 1;

      return a.localeCompare(b);
    });
  }

  getCategoryDisplayName(category: string): string {
    return this.categories[category as keyof typeof this.categories] || category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  formatSettingKey(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  onSelectSettingChange(key: string, event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.updateSetting(key, target.value);
  }

  onNumberSettingChange(key: string, event: Event): void {
    const target = event.target as HTMLInputElement;
    const value = target.value;
    const setting = this.settings[key];

    // Basic validation
    if (setting.min !== undefined && parseFloat(value) < setting.min) {
      this.error = `Value must be at least ${setting.min}`;
      return;
    }
    if (setting.max !== undefined && parseFloat(value) > setting.max) {
      this.error = `Value must be at most ${setting.max}`;
      return;
    }

    this.updateSetting(key, value);
  }

  formatSettingValue(setting: SystemSetting): string {
    if (!setting) return '';

    switch (setting.type) {
      case 'boolean':
        return setting.value === 'true' ? 'Yes' : 'No';
      case 'number':
        return setting.value;
      case 'select':
        return setting.value;
      case 'text':
        return setting.value;
      default:
        return setting.value;
    }
  }

  markAutomaticAbsents(): void {
    this.error = '';
    this.success = '';
    this.markingAbsents = true;

    this.apiService.markAutomaticAbsents().subscribe({
      next: (response) => {
        this.success = 'Automatic absent marking completed successfully';
        this.markingAbsents = false;
      },
      error: (error) => {
        this.error = 'Failed to mark automatic absents: ' + error.message;
        this.markingAbsents = false;
      }
    });
  }

  getAutoAbsentThreshold(): string {
    const setting = this.settings['auto_mark_absent_after_minutes'];
    return setting ? setting.value : '45';
  }
}