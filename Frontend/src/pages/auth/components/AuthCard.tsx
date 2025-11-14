import { useState, useEffect } from 'react';
import {
  LogIn,
  UserPlus,
  Mail,
  Lock,
  User,
  Loader2,
  ArrowRight,

} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { ChromeIcon } from 'lucide-react';

export type AuthMode = 'login' | 'register';

type AuthCardProps = {
  initialMode?: AuthMode;
  allowModeToggle?: boolean;
  redirectPath?: string;
};

const errorMessages: Record<string, string> = {
  'auth/invalid-credential': 'The email or password you entered is incorrect.',
  'auth/user-disabled': 'This account has been disabled. Contact support for assistance.',
  'auth/user-not-found': 'No account found. Try registering instead.',
  'auth/wrong-password': 'Incorrect password. Please try again.',
  'auth/email-already-in-use': 'This email is already registered. Try logging in instead.',
  'auth/weak-password': 'Password should be at least 6 characters.',
  default: 'Something went wrong. Please try again.',
};

const getErrorMessage = (error: unknown) => {
  if (error && typeof error === 'object' && 'code' in error) {
    const code = String(error.code);
    return errorMessages[code] ?? errorMessages.default;
  }
  if (error instanceof Error) return error.message;
  return errorMessages.default;
};

export const AuthCard = ({
  initialMode = 'login',
  allowModeToggle = true,
  redirectPath = '/workspace/demo',
}: AuthCardProps) => {
  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const { signIn, signUp, isActionLoading, isAuthenticated,signInWithGoogle,logOut } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    setMode(initialMode);
    setError(null);
  }, [initialMode]);

  const toggleMode = () => {
    if (!allowModeToggle) return;
    setMode((prev) => (prev === 'login' ? 'register' : 'login'));
    setError(null);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      setError(null);
      if (mode === 'login') {
        await signIn(email, password);
      } else {
        await signUp(name, email, password);
      }
      navigate(redirectPath);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };


  const primaryActionLabel = mode === 'login' ? 'Login' : 'Create account';
  const secondaryActionLabel =
    mode === 'login' ? 'Need an account? Register' : 'Already have an account? Login';

  return (
    <div className="p-10 border shadow-2xl rounded-3xl border-white/10 bg-white/5 shadow-naver-green/20 backdrop-blur">
      <div className="flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.35em] text-naver-green">
        <span className="inline-flex items-center justify-center w-10 h-10 rounded-2xl bg-linear-to-br from-naver-green to-emerald-500 text-gray-950">
          {mode === 'login' ? <LogIn className="w-5 h-5" /> : <UserPlus className="w-5 h-5" />}
        </span>
        {mode === 'login' ? 'Welcome back' : 'Create your account'}
      </div>

      <h2 className="mt-6 text-3xl font-semibold text-white">
        {mode === 'login' ? 'Sign in to continue' : 'Join NavNexus today'}
      </h2>
      <p className="mt-2 text-sm text-gray-400">
        {mode === 'login'
          ? 'Access your knowledge graphs and collaborate with your team.'
          : 'Unlock AI-assisted synthesis and build interactive knowledge graphs.'}
      </p>

      <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
        {mode === 'register' && (
          <label className="block text-sm text-gray-300">
            <span className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.3em] text-gray-400">
              <User className="w-4 h-4" />
              Full name
            </span>
            <input
              className="w-full px-4 py-3 text-sm text-white border rounded-xl border-white/10 bg-white/5 placeholder:text-gray-500 focus:border-naver-green focus:outline-none focus:ring-2 focus:ring-naver-green/30"
              placeholder="Jane Doe"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </label>
        )}

        <label className="block text-sm text-gray-300">
          <span className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.3em] text-gray-400">
            <Mail className="w-4 h-4" />
            Email
          </span>
          <input
            className="w-full px-4 py-3 text-sm text-white border rounded-xl border-white/10 bg-white/5 placeholder:text-gray-500 focus:border-naver-green focus:outline-none focus:ring-2 focus:ring-naver-green/30"
            placeholder="you@example.com"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label className="block text-sm text-gray-300">
          <span className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.3em] text-gray-400">
            <Lock className="w-4 h-4" />
            Password
          </span>
          <input
            className="w-full px-4 py-3 text-sm text-white border rounded-xl border-white/10 bg-white/5 placeholder:text-gray-500 focus:border-naver-green focus:outline-none focus:ring-2 focus:ring-naver-green/30"
            placeholder="Enter your password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        {error && (
          <p className="px-4 py-2 text-xs border rounded-xl border-rose-500/30 bg-rose-500/10 text-rose-200">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isActionLoading}
          className="inline-flex items-center justify-center w-full gap-2 px-5 py-3 text-sm font-semibold transition rounded-full shadow-lg bg-linear-to-r from-naver-green via-emerald-400 to-emerald-600 text-gray-950 shadow-naver-green/40 hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isActionLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              {primaryActionLabel}
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/10" />
        </div>
        <div className="relative flex justify-center">
          <span className="px-3 text-xs text-gray-400 bg-gray-900">
            Or continue with
          </span>
        </div>
      </div>

      {/* Google Login */}
      <button
        type="button"
        onClick={()=>{signInWithGoogle()}}
        className="inline-flex items-center justify-center w-full gap-3 px-5 py-3 text-sm font-semibold text-white transition border rounded-full border-white/10 bg-white/10 hover:bg-white/20"
      >
        <ChromeIcon className="w-5 h-5 text-naver-green" />
        <h1 className="text-sm font-semibold">Continue with Google</h1>
      </button>

      {allowModeToggle && (
        <button
          type="button"
          onClick={toggleMode}
          className="block w-full mt-8 text-sm font-medium text-center transition text-naver-green hover:text-white"
        >
          {secondaryActionLabel}
        </button>
      )}

      {isAuthenticated && (
        <p className="mt-4 text-xs text-center text-gray-500">
          You are already signed in.{' '}
          <button
            type="button"
            onClick={() => navigate(redirectPath)}
            className="text-naver-green underline-offset-4 hover:underline"
          >
            Go to your workspace.
          </button>
        </p>
      )}
    </div>
  );
};
