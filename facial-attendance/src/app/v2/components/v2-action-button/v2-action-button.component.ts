import { Component, EventEmitter, Input, Output } from '@angular/core';

export type V2ButtonVariant = 'primary' | 'outline' | 'secondary' | 'danger' | 'ghost' | 'warning';
export type V2ButtonSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-v2-action-button',
  templateUrl: './v2-action-button.component.html',
  styleUrls: ['./v2-action-button.component.scss']
})
export class V2ActionButtonComponent {
  @Input() label = '';
  @Input() variant: V2ButtonVariant = 'primary';
  @Input() size: V2ButtonSize = 'md';
  @Input() icon = '';
  @Input() disabled = false;
  @Input() type: 'button' | 'submit' = 'button';
  @Output() action = new EventEmitter<void>();
}
