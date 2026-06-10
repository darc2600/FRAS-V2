import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { IonicModule } from '@ionic/angular';
import { WebcamModule } from 'ngx-webcam';
import { AppComponent } from './app.component';
import { RouterModule } from '@angular/router';
import { routes } from './app.routes';
import { NavbarComponent } from './components/navbar/navbar.component';
import { LoginComponent } from './login/login.component';
import { AuthInterceptor } from './auth.interceptor';
import { V2UiModule } from './v2/components';
import { V2TodaysClassesComponent } from './v2/pages/todays-classes/todays-classes.component';
import { V2LiveSessionComponent } from './v2/pages/live-session/live-session.component';

@NgModule({
  declarations: [
    AppComponent,
    NavbarComponent,
    V2TodaysClassesComponent,
    V2LiveSessionComponent,
    LoginComponent
  ],
  imports: [
  BrowserModule,
  FormsModule,
  ReactiveFormsModule,
  CommonModule,
  HttpClientModule,
  IonicModule.forRoot(),
  WebcamModule,
  V2UiModule,
  RouterModule.forRoot(routes)
  ],
  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}
