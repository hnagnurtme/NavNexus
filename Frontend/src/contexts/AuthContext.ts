import React, { createContext, useContext, useEffect, useState, type PropsWithChildren } from 'react';
import { authService } from '@/services/auth.service';
import type { AuthenticationResponse } from '@/types/auth.types';

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  phoneNumber: string;
  emailVerified: boolean;
};

type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  isActionLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (fullName: string, email: string, password: string, phoneNumber: string) => Promise<void>;
  signOutUser: () => Promise<void>;
};

const STORAGE_KEY = 'user_info';

const readJson = <T,>(key: string): T | null => {
  if (typeof window === 'undefined') return null;
  try {
    return JSON.parse(localStorage.getItem(key) || 'null') as T;
  } catch {
    localStorage.removeItem(key);
    return null;
  }
};

const writeJson = (key: string, value: unknown) => {
  if (typeof window !== 'undefined') localStorage.setItem(key, JSON.stringify(value));
};

const mapAuthResponseToUser = (authResponse: AuthenticationResponse): AuthUser => {
  return {
    id: authResponse.id,
    name: authResponse.fullName || '',
    email: authResponse.email || '',
    phoneNumber: authResponse.phoneNumber || '',
    emailVerified: authResponse.emailVerified,
  };
};

export const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider = ({ children }: PropsWithChildren<{}>) => {
  const [user, setUser] = useState<AuthUser | null>(() => readJson<AuthUser>(STORAGE_KEY));
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    setIsInitializing(false);
  }, []);

  const signIn = async (email: string, password: string) => {
    setIsActionLoading(true);
    try {
      const response = await authService.login(email, password);
      
      if (!response.success || !response.data) {
        throw new Error(response.message || 'Login failed');
      }

      // Store the access token
      if (response.data.accessToken) {
        localStorage.setItem('auth_token', response.data.accessToken);
      }

      // Map and store user info
      const nextUser = mapAuthResponseToUser(response.data);
      setUser(nextUser);
      writeJson(STORAGE_KEY, nextUser);
    } finally {
      setIsActionLoading(false);
    }
  };

  const signUp = async (fullName: string, email: string, password: string, phoneNumber: string) => {
    setIsActionLoading(true);
    try {
      const response = await authService.register({
        email,
        password,
        fullName,
        phoneNumber,
      });

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Registration failed');
      }

      // Store the access token
      if (response.data.accessToken) {
        localStorage.setItem('auth_token', response.data.accessToken);
      }

      // Map and store user info
      const nextUser = mapAuthResponseToUser(response.data);
      setUser(nextUser);
      writeJson(STORAGE_KEY, nextUser);
    } finally {
      setIsActionLoading(false);
    }
  };

  const signOutUser = async () => {
    setIsActionLoading(true);
    try {
      authService.logout();
      setUser(null);
      localStorage.removeItem(STORAGE_KEY);
    } finally {
      setIsActionLoading(false);
    }
  };

  const value: AuthContextValue = {
    user,
    isAuthenticated: Boolean(user),
    isInitializing,
    isActionLoading,
    signIn,
    signUp,
    signOutUser,
  };

  return React.createElement(AuthContext.Provider, { value }, children);
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
