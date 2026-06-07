import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { V2UiModule } from '../../components';
import { V2StudentEvidenceComponent } from './student-evidence.component';

const routes: Routes = [
  { path: ':sessionId/:studentId', component: V2StudentEvidenceComponent }
];

@NgModule({
  declarations: [V2StudentEvidenceComponent],
  imports: [
    CommonModule,
    FormsModule,
    V2UiModule,
    RouterModule.forChild(routes)
  ]
})
export class V2StudentEvidenceModule {}
