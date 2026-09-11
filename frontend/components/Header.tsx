'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getHealthStatus } from '../lib/api';
import { HealthStatus } from '../types';
import { BharatBuyLogo } from './BharatBuyLogo';
import { useAuth } from '../lib/auth-context';
import { Activity, Layers, Cpu, LogOut, LogIn } from 'lucide-react';

export const Header: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const { user, signOut } = useAuth();
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;

    // Timeout sentinel: if the health request takes longer than 8 seconds,
    // mark as unavailable so the UI doesn't stay stuck at "Connecting to Engine..."
    const timeoutId = setTimeout(() => {
      if (!cancelled) {
        setHealth({ status: 'UNAVAILABLE', database: false, total_standards: 0 });
      }
    }, 8000);

    getHealthStatus()
      .then((data) => {
        if (!cancelled) {
          clearTimeout(timeoutId);
          setHealth(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          clearTimeout(timeoutId);
          // Backend unreachable — show UNAVAILABLE instead of staying at "Connecting"
          setHealth({ status: 'UNAVAILABLE', database: false, total_standards: 0 });
        }
      });

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, []);

  const handleSignOut = async () => {
    await signOut();
    router.push('/signin');
  };

  return (
    <header className="fixed top-0 w-full z-50 bg-inverse-surface shadow-[0_1px_8px_rgba(0,0,0,0.15)] border-b border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand & Identity */}
        <Link href="/" className="flex items-center space-x-3 min-w-0 hover:opacity-95 transition-opacity">
          <div className="flex-shrink-0">
            <BharatBuyLogo size={38} />
          </div>
          <div className="flex flex-col min-w-0">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base sm:text-lg tracking-tight text-white leading-none">
                BHARATBUY
              </span>
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-DEFAULT bg-slate-800/90 text-slate-200 font-mono text-[10px] uppercase tracking-wider border border-slate-700/80">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                PROD
              </span>
            </div>
            <span className="font-mono text-[10px] text-surface-variant uppercase tracking-wider truncate mt-0.5">
              AI PROCUREMENT INTELLIGENCE
            </span>
          </div>
        </Link>

        {/* Real-time System Status Telemetry & User Identity */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          {health === null ? (
            /* CONNECTING — waiting for first response */
            <div className="hidden sm:flex items-center space-x-2 text-xs text-surface-container-high bg-white/10 border border-white/10 px-3 py-1.5 rounded-DEFAULT">
              <Activity className="w-3.5 h-3.5 animate-spin text-primary-fixed" />
              <span>Connecting to Engine...</span>
            </div>
          ) : health.status === 'UNAVAILABLE' ? (
            /* UNAVAILABLE — backend unreachable or timed out */
            <div className="hidden sm:flex items-center space-x-2 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 px-3 py-1.5 rounded-DEFAULT">
              <span className="w-2 h-2 rounded-full bg-rose-400 shrink-0" />
              <span className="font-mono font-semibold">Engine Unavailable</span>
            </div>
          ) : (
            /* HEALTHY — backend responded successfully */
            <div className="hidden sm:flex items-center space-x-2.5 bg-white/10 border border-white/10 rounded-DEFAULT px-3 py-1.5 text-xs text-surface-container-high">
              <div className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span className="font-medium text-emerald-300 hidden lg:inline">System Active</span>
              </div>
              <span className="text-white/20">|</span>
              <div className="flex items-center space-x-1">
                <Layers className="w-3.5 h-3.5 text-primary-fixed" />
                <span className="font-mono font-semibold text-white">{health.total_standards}</span>
                <span className="text-surface-container-high text-[11px] hidden md:inline">Standards</span>
              </div>
              <span className="text-white/20 hidden md:inline">|</span>
              <div className="hidden md:flex items-center space-x-1 text-surface-container-high text-[11px]">
                <Cpu className="w-3.5 h-3.5 text-amber-300" />
                <span>Hybrid BM25+Vector</span>
              </div>
              <span className="text-white/20 hidden lg:inline">|</span>
              {health.gemini_configured ? (
                <span className="hidden lg:inline-flex items-center gap-1 bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-mono font-semibold px-2 py-0.5 rounded-DEFAULT text-[10px] tracking-wide">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                  GEMINI ACTIVE
                </span>
              ) : (
                <span className="hidden lg:inline-flex items-center gap-1 bg-slate-500/20 text-slate-300 border border-slate-500/30 font-mono font-semibold px-2 py-0.5 rounded-DEFAULT text-[10px] tracking-wide">
                  DETERMINISTIC FALLBACK
                </span>
              )}
              <span className="text-white/20">|</span>
              {health.is_demo_mode ? (
                <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono font-semibold px-2 py-0.5 rounded-DEFAULT text-[10px] tracking-wide">
                  DEMO MODE
                </span>
              ) : (
                <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono font-semibold px-2 py-0.5 rounded-DEFAULT text-[10px] tracking-wide">
                  PRODUCTION REGISTRY
                </span>
              )}
            </div>
          )}


          {/* Authenticated User Identity Area */}
          {user ? (
            <div className="flex items-center space-x-2 bg-white/10 border border-white/10 rounded-DEFAULT px-2.5 py-1.5 text-xs">
              <div className="flex items-center space-x-1.5 min-w-0 max-w-[160px] sm:max-w-[200px]">
                <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center flex-shrink-0 text-white font-medium text-xs">
                  {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </div>
                <div className="flex flex-col min-w-0 leading-tight">
                  <span className="font-medium text-white truncate">{user.name}</span>
                  <span className="text-[10px] text-surface-container-high font-mono truncate">{user.organization}</span>
                </div>
              </div>
              <span className="text-white/20">|</span>
              <button
                onClick={handleSignOut}
                title="Sign out"
                aria-label="Sign out"
                className="text-surface-container-high hover:text-rose-300 transition-colors p-1 rounded-DEFAULT hover:bg-white/10"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <Link
              href="/signin"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-primary hover:bg-primary-container text-white rounded-DEFAULT text-xs font-medium transition-colors shadow-sm"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};
