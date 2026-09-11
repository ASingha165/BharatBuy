'use client';

import React, { useState } from 'react';
import { SourcingRecommendationItem } from '../types';
import { EvidenceDrawer } from './EvidenceDrawer';
import {
  Building2,
  MapPin,
  CheckCircle,
  ShieldCheck,
  AlertTriangle,
  ArrowUpRight,
  Award,
  Compass,
  FileText,
  ShieldAlert
} from 'lucide-react';

interface SourcingRecommendationsProps {
  recommendations: SourcingRecommendationItem[];
  selectedHubId?: string | null;
  onSelectHub?: (id: string) => void;
}

export const SourcingRecommendations: React.FC<SourcingRecommendationsProps> = ({
  recommendations,
  selectedHubId,
  onSelectHub
}) => {
  const [activeEvidenceSource, setActiveEvidenceSource] = useState<SourcingRecommendationItem | null>(null);

  const getLocationString = (rec: SourcingRecommendationItem): string => {
    if (typeof rec.location === 'object' && rec.location !== null) {
      return `${rec.location.city}, ${rec.location.state}`;
    }
    return String(rec.location || rec.state || 'India');
  };

  const getSourceId = (rec: SourcingRecommendationItem): string => {
    return rec.source_id || rec.supplier_id || 'source';
  };

  const getSourceName = (rec: SourcingRecommendationItem): string => {
    return rec.source_name || rec.supplier_name || 'Industrial Source';
  };

  return (
    <div id="workflow-evidence" className="scroll-mt-24 space-y-4">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-surface-container-high">
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-primary" />
          <h3 className="text-base sm:text-lg font-bold text-on-surface font-mono uppercase tracking-tight">
            Eligible Sourcing Options & Manufacturing Entities ({recommendations.length})
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="bg-surface-container text-on-surface border border-surface-container-high px-2.5 py-0.5 rounded-DEFAULT flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Zero-Fabrication Data Registry</span>
          </span>
        </div>
      </div>

      {/* Sourcing Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {recommendations.map((rec) => {
          const sId = getSourceId(rec);
          const isSelected = sId === selectedHubId;
          const locStr = getLocationString(rec);
          const trustLvl = rec.trust_level || 'MODERATE';
          const suitabilityPct = Math.round(rec.suitability_score * 100);

          const vStat = (rec.verification_status || '').toUpperCase();
          const pLabel = (rec.provenance_label || '').toUpperCase();
          const sType = (rec.source_type || '').toUpperCase();
          const isPSU = getSourceName(rec).toLowerCase().includes('sail') || getSourceName(rec).toLowerCase().includes('bhel') || getSourceName(rec).toLowerCase().includes('iti') || getSourceName(rec).toLowerCase().includes('central electronics') || getSourceName(rec).toLowerCase().includes('cement corporation');

          // 1. Current Live / Buyer Verified (Emerald ONLY)
          const isBuyerVerified = pLabel === 'BUYER_VERIFIED' || vStat === 'CONFIRMED' || rec.bis_certification_status === 'CONFIRMED';

          // 2. Region Only (Blue)
          const isRegion = sType === 'SOURCING_REGION' || vStat === 'REGION_ONLY' || pLabel === 'REGION_ONLY';

          // 3. Unverified Commercial Source (Rose)
          const isUnverified = sType === 'SUPPLIER' || sType === 'DISTRIBUTOR' || vStat === 'UNVERIFIED' || vStat === 'REQUIRES_VENDOR_VERIFICATION' || rec.bis_certification_status === 'NO_EVIDENCE';

          // 4. Requires Live Verification (Amber - all static PSUs, manufacturers, and CML records)
          const isRequiresLiveVerification = !isBuyerVerified && !isRegion && !isUnverified;

          return (
            <div
              key={sId}
              onClick={() => onSelectHub && onSelectHub(sId)}
              className={`rounded-DEFAULT p-4 sm:p-5 cursor-pointer transition shadow-sm space-y-3 relative overflow-hidden group border ${
                isSelected
                  ? 'border-primary ring-1 ring-primary/20 bg-surface-container-low'
                  : isBuyerVerified
                  ? 'bg-surface-container-lowest border-emerald-200 hover:border-emerald-400'
                  : isRequiresLiveVerification
                  ? 'bg-surface-container-lowest border-amber-200 hover:border-amber-400'
                  : isRegion
                  ? 'bg-surface-container-lowest border-surface-container-high hover:border-primary'
                  : 'bg-surface-container-lowest border-rose-200 hover:border-rose-400'
              }`}
            >
              {/* Vertical Indicator Accent */}
              <div
                className={`absolute left-0 top-0 bottom-0 w-1 ${
                  isBuyerVerified
                    ? 'bg-emerald-500'
                    : isRequiresLiveVerification
                    ? 'bg-amber-500'
                    : isRegion
                    ? 'bg-primary'
                    : 'bg-error'
                }`}
              />

              {/* Header: Type Badge & Location */}
              <div className="flex items-start justify-between gap-3 pl-1">
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {isBuyerVerified ? (
                      <span className="text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-DEFAULT font-mono font-bold uppercase flex items-center gap-1">
                        <CheckCircle className="w-3 h-3 text-emerald-600" />
                        <span>Buyer Verified (Live)</span>
                      </span>
                    ) : isRequiresLiveVerification ? (
                      <span className="text-[10px] bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-DEFAULT font-mono font-bold uppercase flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3 text-amber-600" />
                        <span>Requires Live Verification</span>
                      </span>
                    ) : isRegion ? (
                      <span className="text-[10px] bg-surface-container text-primary border border-surface-container-high px-2 py-0.5 rounded-DEFAULT font-mono font-bold uppercase flex items-center gap-1">
                        <Compass className="w-3 h-3 text-primary" />
                        <span>Region Only</span>
                      </span>
                    ) : (
                      <span className="text-[10px] bg-rose-50 text-rose-800 border border-rose-200 px-2 py-0.5 rounded-DEFAULT font-mono font-bold uppercase flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3 text-error" />
                        <span>Unverified Source</span>
                      </span>
                    )}

                    {/* Secondary Entity Badge */}
                    <span className="text-[9px] bg-surface-container text-on-surface border border-surface-container-high px-1.5 py-0.5 rounded-DEFAULT font-mono font-semibold uppercase">
                      {isPSU ? 'Central PSU' : sType === 'MANUFACTURER' ? 'Manufacturer' : isRegion ? 'Cluster' : 'Distributor'}
                    </span>

                    {rec.provenance_label && (
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-DEFAULT font-mono font-bold uppercase border ${
                        pLabel === 'BUYER_VERIFIED'
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                          : pLabel === 'REGION_ONLY'
                          ? 'bg-surface-container text-primary border-surface-container-high'
                          : pLabel === 'DEMO_DATA'
                          ? 'bg-purple-50 text-purple-800 border-purple-200'
                          : pLabel === 'SUPPLIER_DECLARATION'
                          ? 'bg-rose-50 text-rose-800 border-rose-200'
                          : 'bg-amber-50 text-amber-800 border-amber-200'
                      }`}>
                        {rec.provenance_label.replace(/_/g, ' ')}
                      </span>
                    )}

                    <span className="text-[10px] text-secondary font-mono">
                      {typeof rec.location === 'object' ? rec.location.state : rec.state}
                    </span>
                  </div>

                  <h4 className="text-base font-bold text-on-surface group-hover:text-primary transition truncate">
                    {getSourceName(rec)}
                  </h4>

                  <p className="text-xs text-secondary flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-error shrink-0" />
                    <span className="truncate">{locStr}</span>
                  </p>
                </div>

                {/* Suitability & Trust Badges */}
                <div className="text-right flex flex-col items-end space-y-1 shrink-0">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-DEFAULT border bg-surface-container text-primary border-surface-container-high">
                    {suitabilityPct}% Suitability
                  </span>
                  <span
                    className={`font-mono text-[10px] font-semibold px-2 py-0.5 rounded-DEFAULT border uppercase ${
                      trustLvl === 'HIGH'
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                        : trustLvl === 'MODERATE'
                        ? 'bg-surface-container text-primary border-surface-container-high'
                        : 'bg-rose-50 text-rose-800 border-rose-200'
                    }`}
                  >
                    Trust: {trustLvl}
                  </span>
                </div>
              </div>

              {/* BIS Status Box */}
              <div className="text-xs rounded-DEFAULT p-2.5 pl-3 border border-surface-container-high bg-surface-container-low/70">
                {isBuyerVerified ? (
                  <div className="space-y-0.5 text-emerald-900">
                    <div className="flex items-center gap-1.5 font-bold font-mono text-[11px] text-emerald-800">
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Live Buyer Verification Confirmed</span>
                    </div>
                    <p className="text-[10px] text-secondary leading-snug">
                      Operational license validity explicitly confirmed on official BIS portal (manakonline.in) by procurement officer.
                    </p>
                  </div>
                ) : isRegion ? (
                  <div className="space-y-0.5 text-on-surface">
                    <div className="flex items-center gap-1.5 font-bold font-mono text-[11px] text-primary">
                      <Compass className="w-3.5 h-3.5 text-primary" />
                      <span>Sourcing Region (Cluster Only)</span>
                    </div>
                    <p className="text-[10px] text-secondary leading-snug">
                      Geographic manufacturing corridor. No supplier-level CML attached. Specific factory site license must be audited prior to buyer approval.
                    </p>
                  </div>
                ) : isRequiresLiveVerification ? (
                  <div className="space-y-0.5 text-amber-900">
                    <div className="flex items-center gap-1.5 font-bold font-mono text-[11px] text-amber-800">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                      <span>Requires Live Verification (Static Record on File)</span>
                    </div>
                    <p className="text-[10px] text-secondary leading-snug">
                      Static factory record / CML schedule on file. Current operational validity must be audited on official BIS portal (<em>manakonline.in</em>) prior to buyer approval.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-0.5 text-rose-900">
                    <div className="flex items-center gap-1.5 font-bold font-mono text-[11px] text-error">
                      <ShieldAlert className="w-3.5 h-3.5 text-error" />
                      <span>Unverified Source (Vendor Audit Required)</span>
                    </div>
                    <p className="text-[10px] text-secondary leading-snug">
                      Commercial channel distributor without direct primary factory license. Buyer must demand original manufacturer test certificates and CML schedule.
                    </p>
                  </div>
                )}
              </div>

              {/* Relevant Standard & Scope */}
              <div className="text-[11px] text-secondary flex items-center justify-between pt-1 pl-1">
                <span className="truncate">
                  <strong className="text-on-surface">Standards: </strong>
                  <span className="font-mono text-primary font-semibold">
                    {rec.relevant_standards.join(', ')}
                  </span>
                </span>
                <span className="text-[10px] text-secondary font-mono truncate ml-2">
                  {rec.supported_items.slice(0, 2).join(', ')}
                </span>
              </div>

              {/* Action Bar */}
              <div className="flex items-center justify-between pt-2 border-t border-surface-container-high pl-1">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveEvidenceSource(rec);
                  }}
                  className="px-3 py-1 rounded-DEFAULT bg-primary hover:bg-primary-container text-on-primary font-mono text-xs font-semibold transition flex items-center gap-1.5 shadow-sm"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>INSPECT EVIDENCE VAULT</span>
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (onSelectHub) onSelectHub(sId);
                    const mapEl = document.getElementById('sourcing-map-container');
                    if (mapEl) {
                      mapEl.scrollIntoView({ behavior: 'smooth' });
                    }
                  }}
                  className="text-secondary hover:text-on-surface transition flex items-center gap-1 text-[11px] font-mono cursor-pointer"
                >
                  <Compass className="w-3.5 h-3.5 text-primary" />
                  <span>Map & Directions</span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-primary" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Slide-over Evidence Drawer */}
      <EvidenceDrawer
        source={activeEvidenceSource}
        isOpen={Boolean(activeEvidenceSource)}
        onClose={() => setActiveEvidenceSource(null)}
      />
    </div>
  );
};
