'use client';

import React, { useEffect, useState } from 'react';
import { StandardDetailResponse } from '../types';
import { getStandardDetails } from '../lib/api';
import { X, FileText, Calendar, Building2, CheckCircle, Network, ArrowRight } from 'lucide-react';

interface StandardDetailsProps {
  standardId: string | null;
  onClose: () => void;
  onSelectRelated: (standard_id: string) => void;
}

export const StandardDetails: React.FC<StandardDetailsProps> = ({
  standardId,
  onClose,
  onSelectRelated,
}) => {
  const [details, setDetails] = useState<StandardDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (standardId) {
      setIsLoading(true);
      getStandardDetails(standardId)
        .then(setDetails)
        .catch(() => setDetails(null))
        .finally(() => setIsLoading(false));
    }
  }, [standardId]);

  if (!standardId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-inverse-surface/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-surface-container-lowest border border-surface-container-high w-full max-w-2xl rounded-DEFAULT p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-secondary hover:text-on-surface bg-surface-container hover:bg-surface-container-high p-2 rounded-DEFAULT transition"
        >
          <X className="w-5 h-5" />
        </button>

        {isLoading ? (
          <div className="py-12 text-center text-secondary space-y-3">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-sm font-mono">Fetching Indian Standard specification details...</p>
          </div>
        ) : details ? (
          <div className="space-y-6">
            <div className="border-b border-surface-container-high pb-4">
              <div className="flex items-center space-x-3 mb-2">
                <span className="text-2xl font-extrabold text-on-surface tracking-wide font-mono">
                  {details.is_code}
                </span>
                <span className="bg-emerald-50 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-DEFAULT border border-emerald-200 font-mono">
                  {details.status}
                </span>
              </div>
              <h2 className="text-lg font-semibold text-on-surface leading-snug">
                {details.title}
              </h2>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="bg-surface-container-low p-3 rounded-DEFAULT border border-surface-container-high flex items-center space-x-2">
                <Building2 className="w-4 h-4 text-primary" />
                <div>
                  <span className="text-secondary block font-medium font-mono text-[11px]">Department</span>
                  <span className="text-on-surface font-semibold">{details.department}</span>
                </div>
              </div>

              <div className="bg-surface-container-low p-3 rounded-DEFAULT border border-surface-container-high flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-primary" />
                <div>
                  <span className="text-secondary block font-medium font-mono text-[11px]">Publication Year</span>
                  <span className="text-on-surface font-semibold font-mono">{details.publication_year}</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-on-surface mb-2 flex items-center space-x-2 font-mono">
                <FileText className="w-4 h-4 text-primary" />
                <span>Scope & Technical Applicability</span>
              </h3>
              <p className="text-xs text-on-surface bg-surface-container-low p-4 rounded-DEFAULT border border-surface-container-high leading-relaxed">
                {details.scope_summary}
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-secondary mb-1 font-mono">Key Specifications</h4>
                <div className="text-xs text-on-surface bg-surface-container-low p-3.5 rounded-DEFAULT border border-surface-container-high font-mono">
                  {details.key_specifications}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-secondary mb-1 font-mono">Mandatory Testing Requirements</h4>
                <div className="text-xs text-on-surface bg-surface-container-low p-3.5 rounded-DEFAULT border border-surface-container-high font-mono">
                  {details.testing_requirements}
                </div>
              </div>
            </div>

            {details.related_standards && details.related_standards.length > 0 && (
              <div className="border-t border-surface-container-high pt-4">
                <h3 className="text-xs font-semibold text-on-surface mb-3 flex items-center space-x-1.5 font-mono">
                  <Network className="w-4 h-4 text-primary" />
                  <span>Connected Inter-Standard Relationships ({details.related_standards.length})</span>
                </h3>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {details.related_standards.map((rel, idx) => (
                    <div
                      key={idx}
                      onClick={() => onSelectRelated(rel.standard_id)}
                      className="bg-surface-container-low hover:bg-surface-container p-3 rounded-DEFAULT border border-surface-container-high flex items-center justify-between cursor-pointer transition"
                    >
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-primary font-mono">{rel.is_code}</span>
                          <span className="text-[10px] bg-surface-container text-primary px-2 py-0.5 rounded-DEFAULT font-mono border border-surface-container-high">
                            {rel.relationship_type}
                          </span>
                        </div>
                        <p className="text-[11px] text-secondary line-clamp-1">{rel.title}</p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-secondary" />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="py-12 text-center text-error text-sm font-mono">
            Failed to load standard details.
          </div>
        )}
      </div>
    </div>
  );
};
