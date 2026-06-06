import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { V2ActionButtonComponent } from './v2-action-button/v2-action-button.component';
import { V2ClassCardComponent } from './v2-class-card/v2-class-card.component';
import { V2DataTableComponent } from './v2-data-table/v2-data-table.component';
import { V2PageHeaderComponent } from './v2-page-header/v2-page-header.component';
import { V2PresenceRatioBarComponent } from './v2-presence-ratio-bar/v2-presence-ratio-bar.component';
import { V2SearchFilterBarComponent } from './v2-search-filter-bar/v2-search-filter-bar.component';
import { V2SidebarComponent } from './v2-sidebar/v2-sidebar.component';
import { V2StatCardComponent } from './v2-stat-card/v2-stat-card.component';
import { V2StatusBadgeComponent } from './v2-status-badge/v2-status-badge.component';
import { V2StudentDetailDrawerComponent } from './v2-student-detail-drawer/v2-student-detail-drawer.component';
import { V2TimelineComponent } from './v2-timeline/v2-timeline.component';
import { V2TopbarComponent } from './v2-topbar/v2-topbar.component';

const COMPONENTS = [
  V2ActionButtonComponent,
  V2ClassCardComponent,
  V2DataTableComponent,
  V2PageHeaderComponent,
  V2PresenceRatioBarComponent,
  V2SearchFilterBarComponent,
  V2SidebarComponent,
  V2StatCardComponent,
  V2StatusBadgeComponent,
  V2StudentDetailDrawerComponent,
  V2TimelineComponent,
  V2TopbarComponent
];

@NgModule({
  declarations: COMPONENTS,
  imports: [CommonModule, FormsModule, RouterModule],
  exports: COMPONENTS
})
export class V2UiModule {}
