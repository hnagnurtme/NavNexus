import { useState } from 'react';
import { Lock, LogIn, Mail } from 'lucide-react';

type LoginFormValues = {
  email: string;
  password: string;
};

type LoginFormProps = {
  onSubmit: (values: LoginFormValues) => Promise<void>;
  isLoading: boolean;
  switchToRegister: () => void;
};

export const LoginForm: React.FC<LoginFormProps> = ({
  onSubmit,
  isLoading,
  switchToRegister,
}) => {
  const [values, setValues] = useState<LoginFormValues>({ email: '', password: '' });
  const [error, setError] = useState<string | null>(null);

  const updateValue = (field: keyof LoginFormValues, newValue: string) => {
    setValues((current) => ({
      ...current,
      [field]: newValue,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    try {
      await onSubmit(values);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in. Please try again.');
    }
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="flex items-center justify-between">
        <h4 className="text-xl font-semibold text-white">Welcome back</h4>
        <button
          type="button"
          onClick={switchToRegister}
          className="text-xs font-semibold uppercase tracking-[0.3em] text-cyber-blue transition hover:text-white"
        >
          Register
        </button>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-[0.3em] text-gray-400">
          Email
        </label>
        <div className="relative">
          <Mail className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-cyber-blue" />
          <input
            type="email"
            required
            placeholder="you@example.com"
            className="w-full rounded-xl border border-white/10 bg-white/5 px-12 py-3 text-sm text-white placeholder:text-gray-500 focus:border-cyber-blue focus:outline-none focus:ring-2 focus:ring-cyber-blue/30"
            value={values.email}
            onChange={(event) => updateValue('email', event.target.value)}
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-[0.3em] text-gray-400">
          Password
        </label>
        <div className="relative">
          <Lock className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-cyber-blue" />
          <input
            type="password"
            required
            placeholder="Enter your password"
            className="w-full rounded-xl border border-white/10 bg-white/5 px-12 py-3 text-sm text-white placeholder:text-gray-500 focus:border-cyber-blue focus:outline-none focus:ring-2 focus:ring-cyber-blue/30"
            value={values.password}
            onChange={(event) => updateValue('password', event.target.value)}
          />
        </div>
      </div>

      {error && (
        <p className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-linear-to-r from-naver-green to-cyber-blue px-4 py-3 text-sm font-semibold text-gray-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
      >
        <LogIn className="h-4 w-4" />
        {isLoading ? 'Signing in...' : 'Sign in with email'}
      </button>

      <p className="text-center text-xs text-gray-500">
        Single sign-on providers are coming soon.
      </p>
    </form>
  );
};