'use client';

import React from 'react';
import { RecommendationResultItem } from '../types';
import { Award, FileText, CheckCircle2, Network, ArrowRight, ShieldAlert, Cpu } from 'lucide-react';

interface RecommendationCardProps {
  item: RecommendationResultItem;
  rank: number;
  onSelectGraph: (standard_id: string) => void;
  onViewDetails: (standard_id: string) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  item,
  rank,
  onSelectGraph,
  onViewDetails,
}) => {
  const percentageScore = Math.round(item.score * 100);

  // Badge color based on confidence score
  const getBadgeColor = (score: number) => {
    if (score >= 0.8) return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    if (score >= 0.6) return 'bg-surface-container text-primary border-surface-container-high';
    return 'bg-amber-50 text-amber-800 border-amber-200';
  };

  return (
    <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-6 hover:border-primary transition shadow-sm relative overflow-hidden group">
      {/* Top indicator ribbon */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="w-8 h-8 rounded-DEFAULT bg-surface-container border border-surface-container-high flex items-center justify-center text-sm font-bold text-primary font-mono">
            #{rank}
          </span>
          <div>
            <h3 className="text-lg font-bold text-on-surface tracking-wide group-hover:text-primary transition flex items-center space-x-2">
              <span>{item.is_code}</span>
              <span className="text-xs bg-surface-container text-secondary px-2 py-0.5 rounded-DEFAULT font-normal font-mono">
                {item.publication_year}
              </span>
            </h3>
            <p className="text-xs text-secondary font-medium">{item.department} Department</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`text-xs font-semibold px-3 py-1 rounded-DEFAULT border ${getBadgeColor(item.score)} flex items-center space-x-1 font-mono`}>
            <Award className="w-3.5 h-3.5" />
            <span>{percentageScore}% Match</span>
          </span>
        </div>
      </div>

      <h4 className="text-base font-semibold text-on-surface mb-3 leading-snug">
        {item.title}
      </h4>

      {/* Technical reason pill */}
      <div className="bg-surface-container-low border border-surface-container-high rounded-DEFAULT p-3.5 mb-4 text-xs text-on-surface">
        <div className="flex items-center space-x-1.5 font-semibold text-primary mb-1 font-mono">
          <Cpu className="w-3.5 h-3.5" />
          <span>Technical Recommendation Rationale:</span>
        </div>
        <p className="text-secondary leading-relaxed">{item.reason}</p>
      </div>

      {/* Specifications & Testing */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs mb-5">
        <div className="bg-surface-container-low rounded-DEFAULT p-3 border border-surface-container-high">
          <span className="font-semibold text-secondary block mb-1 font-mono text-[11px]">Key Technical Specifications:</span>
          <p className="text-on-surface line-clamp-2">{item.key_specifications}</p>
        </div>

        <div className="bg-surface-container-low rounded-DEFAULT p-3 border border-surface-container-high">
          <span className="font-semibold text-secondary block mb-1 font-mono text-[11px]">Mandatory BIS Quality Tests:</span>
          <p className="text-on-surface line-clamp-2">{item.testing_requirements}</p>
        </div>
      </div>

      {/* Card Footer Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-surface-container-high text-xs">
        <div className="flex items-center space-x-2">
          {item.related_standards && item.related_standards.length > 0 && (
            <span className="text-secondary bg-surface-container-low px-2.5 py-1 rounded-DEFAULT border border-surface-container-high flex items-center space-x-1 font-mono">
              <Network className="w-3.5 h-3.5 text-primary" />
              <span>{item.related_standards.length} Related Standards</span>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => onSelectGraph(item.standard_id)}
            className="bg-surface-container hover:bg-surface-container-high text-primary border border-surface-container-high px-3.5 py-1.5 rounded-DEFAULT flex items-center space-x-1.5 font-medium transition font-mono text-xs"
          >
            <Network className="w-3.5 h-3.5" />
            <span>Interactive Graph</span>
          </button>

          <button
            onClick={() => onViewDetails(item.standard_id)}
            className="bg-primary hover:bg-primary-container text-on-primary px-3.5 py-1.5 rounded-DEFAULT flex items-center space-x-1.5 font-medium transition shadow-xs font-mono text-xs"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Full Standard</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
};
