'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { BharatBuyLogo } from '../../components/BharatBuyLogo';
import { useAuth } from '../../lib/auth-context';
import { Eye, EyeOff, Lock, Mail, AlertCircle, Loader2, ArrowRight } from 'lucide-react';

export default function SignInPage() {
  const router = useRouter();
  const { signIn, signInWithGoogle, isConfigured } = useAuth();

  // Controlled form state — strictly starts EMPTY
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [rememberMe, setRememberMe] = useState<boolean>(false);
  const [showPassword, setShowPassword] = useState<boolean>(false);

  // Status & Validation
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setErrorMessage('Work email is required.');
      return;
    }

    if (!password) {
      setErrorMessage('Password is required.');
      return;
    }

    setIsLoading(true);
    try {
      await signIn({
        email: cleanEmail,
        password,
        remember_me: rememberMe
      });
      router.push('/');
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || '';
      if (typeof detail === 'string' && !detail.toLowerCase().includes('status code') && !detail.toLowerCase().includes('network error')) {
        setErrorMessage(detail);
      } else if (err.response?.status === 401 || err.response?.status === 403) {
        setErrorMessage('Invalid work email or password. Please verify your credentials.');
      } else if (Array.isArray(detail) && detail.length > 0) {
        setErrorMessage(detail[0].msg || 'Invalid credentials.');
      } else {
        setErrorMessage('Unable to sign in. Please verify your credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setErrorMessage(null);
    setIsGoogleLoading(true);
    try {
      await signInWithGoogle();
      router.push('/');
    } catch (err: any) {
      setErrorMessage(err.message || 'Google Sign-In failed. Please try again.');
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Main Card */}
        <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT shadow-md p-6 sm:p-8">
          {/* Header */}
          <div className="flex flex-col items-center text-center mb-6">
            <div className="mb-3">
              <BharatBuyLogo size={42} />
            </div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-on-surface">
                Sign in to BharatBuy
              </h1>
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-DEFAULT bg-surface-container text-on-surface font-mono text-[10px] uppercase tracking-wider border border-surface-container-high">
                PROD
              </span>
            </div>
            <p className="text-xs text-secondary max-w-xs leading-relaxed">
              Statutory intelligence, BIS compliance, and evidence-backed procurement workbench.
            </p>
          </div>

          {/* Development Configuration Notice (Non-crashing fallback) */}
          {!isConfigured && (
            <div
              role="status"
              className="mb-5 p-3 rounded-DEFAULT bg-amber-50 border border-amber-200 flex items-start gap-2.5 text-xs text-amber-900"
            >
              <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block mb-0.5">Development Notice</span>
                <span>Firebase Authentication is not configured in local environment. Direct backend authentication will be attempted.</span>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {errorMessage && (
            <div
              role="alert"
              className="mb-5 p-3 rounded-DEFAULT bg-rose-50 border border-rose-200 flex items-start gap-2.5 text-xs text-rose-800"
            >
              <AlertCircle className="w-4 h-4 text-error flex-shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Sign In Form */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Work Email */}
            <div>
              <label
                htmlFor="signin-email"
                className="block text-xs font-semibold text-on-surface-variant mb-1.5 font-mono uppercase tracking-wider"
              >
                Work Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-secondary">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="signin-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.in"
                  className="w-full pl-9 pr-3 py-2 bg-surface-container-low border border-outline-variant rounded-DEFAULT text-sm text-on-surface placeholder-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-colors font-sans"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="signin-password"
                  className="block text-xs font-semibold text-on-surface-variant font-mono uppercase tracking-wider"
                >
                  Password
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-secondary">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="signin-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-9 pr-10 py-2 bg-surface-container-low border border-outline-variant rounded-DEFAULT text-sm text-on-surface placeholder-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-colors font-sans"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-secondary hover:text-on-surface transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between pt-1">
              <label htmlFor="signin-remember" className="flex items-center cursor-pointer select-none">
                <input
                  id="signin-remember"
                  name="remember_me"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded-DEFAULT border-outline-variant text-primary focus:ring-0 accent-primary"
                />
                <span className="ml-2 text-xs text-secondary">Remember session (30 days)</span>
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || isGoogleLoading}
              className="w-full mt-2 py-2.5 px-4 bg-primary hover:bg-primary-container text-on-primary font-medium rounded-DEFAULT text-sm transition-colors flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed font-mono"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-on-primary" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            {/* Visual Divider */}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-surface-container-high" />
              </div>
              <div className="relative flex justify-center text-xs uppercase font-mono">
                <span className="bg-surface-container-lowest px-2 text-secondary">
                  or
                </span>
              </div>
            </div>

            {/* Continue with Google Button */}
            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={isLoading || isGoogleLoading}
              className="w-full py-2.5 px-4 bg-surface-container-low hover:bg-surface-container text-on-surface font-medium rounded-DEFAULT text-sm transition-colors flex items-center justify-center gap-2.5 border border-outline-variant shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGoogleLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  <span>Connecting to Google...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.26v3.15C3.25 21.36 7.31 24 12 24z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.26C.46 8.16 0 9.97 0 12s.46 3.84 1.26 5.42l4.02-3.15z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.64 1.26 6.58l4.02 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                    />
                  </svg>
                  <span>Continue with Google</span>
                </>
              )}
            </button>
          </form>

          {/* Footer Link */}
          <div className="mt-6 pt-5 border-t border-surface-container-high text-center">
            <p className="text-xs text-secondary">
              New to BharatBuy?{' '}
              <Link
                href="/signup"
                className="font-medium text-primary hover:text-primary-container transition-colors underline-offset-4 hover:underline"
              >
                Create an account
              </Link>
            </p>
          </div>
        </div>

        {/* Security & Statutory Notice */}
        <div className="mt-4 text-center">
          <p className="text-[11px] text-secondary font-mono">
            Secured by Firebase Authentication &bull; SIH26108
          </p>
        </div>
      </div>
    </div>
  );
}
