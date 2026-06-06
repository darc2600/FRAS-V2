import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-v2-presence-ratio-bar',
  templateUrl: './v2-presence-ratio-bar.component.html',
  styleUrls: ['./v2-presence-ratio-bar.component.scss']
})
export class V2PresenceRatioBarComponent {
  @Input() insideSeconds = 0;
  @Input() outsideSeconds = 0;
  @Input() untrackedSeconds = 0;
  @Input() sessionSeconds = 1;
  @Input() showLegend = true;

  percent(value: number): number {
    const total = Math.max(this.sessionSeconds, 1);
    return Math.max(0, Math.min(100, (value / total) * 100));
  }
}
