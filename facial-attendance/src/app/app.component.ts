import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavbarComponent } from './components/navbar/navbar.component';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'facial-attendance';
  sidebarOpen = false;

  get hideSidebar(): boolean {
    const currentUrl = window.location.pathname;
    return currentUrl.includes('/login') || currentUrl.includes('/registration');
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }
}
