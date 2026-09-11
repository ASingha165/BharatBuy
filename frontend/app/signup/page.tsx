'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { BharatBuyLogo } from '../../components/BharatBuyLogo';
import { useAuth } from '../../lib/auth-context';
import { Eye, EyeOff, Lock, Mail, User, Building2, AlertCircle, Loader2, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function SignUpPage() {
  const router = useRouter();
  const { signUp, isConfigured } = useAuth();

  // Controlled form state — strictly starts EMPTY
  const [name, setName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [organization, setOrganization] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [termsAccepted, setTermsAccepted] = useState<boolean>(false);

  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState<boolean>(false);

  // Status & Validation
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // Client-side validations
    if (!name.trim()) {
      setErrorMessage('Full name is required.');
      return;
    }

    if (!email.trim()) {
      setErrorMessage('Work email is required.');
      return;
    }

    if (!organization.trim()) {
      setErrorMessage('Organization or startup name is required.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    if (!termsAccepted) {
      setErrorMessage('You must consent to statutory procurement governance terms.');
      return;
    }

    setIsLoading(true);
    try {
      await signUp({
        name: name.trim(),
        email: email.trim(),
        organization: organization.trim(),
        password,
        confirm_password: confirmPassword,
        terms_accepted: termsAccepted
      });
      router.push('/');
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || '';
      if (typeof detail === 'string' && !detail.toLowerCase().includes('status code') && !detail.toLowerCase().includes('network error')) {
        setErrorMessage(detail);
      } else if (err.response?.status === 409) {
        setErrorMessage('An account with this work email already exists.');
      } else if (Array.isArray(detail) && detail.length > 0) {
        setErrorMessage(detail[0].msg || 'Registration failed. Please check form fields.');
      } else {
        setErrorMessage('Unable to create account. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Main Card */}
        <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT shadow-md p-6 sm:p-8">
          {/* Header */}
          <div className="flex flex-col items-center text-center mb-6">
            <div className="mb-3">
              <BharatBuyLogo size={42} />
            </div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-on-surface">
                Create BharatBuy Account
              </h1>
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-DEFAULT bg-surface-container text-on-surface font-mono text-[10px] uppercase tracking-wider border border-surface-container-high">
                PROD
              </span>
            </div>
            <p className="text-xs text-secondary max-w-sm leading-relaxed">
              Statutory intelligence, BIS compliance, and verified sourcing for enterprise buyers.
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
                <span>Firebase Authentication is not configured in local environment. Direct backend registration will be attempted.</span>
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

          {/* Sign Up Form */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Full Name */}
            <div>
              <label
                htmlFor="signup-name"
                className="block text-xs font-semibold text-on-surface-variant mb-1.5 font-mono uppercase tracking-wider"
              >
                Full Name
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-secondary">
                  <User className="w-4 h-4" />
                </div>
                <input
                  id="signup-name"
                  name="name"
                  type="text"
                  autoComplete="name"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your full name"
                  className="w-full pl-9 pr-3 py-2 bg-surface-container-low border border-outline-variant rounded-DEFAULT text-sm text-on-surface placeholder-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-colors font-sans"
                />
              </div>
            </div>

            {/* Work Email */}
            <div>
              <label
                htmlFor="signup-email"
                className="block text-xs font-semibold text-on-surface-variant mb-1.5 font-mono uppercase tracking-wider"
              >
                Work Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-secondary">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="signup-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@organization.in"
                  className="w-full pl-9 pr-3 py-2 bg-surface-container-low border border-outline-variant rounded-DEFAULT text-sm text-on-surface placeholder-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-colors font-sans"
                />
              </div>
            </div>

            {/* Organization / Startup Name */}
            <div>
              <label
                htmlFor="signup-organization"
                className="block text-xs font-semibold text-on-surface-variant mb-1.5 font-mono uppercase tracking-wider"
              >
                Organization / Startup Name
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-secondary">
                  <Building2 className="w-4 h-4" />
                </div>
                <input
                  id="signup-organization"
                  name="organization"
                  type="text"
                  autoComplete="organization"
                  required
                  value={organization}
                  onChange={(e) => setOrganization(e.target.value)}
                  placeholder="Enter company or enterprise name"
                  className="w-full pl-9 pr-3 py-2 bg-surface-container-low border border-outline-variant rounded-DEFAULT text-sm text-on-surface placeholder-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-colors font-sans"
                />
              </div>
            </div>

            {/* Password Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Password */}
              <div>
                <label
                  htmlFor="signup-password"
                  className="block text-xs font-semibold text-on-surface-variant mb-1.5 font-mono uppercase tracking-wider"
                >
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-secondary">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    id="signup-password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min 8 characters"
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

              {/* Confirm Password */}
              <div>
                <label
                  htmlFor="signup-confirm-password"
                  className="block text-xs font-semibold text-on-surface-variant mb-1.5 font-mono uppercase tracking-wider"
                >
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-secondary">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    id="signup-confirm-password"
                    name="confirm_password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeat password"
                    className="w-full pl-9 pr-10 py-2 bg-surface-container-low border border-outline-variant rounded-DEFAULT text-sm text-on-surface placeholder-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-colors font-sans"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-secondary hover:text-on-surface transition-colors"
                    aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Statutory Terms Consent Checkbox */}
            <div className="pt-2">
              <label htmlFor="signup-terms" className="flex items-start cursor-pointer select-none">
                <input
                  id="signup-terms"
                  name="terms_accepted"
                  type="checkbox"
                  required
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded-DEFAULT border-outline-variant text-primary focus:ring-0 accent-primary flex-shrink-0"
                />
                <span className="ml-2.5 text-xs text-secondary leading-snug">
                  I agree to statutory procurement governance terms and acknowledge that procurement intelligence is evidence-backed decision support requiring buyer verification before PO release.
                </span>
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-3 py-2.5 px-4 bg-primary hover:bg-primary-container text-on-primary font-medium rounded-DEFAULT text-sm transition-colors flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed font-mono"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-on-primary" />
                  <span>Creating Account...</span>
                </>
              ) : (
                <>
                  <span>Create Account</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Footer Link */}
          <div className="mt-6 pt-5 border-t border-surface-container-high text-center">
            <p className="text-xs text-secondary">
              Already have an account?{' '}
              <Link
                href="/signin"
                className="font-medium text-primary hover:text-primary-container transition-colors underline-offset-4 hover:underline"
              >
                Sign in
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
