import { Component, Input } from '@angular/core';

export type V2SidebarItem = {
  label: string;
  icon?: string;
  href?: string;
  active?: boolean;
};

@Component({
  selector: 'app-v2-sidebar',
  templateUrl: './v2-sidebar.component.html',
  styleUrls: ['./v2-sidebar.component.scss']
})
export class V2SidebarComponent {
  @Input() brandName = 'Mapua University';
  @Input() productName = 'Attendance Suite';
  @Input() items: V2SidebarItem[] = [];
  @Input() userName = '';
  @Input() userRole = 'Course Monitor';
  @Input() userInitials = '';
}
