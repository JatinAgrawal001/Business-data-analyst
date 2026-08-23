import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Sparkles, Lock, Mail, ArrowRight, ShieldCheck, Zap, AlertTriangle } from 'lucide-react';

export const AuthLoginView: React.FC = () => {
  const { login, setCurrentRoute, showToast } = useApp();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isRateLimit, setIsRateLimit] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    try {
      setIsLoading(true);
      setErrorMessage(null);
      setIsRateLimit(false);
      await login(email.trim(), password || undefined);
    } catch (err: any) {
      const msg = err.message || 'Invalid email or password. Please verify your credentials.';
      setErrorMessage(msg);
      if (msg.toLowerCase().includes('rate limit') || msg.toLowerCase().includes('429')) {
        setIsRateLimit(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      await login('analyst@insightflow.io', undefined);
      showToast('success', 'Workspace Activated', 'Logged in as Senior Quantitative Analyst.');
    } catch (err: any) {
      setErrorMessage(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0B10] flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md backdrop-blur-2xl bg-white/[0.04] border border-white/10 rounded-3xl p-8 shadow-2xl">
        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-sky-500 shadow-lg shadow-indigo-500/25 mb-3">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            Welcome to InsightFlow
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Sign in to access your autonomous data analytics workspace
          </p>
        </div>

        {/* Rate limit warning */}
        {isRateLimit && (
          <div className="mb-5 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/25 space-y-2.5 text-xs text-amber-200">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-amber-200">
                  Supabase Email Rate Limit Notice
                </p>
                <p className="text-[11px] text-amber-300/80 mt-0.5 leading-relaxed">
                  Supabase default SMTP server limits emails to 3-4 per hour. Click below to continue directly into your workspace.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleDemoLogin}
              className="w-full py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 rounded-xl font-bold text-xs shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Instant Workspace Login</span>
            </button>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {errorMessage && !isRateLimit && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-300">
              {errorMessage}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Work Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@domain.com"
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:bg-white/[0.07]"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300">Password</label>
              <button
                type="button"
                onClick={() => setCurrentRoute('/forgot-password')}
                className="text-[11px] text-indigo-400 hover:text-indigo-300 cursor-pointer"
              >
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:bg-white/[0.07]"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer mt-2"
          >
            <span>{isLoading ? 'Authenticating...' : 'Sign In to Workspace'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={isLoading}
            className="w-full py-2.5 bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 rounded-xl text-xs font-medium transition-colors flex items-center justify-center gap-2 cursor-pointer"
          >
            <Zap className="w-3.5 h-3.5 text-indigo-400" />
            <span>Sign In with Demo Analyst Profile</span>
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-white/10 text-center text-xs text-slate-400">
          Don't have an account?{' '}
          <button
            onClick={() => setCurrentRoute('/signup')}
            className="font-semibold text-indigo-400 hover:text-indigo-300 cursor-pointer"
          >
            Create an Account
          </button>
        </div>
      </div>
    </div>
  );
};
