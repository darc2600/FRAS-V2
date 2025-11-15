import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface User {
  email: string;
  role: string;
  userId: number;
  token: string;
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
      const role = localStorage.getItem('authRole');
      const userId = localStorage.getItem('authUserId');
      const email = localStorage.getItem('authEmail');

      if (token && role && userId && email) {
        const user: User = {
          email,
          role,
          userId: parseInt(userId),
          token
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
    localStorage.setItem('authRole', user.role);
    localStorage.setItem('authUserId', user.userId.toString());
    localStorage.setItem('authEmail', user.email);
    this.currentUserSubject.next(user);
  }

  logout(): void {
    localStorage.removeItem('authToken');
    localStorage.removeItem('authRole');
    localStorage.removeItem('authUserId');
    localStorage.removeItem('authEmail');
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
    return user ? user.role === role : false;
  }

  isAdmin(): boolean {
    return this.hasRole('admin');
  }

  isInstructor(): boolean {
    return this.hasRole('instructor');
  }

  hasAnyRole(roles: string[]): boolean {
    const user = this.currentUserSubject.value;
    return user ? roles.includes(user.role) : false;
  }
}