import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';

import { V2UiModule } from '../../components/v2-ui.module';
import { V2ClassRosterComponent } from './class-roster.component';

const routes: Routes = [
  { path: '', component: V2ClassRosterComponent }
];

@NgModule({
  declarations: [V2ClassRosterComponent],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild(routes),
    V2UiModule
  ]
})
export class V2ClassRosterModule {}
