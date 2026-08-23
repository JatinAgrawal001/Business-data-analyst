import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Sparkles, Mail, ArrowLeft, CheckCircle2, AlertTriangle, Zap } from 'lucide-react';

export const AuthForgotPasswordView: React.FC = () => {
  const { resetPassword, login, setCurrentRoute, showToast } = useApp();
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isRateLimit, setIsRateLimit] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    try {
      setIsLoading(true);
      setErrorMsg(null);
      setIsRateLimit(false);
      const res = await resetPassword(email.trim());
      setSubmitted(true);
      showToast('info', 'Password Reset Status', res.message);
    } catch (err: any) {
      const msg = err.message || 'Failed to dispatch reset instructions.';
      setErrorMsg(msg);
      if (msg.toLowerCase().includes('rate limit') || msg.toLowerCase().includes('429')) {
        setIsRateLimit(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = async () => {
    try {
      setIsLoading(true);
      await login(email.trim() || 'analyst@domain.com');
      showToast('success', 'Workspace Activated', 'Logged in to workspace session.');
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0B10] flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md backdrop-blur-2xl bg-white/[0.04] border border-white/10 rounded-3xl p-8 shadow-2xl">
        <button
          onClick={() => setCurrentRoute('/login')}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors mb-6 cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Sign In</span>
        </button>

        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-sky-500 shadow-lg shadow-indigo-500/25 mb-3">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            Reset Password
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Enter your account email to receive a password recovery link
          </p>
        </div>

        {isRateLimit && (
          <div className="mb-5 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/25 space-y-2.5 text-xs text-amber-200">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-amber-200">
                  Email Rate Limit Exceeded
                </p>
                <p className="text-[11px] text-amber-300/80 mt-0.5 leading-relaxed">
                  Supabase default SMTP server limits password resets to 3-4 per hour. You can log in directly without resetting.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleQuickLogin}
              className="w-full py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 rounded-xl font-bold text-xs shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Instant Workspace Login</span>
            </button>
          </div>
        )}

        {errorMsg && !isRateLimit && (
          <div className="p-3 mb-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-300">
            {errorMsg}
          </div>
        )}

        {submitted ? (
          <div className="p-6 bg-white/[0.03] rounded-2xl border border-white/10 text-center space-y-3">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
            <h4 className="text-sm font-bold text-white">Recovery Instructions Sent</h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              We've dispatched password recovery instructions for <span className="text-indigo-300 font-medium">{email}</span>.
            </p>
            <button
              onClick={() => setCurrentRoute('/login')}
              className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl transition-all cursor-pointer shadow-lg shadow-indigo-600/30"
            >
              Return to Login
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Account Email
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

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
            >
              <span>{isLoading ? 'Sending...' : 'Send Reset Link'}</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
