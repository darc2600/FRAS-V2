import { Component, Input } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../auth.service';

@Component({
  selector: 'app-profile-sidebar',
  templateUrl: './profile-sidebar.component.html',
  styleUrls: ['./profile-sidebar.component.css']
})
export class ProfileSidebarComponent {
  @Input() isOpen: boolean = false;

  constructor(private router: Router, private authService: AuthService) {}

  signOut() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
