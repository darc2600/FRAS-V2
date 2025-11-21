import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-submit-support',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './submit-support.component.html',
  styleUrls: ['./submit-support.component.css']
})
export class SubmitSupportComponent {
  ticket = {
    subject: '',
    description: '',
    category: 'technical',
    priority: 'medium'
  };

  loading = false;
  error = '';
  success = '';

  categories = [
    { value: 'technical', label: 'Technical Issue' },
    { value: 'account', label: 'Account Problem' },
    { value: 'attendance', label: 'Attendance Issue' },
    { value: 'feature', label: 'Feature Request' },
    { value: 'other', label: 'Other' }
  ];

  priorities = [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
    { value: 'critical', label: 'Critical' }
  ];

  constructor(
    private apiService: ApiService,
    public authService: AuthService
  ) {}

  submitTicket(): void {
    if (!this.ticket.subject || !this.ticket.description) {
      this.error = 'Please fill in all required fields';
      return;
    }

    this.loading = true;
    this.error = '';
    this.success = '';

    this.apiService.submitSupportTicket(this.ticket).subscribe({
      next: (response: any) => {
        this.success = 'Support ticket submitted successfully! Ticket ID: ' + response.ticket_id;
        this.ticket = { subject: '', description: '', category: 'technical', priority: 'medium' };
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Failed to submit ticket: ' + (err.error?.message || err.message);
        this.loading = false;
      }
    });
  }

  hasPermission(permission: string): boolean {
    const currentUser = this.authService.getCurrentUser();
    return currentUser ? currentUser.permissions.includes(permission) : false;
  }
}