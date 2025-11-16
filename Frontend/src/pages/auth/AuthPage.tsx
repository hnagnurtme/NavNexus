import { useMemo } from 'react';
import { Navigate, Link } from 'react-router-dom';
import { ArrowLeft, BookOpen } from 'lucide-react';
import { AuthCard, type AuthMode } from './components/AuthCard';
import { useAuth } from '@/contexts/AuthContext';

type AuthPageProps = {
  initialMode?: AuthMode;
};

export const AuthPage = ({ initialMode = 'login' }: AuthPageProps) => {
  const { isAuthenticated, isInitializing } = useAuth();

  const heroCopy = useMemo(
    () =>
      initialMode === 'login'
        ? {
            title: 'Knowledge Graph Synthesizer',
            subtitle:
              'Manage documents, explore AI insights, and generate interactive knowledge graphs that keep your research synchronized.',
            bullets: [
              'Bring together structured and unstructured knowledge with AI assistance.',
              'Collaborate with teammates in real time and annotate shared graphs.',
              'Export insights across your favourite productivity tools.',
            ],
            cta: {
              label: 'Need an account? Register',
              href: '/register',
            },
          }
        : {
            title: 'Begin your knowledge journey',
            subtitle:
              'Set up your workspace, invite teammates, and turn research artifacts into living knowledge graphs.',
            bullets: [
              'AI summaries, evidence extraction, and synthesis in one place.',
              'Securely manage access with workspace-level permissions.',
              'Export visual graphs and share insights instantly.',
            ],
            cta: {
              label: 'Already have an account? Login',
              href: '/login',
            },
          },
    [initialMode],
  );

  if (!isInitializing && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-linear-to-br from-gray-950 via-slate-950 to-gray-900 text-white">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-12 px-6 py-10 lg:flex-row lg:items-center">
        <section className="flex-1 space-y-8">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm font-medium text-gray-400 transition hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to homepage
          </Link>

          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-3xl bg-linear-to-br from-naver-green to-cyber-blue shadow-lg shadow-cyber-blue/30">
              <BookOpen className="h-7 w-7 text-white" />
            </div>
            <div>
              <p className="text-base font-semibold uppercase tracking-[0.35em] text-cyber-blue">
                NavNexus
              </p>
              <h1 className="text-3xl font-semibold text-white">{heroCopy.title}</h1>
            </div>
          </div>

          <div className="space-y-6 text-gray-300">
            <p className="text-lg">{heroCopy.subtitle}</p>
            <ul className="space-y-3 text-sm">
              {heroCopy.bullets.map((entry) => (
                <li key={entry} className="flex items-center gap-3">
                  <span className="h-2 w-2 rounded-full bg-naver-green" />
                  {entry}
                </li>
              ))}
            </ul>
          </div>

          <Link
            to={heroCopy.cta.href}
            className="inline-flex w-max items-center gap-2 text-sm font-medium text-cyber-blue transition hover:text-white"
          >
            {heroCopy.cta.label}
          </Link>
        </section>

        <section className="flex-1">
          <AuthCard initialMode={initialMode} />
        </section>
      </div>
    </div>
  );
};


