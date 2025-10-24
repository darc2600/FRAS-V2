import { Component, Input } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-profile-sidebar',
  templateUrl: './profile-sidebar.component.html',
  styleUrls: ['./profile-sidebar.component.css']
})
export class ProfileSidebarComponent {
  @Input() isOpen: boolean = false;

  constructor(private router: Router) {}

  signOut() {
    // Add any sign-out logic here (e.g., clear tokens)
    this.router.navigate(['/login']);
  }
}
