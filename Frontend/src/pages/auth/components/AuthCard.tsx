import { useState, useEffect } from "react";
import {
  LogIn,
  UserPlus,
  Mail,
  Lock,
  User,
  Loader2,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

export type AuthMode = "login" | "register";

type AuthCardProps = {
  initialMode?: AuthMode;
  allowModeToggle?: boolean;
  redirectPath?: string;
};

const errorMessages: Record<string, string> = {
  "auth/invalid-credential": "The email or password you entered is incorrect.",
  "auth/user-disabled":
    "This account has been disabled. Contact support for assistance.",
  "auth/user-not-found": "No account found. Try registering instead.",
  "auth/wrong-password": "Incorrect password. Please try again.",
  "auth/email-already-in-use":
    "This email is already registered. Try logging in instead.",
  "auth/weak-password": "Password should be at least 6 characters.",
  default: "Something went wrong. Please try again.",
};

const getErrorMessage = (error: unknown) => {
  if (error && typeof error === "object" && "code" in error) {
    const code = String(error.code);
    return errorMessages[code] ?? errorMessages.default;
  }
  if (error instanceof Error) return error.message;
  return errorMessages.default;
};

export const AuthCard = ({
  initialMode = "login",
  allowModeToggle = true,
  redirectPath = "/",
}: AuthCardProps) => {
  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { signIn, signUp, isActionLoading, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    setMode(initialMode);
    setError(null);
  }, [initialMode]);

  const toggleMode = () => {
    if (!allowModeToggle) return;
    setMode((prev) => (prev === "login" ? "register" : "login"));
    setError(null);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      setError(null);
      if (mode === "login") {
        await signIn(email, password);
      } else {
        await signUp(name, email, password, phoneNumber);
      }
      navigate(redirectPath);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  // ⭐ Auto-fill demo
  const autoFillDemo = () => {
    setEmail("anhnon0106@gmail.com");
    setPassword("123456");
  };

  const primaryActionLabel = mode === "login" ? "Login" : "Create account";
  const secondaryActionLabel =
    mode === "login"
      ? "Need an account? Register"
      : "Already have an account? Login";

  return (
    <div className="p-10 border shadow-2xl rounded-3xl border-white/10 bg-white/5 shadow-naver-green/20 backdrop-blur">
      <div className="flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.35em] text-naver-green">
        <span className="inline-flex items-center justify-center w-10 h-10 rounded-2xl bg-linear-to-br from-naver-green to-emerald-500 text-gray-950">
          {mode === "login" ? (
            <LogIn className="w-5 h-5" />
          ) : (
            <UserPlus className="w-5 h-5" />
          )}
        </span>
        {mode === "login" ? "Welcome back" : "Create your account"}
      </div>

      <h2 className="mt-6 text-3xl font-semibold text-white">
        {mode === "login" ? "Sign in to continue" : "Join NavNexus today"}
      </h2>
      <p className="mt-2 text-sm text-gray-400">
        {mode === "login"
          ? "Access your knowledge graphs and collaborate with your team."
          : "Unlock AI-assisted synthesis and build interactive knowledge graphs."}
      </p>

      <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
        {mode === "register" && (
          <>
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

            <label className="block text-sm text-gray-300">
              <span className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.3em] text-gray-400">
                <User className="w-4 h-4" />
                Phone number
              </span>
              <input
                className="w-full px-4 py-3 text-sm text-white border rounded-xl border-white/10 bg-white/5 placeholder:text-gray-500 focus:border-naver-green focus:outline-none focus:ring-2 focus:ring-naver-green/30"
                placeholder="+1 234 567 8900"
                type="tel"
                value={phoneNumber}
                onChange={(event) => setPhoneNumber(event.target.value)}
                required
              />
            </label>
          </>
        )}

        {/* Email */}
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

        {/* Password */}
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
      {/* ⭐ NOTE DEMO ACCOUNT */}
{mode === "login" && (
  <div className="mt-6 p-4 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 relative overflow-hidden">
    {/* subtle NAVER green glow */}
    <div className="absolute inset-0 bg-gradient-to-br from-[#03C75A]/20 via-transparent to-transparent opacity-20 pointer-events-none" />

    <div className="relative z-10 space-y-3">
      {/* Title + short description */}
      <div className="flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-[#03C75A]" />
        <p className="text-sm text-gray-200 font-medium">
          Want to try NavNexus instantly? Use the demo account below.
        </p>
      </div>

      {/* Auto-fill button */}
      <button
        type="button"
        onClick={autoFillDemo}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5
                   text-sm font-semibold rounded-xl
                   bg-gradient-to-r from-[#03C75A]/20 via-[#25D97E]/25 to-[#07A151]/20
                   text-[#03C75A] shadow-[0_0_10px_#03C75A40]
                   hover:from-[#03C75A]/30 hover:via-[#25D97E]/50 hover:to-[#07A151]/30
                   active:scale-[0.97] transition-all backdrop-blur-md"
      >
        <Sparkles className="w-4 h-4" />
        Auto-fill Demo Account
      </button>
    </div>
  </div>
)}



      {/* Toggle Login/Register */}
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
          You are already signed in.{" "}
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
