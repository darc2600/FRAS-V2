import { Component } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { filter } from 'rxjs/operators';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'facial-attendance';
  sidebarOpen = true;
  hideSidebar = false;

  constructor(private router: Router) {
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.checkRoute();
      });

    this.checkRoute();
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  checkRoute() {
    const currentUrl = this.router.url;
    this.hideSidebar =
      currentUrl.includes('/login') ||
      currentUrl.includes('/registration');
  }
}
