import { Component, EventEmitter, Input, Output } from '@angular/core';

export type V2ClassCardStatus = 'upcoming' | 'ongoing' | 'completed' | 'needs_review';

@Component({
  selector: 'app-v2-class-card',
  templateUrl: './v2-class-card.component.html',
  styleUrls: ['./v2-class-card.component.scss']
})
export class V2ClassCardComponent {
  @Input() courseCode = '';
  @Input() courseName = '';
  @Input() room = '';
  @Input() schedule = '';
  @Input() studentCount = 0;
  @Input() status: V2ClassCardStatus = 'upcoming';
  @Input() primaryActionLabel = 'Start Monitoring';
  @Input() primaryActionDisabled = false;
  @Input() secondaryActions: string[] = [];
  @Output() primaryAction = new EventEmitter<void>();
  @Output() secondaryAction = new EventEmitter<string>();

  get statusTone(): 'success' | 'warning' | 'danger' | 'info' | 'neutral' {
    const tones = {
      upcoming: 'info',
      ongoing: 'warning',
      completed: 'success',
      needs_review: 'danger'
    } as const;
    return tones[this.status];
  }
}
