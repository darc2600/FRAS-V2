import { Component, Input } from '@angular/core';

export type V2StatusTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'excused' | 'primary';

@Component({
  selector: 'app-v2-status-badge',
  templateUrl: './v2-status-badge.component.html',
  styleUrls: ['./v2-status-badge.component.scss']
})
export class V2StatusBadgeComponent {
  @Input() label = '';
  @Input() tone: V2StatusTone = 'neutral';
}
