import { Component, Input } from '@angular/core';
import { V2StatusTone } from '../v2-status-badge/v2-status-badge.component';

export type V2TimelineEvent = {
  time: string;
  type: 'time_in' | 'break_out' | 'break_in' | 'time_out' | 'warning';
  title: string;
  description?: string;
  evidenceLabel?: string;
};

@Component({
  selector: 'app-v2-timeline',
  templateUrl: './v2-timeline.component.html',
  styleUrls: ['./v2-timeline.component.scss']
})
export class V2TimelineComponent {
  @Input() events: V2TimelineEvent[] = [];
  @Input() compact = false;

  toneFor(type: V2TimelineEvent['type']): V2StatusTone {
    if (type === 'time_in') return 'success';
    if (type === 'break_out' || type === 'break_in') return 'info';
    if (type === 'warning') return 'danger';
    return 'neutral';
  }
}
