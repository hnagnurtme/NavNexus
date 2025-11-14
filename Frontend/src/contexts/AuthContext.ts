import { auth, googleProvider } from '@/config/firebase';
import { signInWithPopup, signOut } from 'firebase/auth';
import React, { createContext, useContext, useEffect, useState, type PropsWithChildren } from 'react';

type StoredAccount = { email: string; name: string; password: string; };
export type AuthUser = { id: string; name: string; email: string; };

type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  isActionLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (name: string, email: string, password: string) => Promise<void>;
  signOutUser: () => Promise<void>;
  signInWithGoogle: () => Promise<void>;
};

const STORAGE_KEY = 'navnexus.auth.user';
const ACCOUNTS_KEY = 'navnexus.auth.accounts';

const readJson = <T,>(key: string): T | null => {
  if (typeof window === 'undefined') return null;
  try { return JSON.parse(localStorage.getItem(key) || 'null') as T; } 
  catch { localStorage.removeItem(key); return null; }
};
const writeJson = (key: string, value: unknown) => { if (typeof window !== 'undefined') localStorage.setItem(key, JSON.stringify(value)); };

export const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider = ({ children }: PropsWithChildren<{}>) => {
  const [user, setUser] = useState<AuthUser | null>(() => readJson<AuthUser>(STORAGE_KEY));
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => { setIsInitializing(false); }, []);

  const signIn = async (email: string, password: string) => {
    setIsActionLoading(true);
    try {
      const accounts = readJson<StoredAccount[]>(ACCOUNTS_KEY) || [];
      const match = accounts.find(a => a.email === email.trim().toLowerCase());
      if (!match || match.password !== password) throw new Error('Invalid credentials');
      const nextUser: AuthUser = { id: match.email, email: match.email, name: match.name };
      setUser(nextUser);
      writeJson(STORAGE_KEY, nextUser);
    } finally { setIsActionLoading(false); }
  };

  const signUp = async (name: string, email: string, password: string) => {
    setIsActionLoading(true);
    try {
      if (password.length < 6) throw new Error('Password should be at least 6 characters');
      const trimmedEmail = email.trim().toLowerCase();
      const trimmedName = name.trim();
      const accounts = readJson<StoredAccount[]>(ACCOUNTS_KEY) || [];
      if (accounts.some(a => a.email === trimmedEmail)) throw new Error('Email already in use');

      const newAccount: StoredAccount = { email: trimmedEmail, name: trimmedName || trimmedEmail.split('@')[0], password };
      writeJson(ACCOUNTS_KEY, [...accounts, newAccount]);

      const nextUser: AuthUser = { id: trimmedEmail, email: trimmedEmail, name: newAccount.name };
      setUser(nextUser);
      writeJson(STORAGE_KEY, nextUser);
    } finally { setIsActionLoading(false); }
  };

  const signOutUser = async () => {
    setIsActionLoading(true);
    try {
      await signOut(auth);
      setUser(null);
      localStorage.removeItem(STORAGE_KEY);
    } finally {
      setIsActionLoading(false);
    }
  };

  const signInWithGoogle = async () => {
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const gUser = result.user;
      const nextUser: AuthUser = { id: gUser.uid, email: gUser.email || '', name: gUser.displayName || 'GoogleUser' };
      setUser(nextUser);
      writeJson(STORAGE_KEY, nextUser);
    } catch (error) { console.error('Google Sign-In Error:', error); }
  };

  const value: AuthContextValue = {
    user,
    isAuthenticated: Boolean(user),
    isInitializing,
    isActionLoading,
    signIn,
    signUp,
    signOutUser,
    signInWithGoogle,
  };

  return React.createElement(AuthContext.Provider, { value }, children);
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
