import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface User {
  email: string;
  user_type: string;
  userId: number;
  token: string;
  permissions: string[];
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor() {
    // Load user from localStorage on service initialization
    this.loadUserFromStorage();
  }

  private loadUserFromStorage(): void {
    try {
      const token = localStorage.getItem('authToken');
      const user_type = localStorage.getItem('authUserType');
      const userId = localStorage.getItem('authUserId');
      const email = localStorage.getItem('authEmail');
      const permissions = localStorage.getItem('authPermissions');

      if (token && user_type && userId && email && permissions) {
        const user: User = {
          email,
          user_type,
          userId: parseInt(userId),
          token,
          permissions: JSON.parse(permissions)
        };
        this.currentUserSubject.next(user);
      }
    } catch (error) {
      console.error('Error loading user from storage:', error);
    }
  }

  login(user: User): void {
    if (!user.userId) {
      console.error('Cannot login: userId is undefined');
      return;
    }
    localStorage.setItem('authToken', user.token);
    localStorage.setItem('authUserType', user.user_type);
    localStorage.setItem('authUserId', user.userId.toString());
    localStorage.setItem('authEmail', user.email);
    localStorage.setItem('authPermissions', JSON.stringify(user.permissions));
    this.currentUserSubject.next(user);
  }

  logout(): void {
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUserType');
    localStorage.removeItem('authUserId');
    localStorage.removeItem('authEmail');
    localStorage.removeItem('authPermissions');
    this.currentUserSubject.next(null);
  }

  getToken(): string | null {
    return localStorage.getItem('authToken');
  }

  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  isAuthenticated(): boolean {
    return this.currentUserSubject.value !== null;
  }

  hasRole(role: string): boolean {
    const user = this.currentUserSubject.value;
    return user ? user.user_type === role : false;
  }

  isAdmin(): boolean {
    return this.hasRole('it_admin') || this.hasRole('super_admin');
  }

  isSuperAdmin(): boolean {
    return this.hasRole('super_admin');
  }

  isITAdmin(): boolean {
    return this.hasRole('it_admin');
  }

  isInstructor(): boolean {
    return this.hasRole('instructor') || this.hasRole('regular');
  }

  hasAnyRole(roles: string[]): boolean {
    const user = this.currentUserSubject.value;
    return user ? roles.includes(user.user_type) : false;
  }

  hasPermission(permission: string): boolean {
    const user = this.currentUserSubject.value;
    return user ? user.permissions.includes(permission) : false;
  }

  hasAnyPermission(permissions: string[]): boolean {
    const user = this.currentUserSubject.value;
    return user ? permissions.some(perm => user.permissions.includes(perm)) : false;
  }
}