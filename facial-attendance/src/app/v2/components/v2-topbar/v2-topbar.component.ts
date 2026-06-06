import { Component, Input } from '@angular/core';

export type V2TopbarTab = {
  label: string;
  active?: boolean;
  href?: string;
};

@Component({
  selector: 'app-v2-topbar',
  templateUrl: './v2-topbar.component.html',
  styleUrls: ['./v2-topbar.component.scss']
})
export class V2TopbarComponent {
  @Input() title = 'Attendance Suite';
  @Input() tabs: V2TopbarTab[] = [];
  @Input() searchPlaceholder = '';
  @Input() statusLabel = '';
  @Input() avatarInitials = '';
}
