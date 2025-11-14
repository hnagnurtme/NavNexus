import { useMemo, useState } from 'react';
import { ArrowRight, LogOut, RotateCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

type AuthMode = 'login' | 'register';

const getInitials = (name: string) =>
  name
    .split(/\s+/)
    .map((segment) => segment[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

const getAvatarGradient = (seed: string) => {
  const palette = [
    'from-naver-green to-cyber-blue',
    'from-cyber-blue to-purple-500',
    'from-emerald-400 to-naver-green',
    'from-sky-400 to-cyan-500',
    'from-purple-400 to-cyber-blue',
  ];

  const index = seed
    .split('')
    .reduce((acc, char) => acc + char.charCodeAt(0), 0) % palette.length;

  return palette[index];
};

export const AuthPanel: React.FC = () => {
  const [mode, setMode] = useState<AuthMode>('login');
  const navigate = useNavigate();
  const {
    user,
    isAuthenticated,
    isActionLoading,
    signIn,
    signUp,
    signOutUser,
  } = useAuth();

  const handleNavigateWorkspace = () => {
    navigate('/workspace/demo');
  };

  const handleLogout = async () => {
    await signOutUser();
  };

  const avatar = useMemo(() => {
    if (!user) {
      return null;
    }

    return (
      <div
        className={`flex h-12 w-12 items-center justify-center rounded-2xl text-lg font-semibold text-gray-950 bg-linear-to-br ${getAvatarGradient(
          user.email,
        )}`}
      >
        {getInitials(user.name || user.email)}
      </div>
    );
  }, [user]);

  if (isAuthenticated && user) {
    return (
      <div className="flex flex-col gap-6 rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-naver-green/10 backdrop-blur">
        <div className="rounded-2xl bg-gray-950/80 p-6">
          <h3 className="text-lg font-semibold text-white">You’re signed in</h3>
          <p className="mt-2 text-sm text-gray-400">
            Continue exploring your knowledge graphs or switch workspaces.
          </p>

          <div className="mt-6 space-y-4">
            <div className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4">
              {avatar}
              <div>
                <p className="text-sm font-semibold text-white">{user.name}</p>
                <p className="text-xs text-gray-400">{user.email}</p>
              </div>
            </div>

            <button
              onClick={handleNavigateWorkspace}
              className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-linear-to-r from-naver-green to-cyber-blue px-4 py-3 text-sm font-semibold text-gray-950 transition hover:brightness-110"
            >
              <ArrowRight className="h-4 w-4" />
              Go to Demo Workspace
            </button>

            <button
              onClick={handleLogout}
              disabled={isActionLoading}
              className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white transition hover:border-white/30 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isActionLoading ? (
                <RotateCw className="h-4 w-4 animate-spin" />
              ) : (
                <LogOut className="h-4 w-4" />
              )}
              Logout
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-gray-400">
          <h4 className="text-sm font-semibold text-white">Why teams choose NavNexus?</h4>
          <ul className="mt-4 space-y-3">
            <li className="flex gap-3">
              <span className="mt-1 h-2 w-2 rounded-full bg-naver-green" />
              Real-time collaboration across research teams.
            </li>
            <li className="flex gap-3">
              <span className="mt-1 h-2 w-2 rounded-full bg-cyber-blue" />
              AI-assisted synthesis with explainable insights.
            </li>
            <li className="flex gap-3">
              <span className="mt-1 h-2 w-2 rounded-full bg-purple-400" />
              Secure knowledge hubs with granular permissions.
            </li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div
      id="auth-panel"
      className="flex flex-col gap-6 rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-naver-green/10 backdrop-blur"
    >
      <div className="rounded-2xl bg-linear-to-br from-naver-green/20 via-cyber-blue/20 to-transparent p-px">
        <div className="rounded-2xl bg-gray-950/80 p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cyber-blue">
            Secure access
          </p>
          <h3 className="mt-2 text-lg font-semibold text-white">
            {mode === 'login' ? 'Login to continue' : 'Join the knowledge network'}
          </h3>
          <p className="mt-2 text-sm text-gray-400">
            {mode === 'login'
              ? 'Sign in to manage your documents, collaborate, and generate AI-powered knowledge graphs.'
              : 'Create an account to upload documents, build insights, and synthesize interactive knowledge graphs.'}
          </p>

          <div className="mt-6">
            {mode === 'login' ? (
              <LoginForm
                onSubmit={async (values) => {
                  await signIn(values.email, values.password);
                  handleNavigateWorkspace();
                }}
                isLoading={isActionLoading}
                switchToRegister={() => setMode('register')}
              />
            ) : (
              <RegisterForm
                onSubmit={async (values) => {
                  await signUp(values.name, values.email, values.password, values.phoneNumber);
                  handleNavigateWorkspace();
                }}
                isLoading={isActionLoading}
                switchToLogin={() => setMode('login')}
              />
            )}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-gray-400">
        <h4 className="text-sm font-semibold text-white">Why teams choose NavNexus?</h4>
        <ul className="mt-4 space-y-3">
          <li className="flex gap-3">
            <span className="mt-1 h-2 w-2 rounded-full bg-naver-green" />
            Real-time collaboration across research teams.
          </li>
          <li className="flex gap-3">
            <span className="mt-1 h-2 w-2 rounded-full bg-cyber-blue" />
            AI-assisted synthesis with explainable insights.
          </li>
          <li className="flex gap-3">
            <span className="mt-1 h-2 w-2 rounded-full bg-purple-400" />
            Secure knowledge hubs with granular permissions.
          </li>
        </ul>
      </div>
    </div>
  );
};


