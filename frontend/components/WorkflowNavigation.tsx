'use client';

import React, { useState, useEffect } from 'react';

export interface WorkflowStep {
  id: string;
  stepNumber: number;
  label: string;
  targetId: string;
  statusText: string;
  statusType: 'complete' | 'active' | 'pending' | 'action' | 'audit';
}

interface WorkflowNavigationProps {
  hasResults: boolean;
  synthesisType?: string;
  activeTargetId?: string | null;
  onStepClick?: (targetId: string) => void;
}

const AUDIT_STEPS: WorkflowStep[] = [
  { id: 'requirements', stepNumber: 1, label: '1. Requirement Parsing', targetId: 'workflow-requirements', statusText: 'COMPLETE', statusType: 'complete' },
  { id: 'normalization', stepNumber: 2, label: '2. BOM Normalization', targetId: 'workflow-normalization', statusText: 'COMPLETE', statusType: 'complete' },
  { id: 'standards', stepNumber: 3, label: '3. BIS / ISO Standards Matching', targetId: 'workflow-standards', statusText: 'MATCHED', statusType: 'complete' },
  { id: 'compliance', stepNumber: 4, label: '4. Statutory Compliance Engine', targetId: 'workflow-compliance', statusText: 'EVALUATED', statusType: 'complete' },
  { id: 'sourcing', stepNumber: 5, label: '5. Sourcing Corridor Proximity', targetId: 'workflow-sourcing', statusText: 'MAPPED', statusType: 'complete' },
  { id: 'evidence', stepNumber: 6, label: '6. Evidence & MTC Registry', targetId: 'workflow-evidence', statusText: 'AVAILABLE', statusType: 'complete' },
  { id: 'verification', stepNumber: 7, label: '7. Statutory Verification Gate', targetId: 'workflow-verification', statusText: 'AUDIT REQUIRED', statusType: 'audit' },
  { id: 'explanation', stepNumber: 8, label: '8. Grounded LLM Synthesis', targetId: 'workflow-explanation', statusText: 'GROUNDED', statusType: 'complete' },
  { id: 'approval', stepNumber: 9, label: '9. Buyer Approval Gate', targetId: 'workflow-approval', statusText: 'BUYER ACTION', statusType: 'action' },
];

export const WorkflowNavigation: React.FC<WorkflowNavigationProps> = ({
  hasResults,
  synthesisType,
  activeTargetId,
  onStepClick
}) => {
  const [currentActiveId, setCurrentActiveId] = useState<string>('workflow-requirements');

  useEffect(() => {
    if (activeTargetId) {
      setCurrentActiveId(activeTargetId);
      return;
    }

    if (!hasResults) {
      setCurrentActiveId('workflow-requirements');
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntry = entries.find((entry) => entry.isIntersecting);
        if (visibleEntry) {
          setCurrentActiveId(visibleEntry.target.id);
        }
      },
      {
        rootMargin: '-88px 0px -60% 0px',
        threshold: 0.1
      }
    );

    AUDIT_STEPS.forEach((step) => {
      const el = document.getElementById(step.targetId);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [hasResults, activeTargetId]);

  const handleStepClick = (step: WorkflowStep) => {
    if (!hasResults && step.stepNumber > 1) {
      const reqEl = document.getElementById('workflow-requirements');
      if (reqEl) {
        reqEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      return;
    }

    setCurrentActiveId(step.targetId);
    if (onStepClick) {
      onStepClick(step.targetId);
    }

    const targetEl = document.getElementById(step.targetId);
    if (targetEl) {
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="w-full bg-surface-container-lowest rounded-DEFAULT border border-surface-container-high p-space-md shadow-sm flex flex-col gap-space-sm mb-space-lg">
      {/* Tracker Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-space-xs">
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
          <span className="font-mono text-xs font-semibold text-on-surface uppercase tracking-tight">
            Audit Pipeline Tracker
          </span>
        </div>
        <span className="font-mono text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-DEFAULT flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
          {hasResults ? 'Pipeline Executed' : 'Awaiting Input'}
        </span>
      </div>

      {/* Linear Dense Step Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
        {AUDIT_STEPS.map((step) => {
          const isEnabled = hasResults || step.stepNumber === 1;
          const isActive = currentActiveId === step.targetId;

          let stepBg = 'bg-surface-container-low border-transparent text-on-surface';
          let icon = <span className="w-5 h-5 rounded-full bg-surface-container text-secondary flex items-center justify-center text-[11px] font-bold font-mono">{step.stepNumber}</span>;
          let badgeColor = 'text-secondary bg-surface-container';
          let displayStatus = step.statusText;

          if (!isEnabled) {
            stepBg = 'bg-surface-container-low/50 border-transparent text-secondary/60 opacity-60';
            badgeColor = 'text-secondary/60 bg-surface-container-low';
          } else if (step.id === 'approval') {
            stepBg = isActive ? 'bg-amber-100/80 border-amber-400' : 'bg-amber-50/70 border-amber-200/80';
            icon = <span className="w-5 h-5 rounded-full bg-amber-200 text-amber-900 flex items-center justify-center text-[11px] font-bold font-mono">!</span>;
            badgeColor = 'text-amber-800 bg-amber-100 font-bold border border-amber-300';
          } else if (step.id === 'verification') {
            stepBg = isActive ? 'bg-amber-50 border-amber-300' : 'bg-surface-container-low border-surface-container-high';
            icon = <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center text-[11px] font-bold font-mono">7</span>;
            badgeColor = 'text-amber-800 bg-amber-50 border border-amber-200';
          } else if (step.id === 'explanation') {
            if (synthesisType === 'LIVE_GEMINI_SYNTHESIS') {
              displayStatus = 'LIVE GEMINI';
              stepBg = isActive ? 'bg-cyan-50 border-cyan-400' : 'bg-surface-container-low border-transparent hover:bg-surface-container';
              icon = <span className="w-5 h-5 rounded-full bg-cyan-100 text-cyan-800 flex items-center justify-center text-[11px] font-bold font-mono">8</span>;
              badgeColor = 'text-cyan-800 bg-cyan-50 border border-cyan-300 font-semibold';
            } else {
              displayStatus = 'FALLBACK';
              stepBg = isActive ? 'bg-primary-fixed/40 border-primary' : 'bg-surface-container-low border-transparent hover:bg-surface-container';
              icon = <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-800 flex items-center justify-center text-[11px] font-bold font-mono">8</span>;
              badgeColor = 'text-secondary bg-surface-container border border-outline-variant';
            }
          } else if (isEnabled) {
            stepBg = isActive ? 'bg-primary-fixed/40 border-primary' : 'bg-surface-container-low border-transparent hover:bg-surface-container';
            icon = <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center text-[11px] font-bold font-mono">✓</span>;
            badgeColor = 'text-emerald-700 bg-emerald-50 border border-emerald-200';
          }

          return (
            <button
              key={step.id}
              type="button"
              onClick={() => handleStepClick(step)}
              disabled={!isEnabled}
              className={`flex items-center justify-between p-2 rounded-DEFAULT border transition-all text-left ${stepBg} ${
                isActive ? 'ring-1 ring-primary' : ''
              }`}
            >
              <div className="flex items-center gap-2 min-w-0 pr-1">
                {icon}
                <span className="text-xs font-semibold truncate text-on-surface">
                  {step.label}
                </span>
              </div>
              <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded-DEFAULT uppercase whitespace-nowrap flex-shrink-0 ${badgeColor}`}>
                {displayStatus}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
