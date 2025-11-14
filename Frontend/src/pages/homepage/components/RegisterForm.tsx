import { useState } from 'react';
import { Lock, Mail, UserPlus, User } from 'lucide-react';

type RegisterFormValues = {
  name: string;
  email: string;
  password: string;
  phoneNumber: string;
  confirmPassword: string;
};

type RegisterFormProps = {
  onSubmit: (values: Omit<RegisterFormValues, 'confirmPassword'>) => Promise<void>;
  isLoading: boolean;
  switchToLogin: () => void;
};

export const RegisterForm: React.FC<RegisterFormProps> = ({
  onSubmit,
  isLoading,
  switchToLogin,
}) => {
  const [values, setValues] = useState<RegisterFormValues>({
    name: '',
    email: '',
    password: '',
    phoneNumber: '',
    confirmPassword: '',
  });
  const [error, setError] = useState<string | null>(null);

  const updateValue = (field: keyof RegisterFormValues, newValue: string) => {
    setValues((current) => ({
      ...current,
      [field]: newValue,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (values.password !== values.confirmPassword) {
      setError('Passwords do not match. Please try again.');
      return;
    }

    try {
      await onSubmit({
        name: values.name,
        email: values.email,
        password: values.password,
        phoneNumber: values.phoneNumber,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create account right now.');
    }
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="flex items-center justify-between">
        <h4 className="text-xl font-semibold text-white">Create your account</h4>
        <button
          type="button"
          onClick={switchToLogin}
          className="text-xs font-semibold uppercase tracking-[0.3em] text-cyber-blue transition hover:text-white"
        >
          Login
        </button>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-[0.3em] text-gray-400">
          Full name
        </label>
        <input
          type="text"
          required
          placeholder="Jane Doe"
          className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-gray-500 focus:border-cyber-blue focus:outline-none focus:ring-2 focus:ring-cyber-blue/30"
          value={values.name}
          onChange={(event) => updateValue('name', event.target.value)}
        />
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
          Phone Number
        </label>
        <div className="relative">
          <User className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-cyber-blue" />
          <input
            type="tel"
            required
            placeholder="+1 234 567 8900"
            className="w-full rounded-xl border border-white/10 bg-white/5 px-12 py-3 text-sm text-white placeholder:text-gray-500 focus:border-cyber-blue focus:outline-none focus:ring-2 focus:ring-cyber-blue/30"
            value={values.phoneNumber}
            onChange={(event) => updateValue('phoneNumber', event.target.value)}
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
            placeholder="Minimum 6 characters"
            className="w-full rounded-xl border border-white/10 bg-white/5 px-12 py-3 text-sm text-white placeholder:text-gray-500 focus:border-cyber-blue focus:outline-none focus:ring-2 focus:ring-cyber-blue/30"
            value={values.password}
            onChange={(event) => updateValue('password', event.target.value)}
            minLength={6}
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-[0.3em] text-gray-400">
          Confirm password
        </label>
        <input
          type="password"
          required
          placeholder="Re-enter your password"
          className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-gray-500 focus:border-cyber-blue focus:outline-none focus:ring-2 focus:ring-cyber-blue/30"
          value={values.confirmPassword}
          onChange={(event) => updateValue('confirmPassword', event.target.value)}
          minLength={6}
        />
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
        <UserPlus className="h-4 w-4" />
        {isLoading ? 'Creating account...' : 'Create account'}
      </button>

      <div className="flex items-center gap-3 text-xs text-gray-500">
        <span className="h-px flex-1 bg-white/10" />
        Coming soon
        <span className="h-px flex-1 bg-white/10" />
      </div>
    </form>
  );
};


