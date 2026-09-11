'use client';

import React, { useState, useEffect } from 'react';
import { Cpu, Database, ShieldCheck, MapPin, Sparkles, CheckCircle2 } from 'lucide-react';

const PIPELINE_STEPS = [
  { icon: Cpu, label: 'Normalizing procurement specifications & physical units', color: 'text-blue-400' },
  { icon: Database, label: 'Querying 559 Indian Standards database (Hybrid BM25 + Vector)', color: 'text-amber-400' },
  { icon: ShieldCheck, label: 'Evaluating statutory compliance & BIS testing clauses', color: 'text-emerald-400' },
  { icon: MapPin, label: 'Discovering registered Indian manufacturing corridors & source records', color: 'text-purple-400' },
  { icon: Sparkles, label: 'Synthesizing evidence-backed grounded procurement briefing', color: 'text-cyan-400' },
];

export const LoadingState: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev < PIPELINE_STEPS.length - 1 ? prev + 1 : prev));
    }, 700);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Animated Pipeline Progress Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-5 h-5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-base font-bold text-white tracking-tight">
              Executing Multi-Stage Procurement Intelligence Pipeline
            </span>
          </div>
          <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
            STAGE {activeStep + 1} OF {PIPELINE_STEPS.length}
          </span>
        </div>

        <div className="space-y-3">
          {PIPELINE_STEPS.map((step, idx) => {
            const Icon = step.icon;
            const isCompleted = idx < activeStep;
            const isCurrent = idx === activeStep;
            return (
              <div
                key={idx}
                className={`flex items-center space-x-3 p-3 rounded-xl border transition-all duration-300 ${
                  isCurrent
                    ? 'bg-slate-800/80 border-amber-500/40 shadow-lg shadow-amber-500/5'
                    : isCompleted
                    ? 'bg-slate-950/40 border-emerald-500/20 text-slate-300'
                    : 'bg-slate-950/20 border-slate-800/50 text-slate-600'
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                ) : isCurrent ? (
                  <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin flex-shrink-0"></div>
                ) : (
                  <div className="w-4 h-4 rounded-full border border-slate-700 flex-shrink-0"></div>
                )}
                <Icon className={`w-4 h-4 ${isCurrent ? step.color : isCompleted ? 'text-emerald-400' : 'text-slate-600'} flex-shrink-0`} />
                <span className={`text-xs font-medium ${isCurrent ? 'text-white font-semibold' : ''}`}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Skeleton placeholders */}
      <div className="space-y-4 animate-pulse">
        {[1, 2].map((i) => (
          <div key={i} className="bg-slate-900/60 border border-slate-800/60 rounded-2xl p-6 space-y-4">
            <div className="flex justify-between items-center">
              <div className="h-5 bg-slate-800 rounded w-48"></div>
              <div className="h-6 bg-slate-800 rounded-full w-28"></div>
            </div>
            <div className="h-4 bg-slate-800/60 rounded w-3/4"></div>
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="h-16 bg-slate-950 rounded-xl"></div>
              <div className="h-16 bg-slate-950 rounded-xl"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
