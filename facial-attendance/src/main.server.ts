import { AppComponent } from './app/app.component';
import { appConfig } from './app/app.config';
import { bootstrapApplication } from '@angular/platform-browser';

export function bootstrap() {
  return bootstrapApplication(AppComponent, appConfig);
}
