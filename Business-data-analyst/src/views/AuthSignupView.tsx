import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Sparkles, Lock, Mail, User, Building, ArrowRight, AlertTriangle, Zap, CheckCircle2 } from 'lucide-react';

export const AuthSignupView: React.FC = () => {
  const { signUp, setCurrentRoute, showToast } = useApp();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isRateLimit, setIsRateLimit] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !name) return;
    try {
      setIsLoading(true);
      setErrorMessage(null);
      setIsRateLimit(false);
      await signUp(name.trim(), email.trim(), password || undefined, company.trim());
    } catch (err: any) {
      const msg = err.message || 'Registration could not be completed.';
      setErrorMessage(msg);
      if (msg.toLowerCase().includes('rate limit') || msg.toLowerCase().includes('429')) {
        setIsRateLimit(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickWorkspaceAccess = async () => {
    try {
      setIsLoading(true);
      await signUp(name.trim() || 'Lead Analyst', email.trim() || 'analyst@domain.com', undefined, company.trim() || 'Enterprise Analytics');
      showToast('success', 'Instant Workspace Activated', 'Bypassed SMTP limit into workspace session.');
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
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-sky-500 shadow-lg shadow-indigo-500/25 mb-3">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            Create Analyst Account
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Start profiling schemas and generating automated intelligence
          </p>
        </div>

        {/* Rate Limit Notice & Instant Bypass Option */}
        {isRateLimit && (
          <div className="mb-5 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/25 space-y-2.5 text-xs text-amber-200">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-amber-200">
                  Supabase Email Rate Limit Exceeded
                </p>
                <p className="text-[11px] text-amber-300/80 mt-0.5 leading-relaxed">
                  Supabase's default free-tier SMTP limits confirmation emails to 3-4 per hour. You don't need to wait — continue immediately in instant workspace mode!
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleQuickWorkspaceAccess}
              className="w-full py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 rounded-xl font-bold text-xs shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Continue in Instant Workspace Mode</span>
            </button>
          </div>
        )}

        {errorMessage && !isRateLimit && (
          <div className="p-3 mb-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-300">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Full Name
            </label>
            <div className="relative">
              <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Dr. Jordan Hayes"
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:bg-white/[0.07]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Work Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jordan@company.com"
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:bg-white/[0.07]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Organization / Company
            </label>
            <div className="relative">
              <Building className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="Global Health Analytics"
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:bg-white/[0.07]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:bg-white/[0.07]"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer mt-2"
          >
            <span>{isLoading ? 'Creating Account...' : 'Get Started Free'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={handleQuickWorkspaceAccess}
            disabled={isLoading}
            className="w-full py-2.5 bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 rounded-xl text-xs font-medium transition-colors flex items-center justify-center gap-2 cursor-pointer"
          >
            <Zap className="w-3.5 h-3.5 text-indigo-400" />
            <span>Instant Workspace Access (No Email Wait)</span>
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-white/10 text-center text-xs text-slate-400">
          Already have an account?{' '}
          <button
            onClick={() => setCurrentRoute('/login')}
            className="font-semibold text-indigo-400 hover:text-indigo-300 cursor-pointer"
          >
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
};
