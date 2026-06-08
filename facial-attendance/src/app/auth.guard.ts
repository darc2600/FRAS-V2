import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, CanDeactivate, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { AuthService } from './auth.service';

export const SESSION_BREAK_LOCK_KEY = 'frasV2BreakSessionId';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(): boolean {
    if (this.authService.isAuthenticated()) {
      return true;
    } else {
      this.router.navigate(['/login']);
      return false;
    }
  }
}

@Injectable({
  providedIn: 'root'
})
export class AdminGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(): boolean {
    if (this.authService.isAuthenticated() && this.authService.isAdmin()) {
      return true;
    } else {
      this.router.navigate(['/login']);
      return false;
    }
  }
}

@Injectable({
  providedIn: 'root'
})
export class AnalyticsGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(): boolean {
    if (
      this.authService.isAuthenticated() &&
      this.authService.hasAnyPermission(['view_analytics', 'view_all_data'])
    ) {
      return true;
    } else {
      this.router.navigate(['/login']);
      return false;
    }
  }
}

@Injectable({
  providedIn: 'root'
})
export class SessionBreakGuard implements CanActivate, CanDeactivate<any> {
  constructor(private router: Router) {}

  canActivate(_route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean | UrlTree {
    const lockedSessionId = localStorage.getItem(SESSION_BREAK_LOCK_KEY);
    if (!lockedSessionId) return true;

    const targetUrl = state.url || '';
    if (targetUrl.startsWith(`/live-session/${lockedSessionId}`)) return true;
    if (targetUrl.startsWith('/login')) return true;

    return this.router.createUrlTree(['/live-session', lockedSessionId]);
  }

  canDeactivate(component: any): boolean {
    if (component?.isBreakMode) {
      component.actionMessage = component?.breakUnlocked
        ? 'Session Break is still active. End break before leaving this page.'
        : 'Session Break is active. Unlock and end break before leaving this page.';
      return false;
    }
    return true;
  }
}
