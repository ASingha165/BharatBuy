'use client';

import React from 'react';
import { PackageEvaluation, GroundedExplanation } from '../types';
import { Award, AlertTriangle, CheckCircle, ShieldAlert, Sparkles, TrendingUp, Bot, FileText, Info, Layers, Check } from 'lucide-react';

interface PackageEvaluationSummaryProps {
  evaluation: PackageEvaluation;
  explanation: GroundedExplanation;
  company: string;
}

export const PackageEvaluationSummary: React.FC<PackageEvaluationSummaryProps> = ({
  evaluation,
  explanation,
  company
}) => {
  const score = evaluation.overall_readiness_score;

  const getScoreColor = (sc: number) => {
    if (sc >= 75) return { text: 'text-emerald-700', stroke: '#059669', bg: 'bg-emerald-50 border-emerald-200' };
    if (sc >= 50) return { text: 'text-amber-800', stroke: '#d97706', bg: 'bg-amber-50 border-amber-200' };
    return { text: 'text-error', stroke: '#ba1a1a', bg: 'bg-error-container border-error' };
  };

  const style = getScoreColor(score);

  return (
    <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-5 sm:p-7 shadow-sm space-y-6">
      {/* Top Header & Readiness Indicator */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 pb-5 border-b border-surface-container-high">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-1.5 bg-surface-container-high border border-surface-container-highest rounded-DEFAULT px-2.5 py-0.5 text-[11px] font-mono font-semibold text-primary">
            <Award className="w-3.5 h-3.5" />
            <span>Package Readiness Assessment</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">
            Procurement Evaluation: <span className="text-primary">{company}</span>
          </h2>
          <p className="text-xs sm:text-sm text-secondary max-w-2xl leading-relaxed">
            {evaluation.sourcing_feasibility}
          </p>
        </div>

        {/* Readiness Index Radial Display */}
        <div className="flex items-center space-x-4 bg-surface-container-low border border-surface-container-high p-3.5 rounded-DEFAULT self-start lg:self-auto shadow-sm">
          <div className="relative w-16 h-16 flex items-center justify-center">
            <svg className="w-16 h-16 transform -rotate-90">
              <circle
                cx="32"
                cy="32"
                r="26"
                stroke="currentColor"
                strokeWidth="5"
                className="text-surface-container-high"
                fill="transparent"
              />
              <circle
                cx="32"
                cy="32"
                r="26"
                stroke={style.stroke}
                strokeWidth="5"
                strokeDasharray={163}
                strokeDashoffset={163 - (163 * score) / 100}
                strokeLinecap="round"
                fill="transparent"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className={`text-sm font-extrabold font-mono ${style.text}`}>{score}%</span>
              <span className="text-[8px] text-secondary font-semibold uppercase font-mono">{evaluation.readiness_level}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-xs font-bold text-on-surface block">Readiness Index</span>
            <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-DEFAULT border inline-block ${style.bg} ${style.text}`}>
              {evaluation.readiness_level}
            </span>
            <span className="text-[10px] text-secondary font-mono block">{evaluation.total_items} Items Analyzed</span>
          </div>
        </div>
      </div>

      {/* Metric Bars (5 Core Coverage Indices) */}
      <div id="workflow-normalization" className="scroll-mt-24 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 text-xs">
        <div className="bg-surface-container-low rounded-DEFAULT p-3 border border-surface-container-high space-y-1">
          <div className="flex items-center justify-between font-mono">
            <span className="text-secondary text-[11px]">Standards</span>
            <span className="text-primary font-bold">{Math.round((evaluation.standards_coverage ?? 0) * 100)}%</span>
          </div>
          <div className="w-full h-1.5 bg-surface-container rounded-DEFAULT overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-500"
              style={{ width: `${(evaluation.standards_coverage ?? 0) * 100}%` }}
            />
          </div>
          <span className="text-[10px] text-secondary block truncate">IS Catalog Coverage</span>
        </div>

        <div className="bg-surface-container-low rounded-DEFAULT p-3 border border-surface-container-high space-y-1">
          <div className="flex items-center justify-between font-mono">
            <span className="text-secondary text-[11px]">Compliance</span>
            <span className="text-tertiary font-bold">{Math.round((evaluation.compliance_coverage ?? 0) * 100)}%</span>
          </div>
          <div className="w-full h-1.5 bg-surface-container rounded-DEFAULT overflow-hidden">
            <div
              className="h-full bg-tertiary-container transition-all duration-500"
              style={{ width: `${(evaluation.compliance_coverage ?? 0) * 100}%` }}
            />
          </div>
          <span className="text-[10px] text-secondary block truncate">Mandatory Schemes</span>
        </div>

        <div className="bg-surface-container-low rounded-DEFAULT p-3 border border-surface-container-high space-y-1">
          <div className="flex items-center justify-between font-mono">
            <span className="text-secondary text-[11px]">Sourcing</span>
            <span className="text-emerald-700 font-bold">{Math.round((evaluation.sourcing_coverage ?? 0) * 100)}%</span>
          </div>
          <div className="w-full h-1.5 bg-surface-container rounded-DEFAULT overflow-hidden">
            <div
              className="h-full bg-emerald-600 transition-all duration-500"
              style={{ width: `${(evaluation.sourcing_coverage ?? 0) * 100}%` }}
            />
          </div>
          <span className="text-[10px] text-secondary block truncate">Eligible Hubs / Mfrs</span>
        </div>

        <div className="bg-surface-container-low rounded-DEFAULT p-3 border border-surface-container-high space-y-1">
          <div className="flex items-center justify-between font-mono">
            <span className="text-secondary text-[11px]">Evidence</span>
            <span className="text-primary font-bold">{Math.round(((evaluation.evidence_coverage ?? evaluation.sourcing_coverage) ?? 0) * 100)}%</span>
          </div>
          <div className="w-full h-1.5 bg-surface-container rounded-DEFAULT overflow-hidden">
            <div
              className="h-full bg-primary-container transition-all duration-500"
              style={{ width: `${((evaluation.evidence_coverage ?? evaluation.sourcing_coverage) ?? 0) * 100}%` }}
            />
          </div>
          <span className="text-[10px] text-secondary block truncate">Authoritative Records</span>
        </div>

        <div className="bg-surface-container-low rounded-DEFAULT p-3 border border-surface-container-high space-y-1 col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between font-mono">
            <span className="text-secondary text-[11px]">Verification</span>
            <span className="text-secondary font-bold">{Math.round((evaluation.verification_coverage ?? 0) * 100)}%</span>
          </div>
          <div className="w-full h-1.5 bg-surface-container rounded-DEFAULT overflow-hidden">
            <div
              className="h-full bg-secondary transition-all duration-500"
              style={{ width: `${(evaluation.verification_coverage ?? 0) * 100}%` }}
            />
          </div>
          <span className="text-[10px] text-secondary block truncate">Documented CML Licenses</span>
        </div>
      </div>

      {/* 4-State Decision Summary Banner */}
      {evaluation.decision_summary && (() => {
        const dStatus = evaluation.decision_summary?.decision_status || evaluation.decision_status || (evaluation.decision_summary?.procurement_ready ? 'READY' : 'READY_WITH_VERIFICATION');
        const badgeStyle = 
          dStatus === 'READY'
            ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
            : dStatus === 'READY_WITH_VERIFICATION'
            ? 'bg-amber-50 text-amber-800 border-amber-300'
            : dStatus === 'INSUFFICIENT_EVIDENCE'
            ? 'bg-surface-container text-secondary border-outline-variant'
            : 'bg-error-container text-on-error-container border-error';

        const labelText =
          dStatus === 'READY'
            ? 'READY — Procurement-ready for buyer approval'
            : dStatus === 'READY_WITH_VERIFICATION'
            ? 'READY WITH VERIFICATION — Buyer approval required after live portal check'
            : dStatus === 'INSUFFICIENT_EVIDENCE'
            ? 'INSUFFICIENT EVIDENCE — Clarify specifications & standard requirements'
            : 'NOT RECOMMENDED — Regulatory conflict or unviable sourcing';

        return (
          <div id="workflow-approval" className="scroll-mt-24 bg-surface-container-low border border-surface-container-high rounded-DEFAULT p-4 text-xs space-y-2.5 shadow-sm">
            <div className="flex items-center justify-between pb-2 border-b border-surface-container-high flex-wrap gap-2">
              <span className="font-bold text-on-surface flex items-center gap-1.5 font-mono">
                <FileText className="w-4 h-4 text-primary" />
                <span>PROCUREMENT EXECUTION DECISION</span>
              </span>
              <span className={`px-2 py-0.5 rounded-DEFAULT font-mono font-bold text-[10px] uppercase border ${badgeStyle}`}>
                {labelText}
              </span>
            </div>
            <p className="text-secondary text-[11px] leading-relaxed">
              {evaluation.decision_summary.summary_text}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1">
              {evaluation.decision_summary.strong_sourcing_items.length > 0 && (
                <div className="bg-surface-container-lowest p-2.5 rounded-DEFAULT border border-surface-container-high text-secondary">
                  <strong className="text-emerald-700 font-mono">✓ High Alignment Items: </strong>
                  <span>{evaluation.decision_summary.strong_sourcing_items.join(', ')}</span>
                </div>
              )}
              {evaluation.decision_summary.verification_required_items.length > 0 && (
                <div className="bg-surface-container-lowest p-2.5 rounded-DEFAULT border border-surface-container-high text-secondary">
                  <strong className="text-amber-800 font-mono">⚠ Verification Required: </strong>
                  <span>{evaluation.decision_summary.verification_required_items.join(', ')}</span>
                </div>
              )}
            </div>
            {evaluation.decision_summary.missing_verifications && evaluation.decision_summary.missing_verifications.length > 0 && (
              <div id="workflow-verification" className="scroll-mt-24 bg-amber-50 p-2.5 rounded-DEFAULT border border-amber-200 text-[10px] text-amber-900 space-y-1">
                <strong className="text-amber-800 block uppercase font-mono tracking-wider">
                  Mandatory Buyer Verification Checklist:
                </strong>
                <ul className="list-disc list-inside space-y-0.5 text-amber-950">
                  {evaluation.decision_summary.missing_verifications.map((v, idx) => (
                    <li key={idx}>{v}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex items-start gap-1.5 pt-2 border-t border-surface-container-high text-[11px] text-secondary leading-relaxed">
              <Info className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
              <span>
                Procurement intelligence is evidence-backed decision support. Certification validity and supplier eligibility should be independently verified before buyer approval.
              </span>
            </div>
          </div>
        );
      })()}

      {/* Stitch 3-Tier Grounded AI Briefing Section */}
      <div id="workflow-explanation" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between border-b border-surface-container-high pb-2 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-DEFAULT bg-primary-container flex items-center justify-center text-white shadow-sm">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <h3 className="text-sm font-bold text-on-surface uppercase tracking-tight font-mono">
              Grounded AI Explainability Briefing
            </h3>
          </div>
          {explanation.synthesis_type === 'LIVE_GEMINI_SYNTHESIS' || (!explanation.summary.includes('Gemini explanation unavailable') && (explanation.summary.includes('SUPPORTED BY EVIDENCE') || explanation.summary.includes('SUPPORTED BY DATABASE'))) ? (
            <span className="font-mono text-[10px] text-cyan-800 bg-cyan-50 border border-cyan-300 px-2 py-0.5 rounded-DEFAULT font-semibold flex items-center gap-1 shadow-sm">
              <Sparkles className="w-3 h-3 text-cyan-600" />
              <span>LIVE GEMINI SYNTHESIS</span>
            </span>
          ) : (
            <span className="font-mono text-[10px] text-secondary bg-surface-container-high border border-surface-container-highest px-2 py-0.5 rounded-DEFAULT font-semibold">
              GROUNDED DETERMINISTIC FALLBACK
            </span>
          )}
        </div>

        {/* Narrative Executive Summary */}
        <p className="text-xs sm:text-sm text-on-surface leading-relaxed bg-surface-container-low p-3.5 rounded-DEFAULT border border-surface-container-high">
          {explanation.summary}
        </p>

        {/* 3-Part Grounded Attribution Split Layout */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
          {/* 1. Supported by Evidence Card */}
          <div className="bg-surface-container-lowest rounded-DEFAULT p-3.5 border border-surface-container-high relative overflow-hidden flex flex-col gap-2 shadow-sm">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500"></div>
            <div className="flex items-center justify-between pl-1">
              <span className="font-mono text-[10px] font-bold text-emerald-800 uppercase tracking-wide flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                <span>SUPPORTED BY EVIDENCE / DATABASE</span>
              </span>
            </div>
            <ul className="space-y-1 text-on-surface text-[11px] pl-1 list-none">
              {explanation.supported_by_data && explanation.supported_by_data.length > 0 ? (
                explanation.supported_by_data.slice(0, 4).map((item, idx) => (
                  <li key={idx} className="line-clamp-2 leading-relaxed text-secondary flex items-start gap-1.5">
                    <span className="text-emerald-600 text-xs font-bold shrink-0 mt-0.5">✓</span>
                    <span>{item.replace(/\[SUPPORTED BY DATABASE\]\s*/g, '').replace(/\[SUPPORTED BY EVIDENCE\]\s*/g, '')}</span>
                  </li>
                ))
              ) : (
                <li className="text-secondary italic">No direct standard records returned.</li>
              )}
            </ul>
          </div>

          {/* 2. Inferred from Matching Card */}
          <div className="bg-surface-container-lowest rounded-DEFAULT p-3.5 border border-surface-container-high relative overflow-hidden flex flex-col gap-2 shadow-sm">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary-container"></div>
            <div className="flex items-center justify-between pl-1">
              <span className="font-mono text-[10px] font-bold text-primary uppercase tracking-wide flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-primary" />
                <span>INFERRED FROM MATCHING ENGINE</span>
              </span>
            </div>
            <ul className="space-y-1 text-on-surface text-[11px] pl-1 list-none">
              {explanation.inference_requires_verification && explanation.inference_requires_verification.length > 0 ? (
                explanation.inference_requires_verification.slice(0, 4).map((item, idx) => (
                  <li key={idx} className="line-clamp-2 leading-relaxed text-secondary flex items-start gap-1.5">
                    <span className="text-primary-container text-xs font-bold shrink-0 mt-0.5">→</span>
                    <span>{item.replace(/\[INFERRED FROM MATCHING\]\s*/g, '').replace(/\[INFERRED\]\s*/g, '')}</span>
                  </li>
                ))
              ) : (
                <li className="text-secondary italic">No inferences required.</li>
              )}
            </ul>
          </div>

          {/* 3. Requires Live Verification Card */}
          <div className="bg-surface-container-lowest rounded-DEFAULT p-3.5 border border-surface-container-high relative overflow-hidden flex flex-col gap-2 shadow-sm">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-amber-500"></div>
            <div className="flex items-center justify-between pl-1">
              <span className="font-mono text-[10px] font-bold text-amber-800 uppercase tracking-wide flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                <span>REQUIRES LIVE BUYER VERIFICATION</span>
              </span>
            </div>
            <ul className="space-y-1 text-on-surface text-[11px] pl-1 list-none">
              {explanation.compliance_caveats && explanation.compliance_caveats.length > 0 ? (
                explanation.compliance_caveats.slice(0, 4).map((item, idx) => (
                  <li key={idx} className="line-clamp-2 leading-relaxed text-secondary flex items-start gap-1.5">
                    <span className="text-amber-700 text-xs font-bold shrink-0 mt-0.5">!</span>
                    <span>{item.replace(/\[REQUIRES VERIFICATION\]\s*/g, '')}</span>
                  </li>
                ))
              ) : (
                <li className="text-secondary italic">Verification completed.</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
