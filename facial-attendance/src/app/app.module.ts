import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { IonicModule } from '@ionic/angular';
import { WebcamModule } from 'ngx-webcam';
import { AppComponent } from './app.component';
import { RouterModule } from '@angular/router';
import { routes } from './app.routes';
import { WebcamCaptureComponent } from './webcam-capture/webcam-capture.component';
import { NavbarComponent } from './components/navbar/navbar.component';
import { AttendanceMonitorComponent } from './attendance-monitor/attendance-monitor.component';
import { AttendanceLogsComponent } from './attendance-logs/attendance-logs.component';
import { RoomScheduleComponent } from './room-schedule/room-schedule.component';
import { RegistrationComponent } from './registration/registration.component';
import { ScheduleUploadComponent } from './schedule-upload/schedule-upload.component';
import { RoomScheduleEditorComponent } from './room-schedule-editor/room-schedule-editor.component';
// Import other components as needed

@NgModule({
  declarations: [
    AppComponent,
    WebcamCaptureComponent,
    NavbarComponent,
    AttendanceMonitorComponent,
    AttendanceLogsComponent,
    RoomScheduleComponent,
    RegistrationComponent,
    ScheduleUploadComponent,
    RoomScheduleEditorComponent
  ],
  imports: [
  BrowserModule,
  FormsModule,
  ReactiveFormsModule,
  CommonModule,
  HttpClientModule,
  IonicModule.forRoot(),
  WebcamModule,
  RouterModule.forRoot(routes)
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule {}
