import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../api.service';
import { AuthService } from '../auth.service';

interface SupportTicket {
  ticket_id: number;
  user_id: number;
  subject: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  assigned_to?: number;
  created_at: string;
  updated_at: string;
  user_email?: string;
  assigned_email?: string;
}

interface TicketReply {
  reply_id: number;
  ticket_id: number;
  user_id: number;
  message: string;
  is_internal: boolean;
  created_at: string;
  user_email?: string;
}

@Component({
  selector: 'app-support-tickets',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './support-tickets.component.html',
  styleUrls: ['./support-tickets.component.css']
})
export class SupportTicketsComponent implements OnInit {
  tickets: SupportTicket[] = [];
  filteredTickets: SupportTicket[] = [];
  selectedTicket: SupportTicket | null = null;
  replies: TicketReply[] = [];
  loading = false;
  error = '';
  success = '';

  // Filters
  statusFilter = '';
  priorityFilter = '';

  // Update form
  updateForm = {
    status: '',
    priority: '',
    assigned_to: ''
  };

  // Reply form
  newReply = {
    message: '',
    is_internal: false
  };

  statuses = ['open', 'in_progress', 'resolved', 'closed'];
  priorities = ['low', 'medium', 'high', 'critical'];

  constructor(
    private apiService: ApiService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadTickets();
  }

  loadTickets(): void {
    this.loading = true;
    this.error = '';

    this.apiService.getSupportTickets(this.statusFilter, this.priorityFilter).subscribe({
      next: (tickets: SupportTicket[]) => {
        this.tickets = tickets;
        this.filteredTickets = tickets;
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Failed to load tickets: ' + (err.error?.message || err.message);
        this.loading = false;
      }
    });
  }

  applyFilters(): void {
    this.loadTickets();
  }

  selectTicket(ticket: SupportTicket): void {
    this.selectedTicket = ticket;
    this.updateForm = {
      status: ticket.status,
      priority: ticket.priority,
      assigned_to: ticket.assigned_to?.toString() || ''
    };
    this.loadReplies(ticket.ticket_id);
  }

  loadReplies(ticketId: number): void {
    this.apiService.getTicketReplies(ticketId).subscribe({
      next: (replies: TicketReply[]) => {
        this.replies = replies;
      },
      error: (err: any) => {
        console.error('Failed to load replies:', err);
      }
    });
  }

  updateTicket(): void {
    if (!this.selectedTicket) return;

    const update = {
      status: this.updateForm.status || undefined,
      priority: this.updateForm.priority || undefined,
      assigned_to: this.updateForm.assigned_to ? parseInt(this.updateForm.assigned_to) : undefined
    };

    this.apiService.updateSupportTicket(this.selectedTicket.ticket_id, update).subscribe({
      next: () => {
        this.success = 'Ticket updated successfully';
        this.loadTickets();
        if (this.selectedTicket) {
          this.selectTicket(this.selectedTicket);
        }
      },
      error: (err: any) => {
        this.error = 'Failed to update ticket: ' + (err.error?.message || err.message);
      }
    });
  }

  addReply(): void {
    if (!this.selectedTicket || !this.newReply.message.trim()) return;

    this.apiService.addTicketReply(this.selectedTicket.ticket_id, this.newReply).subscribe({
      next: () => {
        this.newReply = { message: '', is_internal: false };
        this.loadReplies(this.selectedTicket!.ticket_id);
        this.success = 'Reply added successfully';
      },
      error: (err: any) => {
        this.error = 'Failed to add reply: ' + (err.error?.message || err.message);
      }
    });
  }

  getPriorityClass(priority: string): string {
    switch (priority) {
      case 'critical': return 'badge-danger';
      case 'high': return 'badge-warning';
      case 'medium': return 'badge-info';
      case 'low': return 'badge-secondary';
      default: return 'badge-secondary';
    }
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'open': return 'badge-primary';
      case 'in_progress': return 'badge-warning';
      case 'resolved': return 'badge-success';
      case 'closed': return 'badge-secondary';
      default: return 'badge-secondary';
    }
  }

  hasPermission(permission: string): boolean {
    const currentUser = this.authService.getCurrentUser();
    return currentUser ? currentUser.permissions.includes(permission) : false;
  }
}