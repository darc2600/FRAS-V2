import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { V2UiModule } from '../../components';
import { V2SessionHistoryComponent } from './session-history.component';

const routes: Routes = [
  { path: '', component: V2SessionHistoryComponent }
];

@NgModule({
  declarations: [V2SessionHistoryComponent],
  imports: [
    CommonModule,
    FormsModule,
    V2UiModule,
    RouterModule.forChild(routes)
  ]
})
export class V2SessionHistoryModule {}
