import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-v2-page-header',
  templateUrl: './v2-page-header.component.html',
  styleUrls: ['./v2-page-header.component.scss']
})
export class V2PageHeaderComponent {
  @Input() title = '';
  @Input() subtitle = '';
  @Input() metadata: string[] = [];
  @Input() primaryActionLabel = '';
  @Output() primaryAction = new EventEmitter<void>();
}
