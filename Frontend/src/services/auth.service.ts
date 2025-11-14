import { apiClient } from './api.service';
import type {
  RegisterRequest,
  LoginRequest,
  AuthenticationResponseApiResponse,
} from '@/types/auth.types';

// Helper to get client IP and user agent
const getClientInfo = () => {
  return {
    ipAddress: '0.0.0.0', // Browser can't access real IP, backend should handle this
    userAgent: navigator.userAgent,
    deviceFingerprint: undefined, // Optional, can be implemented later
  };
};

export const authService = {
  /**
   * Register a new user account
   */
  async register(data: Omit<RegisterRequest, 'ipAddress' | 'userAgent'>): Promise<AuthenticationResponseApiResponse> {
    const response = await apiClient.post<AuthenticationResponseApiResponse>(
      '/auth/register',
      data
    );
    return response.data;
  },

  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<AuthenticationResponseApiResponse> {
    const clientInfo = getClientInfo();
    const loginData: LoginRequest = {
      email,
      password,
      ...clientInfo,
    };

    const response = await apiClient.post<AuthenticationResponseApiResponse>(
      '/auth/login',
      loginData
    );
    return response.data;
  },

  /**
   * Logout - clear local token
   */
  logout(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  },

  /**
   * Get current user from localStorage
   */
  getCurrentUser() {
    const userInfo = localStorage.getItem('user_info');
    return userInfo ? JSON.parse(userInfo) : null;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token');
  },
};
