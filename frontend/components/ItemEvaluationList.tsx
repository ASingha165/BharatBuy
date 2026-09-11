'use client';

import React, { useState } from 'react';
import { ItemComplianceEvaluation } from '../types';
import { CheckCircle2, AlertCircle, HelpCircle, Shield, Award, Network, FileText, ChevronDown, ChevronUp } from 'lucide-react';

interface ItemEvaluationListProps {
  items: ItemComplianceEvaluation[];
  onSelectStandard: (standard_id: string) => void;
  onSelectGraph: (standard_id: string) => void;
}

export const ItemEvaluationList: React.FC<ItemEvaluationListProps> = ({
  items,
  onSelectStandard,
  onSelectGraph
}) => {
  const [expandedItemId, setExpandedItemId] = useState<string | null>(items.length > 0 ? items[0].item_id : null);

  const toggleItem = (itemId: string) => {
    setExpandedItemId(expandedItemId === itemId ? null : itemId);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLIANT':
        return {
          bg: 'bg-emerald-50 text-emerald-800 border-emerald-300',
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />,
          label: '100% Statutory Match'
        };
      case 'CONDITIONAL_COMPLIANCE':
        return {
          bg: 'bg-amber-50 text-amber-800 border-amber-300',
          icon: <AlertCircle className="w-3.5 h-3.5 text-amber-700" />,
          label: 'Conditional Compliance'
        };
      default:
        return {
          bg: 'bg-error-container text-on-error-container border-error',
          icon: <HelpCircle className="w-3.5 h-3.5 text-error" />,
          label: 'Action Required'
        };
    }
  };

  return (
    <div id="workflow-compliance" className="scroll-mt-24 space-y-4">
      {/* Top Analytical Banner */}
      <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-4 sm:p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-4 h-4 text-primary" />
            <h3 className="text-base sm:text-lg font-bold text-on-surface tracking-tight font-mono uppercase">
              Item Compliance & Sourcing Evaluation
            </h3>
          </div>
          <p className="text-xs text-secondary">
            {items.length} Procurement Items Evaluated under Bureau of Indian Standards (BIS) & Quality Control Orders
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="font-mono text-xs text-primary bg-surface-container-high border border-surface-container-highest px-2.5 py-1 rounded-DEFAULT font-semibold">
            {items.length}/{items.length} Evaluated
          </span>
        </div>
      </div>

      {/* Item Cards Stack */}
      <div className="space-y-3">
        {items.map((item, idx) => {
          const badge = getStatusBadge(item.compliance_status);
          const primary = item.primary_standard;
          const isExpanded = expandedItemId === item.item_id;

          // Decoupled twin metrics calculation from item score and profile
          const suitabilityScore = Math.min(100, Math.max(10, Math.round(item.score * 100)));
          const trustScore = item.compliance_status === 'COMPLIANT' ? 88 : item.compliance_status === 'CONDITIONAL_COMPLIANCE' ? 74 : 50;

          return (
            <div
              key={item.item_id}
              className="bg-surface-container-lowest border border-surface-container-high hover:border-primary/40 rounded-DEFAULT shadow-sm transition overflow-hidden"
            >
              {/* Card Summary Header */}
              <div
                onClick={() => toggleItem(item.item_id)}
                className="p-4 sm:p-5 cursor-pointer select-none relative"
              >
                {/* Vertical Indicator Accent */}
                <div
                  className={`absolute left-0 top-0 bottom-0 w-1 ${
                    item.compliance_status === 'COMPLIANT'
                      ? 'bg-emerald-600'
                      : item.compliance_status === 'CONDITIONAL_COMPLIANCE'
                      ? 'bg-amber-500'
                      : 'bg-error'
                  }`}
                />

                <div className="flex items-start justify-between gap-3 pl-1">
                  <div className="min-w-0 flex-1 space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-[10px] font-bold text-primary bg-surface-container-high border border-surface-container-highest px-2 py-0.5 rounded-DEFAULT">
                        LINE #{idx + 1}
                      </span>
                      {primary && (
                        <span className="font-mono text-[11px] font-bold text-primary bg-primary-fixed/40 border border-primary-fixed px-2 py-0.5 rounded-DEFAULT">
                          {primary.is_code}
                        </span>
                      )}
                      <span className="text-[11px] bg-surface-container text-on-surface-variant border border-surface-container-high px-2 py-0.5 rounded-DEFAULT font-medium">
                        {item.normalized_profile.category}
                      </span>
                      <span className="text-xs text-secondary font-mono">
                        Qty: <strong className="text-on-surface">{item.normalized_profile.quantity}</strong> {item.normalized_profile.unit || 'units'}
                      </span>
                    </div>

                    <h4 className="text-base font-bold text-on-surface tracking-tight truncate">
                      {item.item_name}
                    </h4>

                    {primary && (
                      <p className="text-xs text-secondary line-clamp-1">
                        {primary.title}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-DEFAULT border flex items-center gap-1.5 font-mono ${badge.bg}`}>
                      {badge.icon}
                      <span className="hidden sm:inline">{badge.label}</span>
                    </span>
                    <button className="text-secondary hover:text-on-surface p-1">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Decoupled Twin Metrics Display (Side-by-Side) */}
                <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-surface-container-high pl-1">
                  {/* Metric 1: Product Suitability */}
                  <div className="bg-surface-container-low rounded-DEFAULT p-2.5 border border-surface-container-high">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-[10px] text-secondary uppercase tracking-wider">Product Suitability</span>
                      <span className="font-mono text-[11px] font-bold text-on-surface">{suitabilityScore} / 100</span>
                    </div>
                    <div className="w-full bg-surface-container h-1 rounded-DEFAULT mt-1.5 overflow-hidden">
                      <div className="bg-primary h-full" style={{ width: `${suitabilityScore}%` }} />
                    </div>
                    <span className="font-mono text-[10px] text-primary mt-1 block truncate font-medium">
                      {primary ? `${primary.is_code} Specification Matched` : 'Standard Verification Required'}
                    </span>
                  </div>

                  {/* Metric 2: Source Trust */}
                  <div className="bg-surface-container-low rounded-DEFAULT p-2.5 border border-surface-container-high">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-[10px] text-secondary uppercase tracking-wider">Source Trust</span>
                      <span className="font-mono text-[11px] font-bold text-on-surface">{trustScore} / 100</span>
                    </div>
                    <div className="w-full bg-surface-container h-1 rounded-DEFAULT mt-1.5 overflow-hidden">
                      <div className="bg-secondary h-full" style={{ width: `${trustScore}%` }} />
                    </div>
                    <span className="font-mono text-[10px] text-secondary mt-1 block truncate font-medium">
                      Requires Live Portal Check (manakonline.in)
                    </span>
                  </div>
                </div>
              </div>

              {/* Expanded Technical Details Drawer */}
              {isExpanded && primary && (
                <div className="bg-surface-container-low/60 p-4 sm:p-5 border-t border-surface-container-high space-y-4">
                  {/* Technical Match Rationale */}
                  <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-3 space-y-1 shadow-sm">
                    <span className="font-mono text-[11px] text-primary uppercase tracking-wide block font-semibold">
                      Technical Match Rationale:
                    </span>
                    <p className="text-xs text-on-surface leading-relaxed">
                      {primary.reason}
                    </p>
                  </div>

                  {/* Parameter Compliance Micro-Table */}
                  <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-3 shadow-sm">
                    <div className="flex items-center justify-between pb-2 mb-2 border-b border-surface-container-high text-xs">
                      <span className="font-mono text-[11px] text-on-surface uppercase tracking-wider font-semibold">
                        Parameter Compliance Audit
                      </span>
                      <span className="font-mono text-[10px] text-primary bg-surface-container-high px-2 py-0.5 rounded-DEFAULT">
                        {primary.is_code} Specifications
                      </span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-start justify-between gap-4">
                        <span className="text-secondary text-[11px]">Mandatory Testing Clauses:</span>
                        <span className="text-on-surface text-right text-[11px] font-mono max-w-md">
                          {primary.testing_requirements || 'Standard laboratory physical and chemical testing mandated under Scheme I.'}
                        </span>
                      </div>
                      <div className="flex items-start justify-between gap-4 pt-1 border-t border-surface-container-high">
                        <span className="text-secondary text-[11px]">Key Specifications:</span>
                        <span className="text-on-surface text-right text-[11px] font-mono max-w-md">
                          {primary.key_specifications || 'Technical characteristics per Bureau of Indian Standards specification schedule.'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between gap-4 pt-1 border-t border-surface-container-high">
                        <span className="text-secondary text-[11px]">Conformity Scheme:</span>
                        <span className="text-primary font-mono text-[11px] font-semibold">
                          {item.applicable_scheme}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Missing Parameters Warning */}
                  {item.missing_parameters && item.missing_parameters.length > 0 && (
                    <div className="bg-amber-50 border border-amber-200 rounded-DEFAULT p-3 text-xs flex items-start gap-2.5">
                      <AlertCircle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                      <div>
                        <strong className="font-mono text-[11px] text-amber-900 uppercase block mb-1">
                          Missing Technical Parameters to Specify:
                        </strong>
                        <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-950 font-mono">
                          {item.missing_parameters.map((p, pIdx) => (
                            <li key={pIdx}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  {/* Action Bar */}
                  <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-surface-container-high">
                    <button
                      type="button"
                      onClick={() => onSelectGraph(primary.standard_id)}
                      className="bg-surface-container hover:bg-surface-container-high text-primary border border-surface-container-high px-3 py-1.5 rounded-DEFAULT flex items-center gap-1.5 text-xs font-mono transition"
                    >
                      <Network className="w-3.5 h-3.5" />
                      <span>Relationships Graph</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => onSelectStandard(primary.standard_id)}
                      className="bg-primary hover:bg-primary-container text-white px-3.5 py-1.5 rounded-DEFAULT flex items-center gap-1.5 text-xs font-mono font-medium transition shadow-sm"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Inspect Standard Clauses</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
