import { Component, Input } from '@angular/core';

export type V2StatTone = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'review' | 'break' | 'excused';

@Component({
  selector: 'app-v2-stat-card',
  templateUrl: './v2-stat-card.component.html',
  styleUrls: ['./v2-stat-card.component.scss']
})
export class V2StatCardComponent {
  @Input() label = '';
  @Input() value: string | number = '';
  @Input() helperText = '';
  @Input() tone: V2StatTone = 'default';
}
