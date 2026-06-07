import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';

import { V2UiModule } from '../../components/v2-ui.module';
import { V2StudentClassHistoryComponent } from './student-class-history.component';

const routes: Routes = [
  { path: '', component: V2StudentClassHistoryComponent }
];

@NgModule({
  declarations: [V2StudentClassHistoryComponent],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild(routes),
    V2UiModule
  ]
})
export class V2StudentClassHistoryModule {}
