import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { V2UiModule } from '../../components';
import { V2PostSessionReviewComponent } from './post-session-review.component';

const routes: Routes = [
  { path: ':sessionId', component: V2PostSessionReviewComponent }
];

@NgModule({
  declarations: [V2PostSessionReviewComponent],
  imports: [
    CommonModule,
    FormsModule,
    V2UiModule,
    RouterModule.forChild(routes)
  ]
})
export class V2PostSessionReviewModule {}
