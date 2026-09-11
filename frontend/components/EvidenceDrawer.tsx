'use client';

import React, { useState, useEffect } from 'react';
import { SourcingRecommendationItem, EvidenceRecord, SourceVerificationResponse, AuditLogEntry } from '../types';
import { getSourceVerification, submitManualVerification } from '../lib/api';
import {
  X,
  ShieldCheck,
  Award,
  AlertTriangle,
  Compass,
  FileCheck,
  Building,
  MapPin,
  ExternalLink,
  Layers,
  Calendar,
  Info,
  CheckSquare,
  Square,
  Clock,
  UserCheck,
  History
} from 'lucide-react';

interface EvidenceDrawerProps {
  source: SourcingRecommendationItem | null;
  isOpen: boolean;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  source,
  isOpen,
  onClose
}) => {
  const [verificationData, setVerificationData] = useState<SourceVerificationResponse | null>(null);
  const [loadingVerif, setLoadingVerif] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [verifiedBy, setVerifiedBy] = useState('procurement.lead@buyer.org');
  const [checks, setChecks] = useState<{ [key: string]: boolean }>({
    license_exists: false,
    product_category_matches: false,
    applicable_standard_matches: false,
    license_currently_valid: false,
    manufacturer_site_matches: false
  });
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const sourceId = source?.source_id || source?.supplier_id;

  useEffect(() => {
    if (isOpen && sourceId) {
      setLoadingVerif(true);
      getSourceVerification(sourceId)
        .then((data) => {
          setVerificationData(data);
        })
        .catch((err) => {
          console.warn('Could not load source verification workflow:', err);
        })
        .finally(() => {
          setLoadingVerif(false);
        });
    } else {
      setVerificationData(null);
      setSuccessMsg(null);
    }
  }, [isOpen, sourceId]);

  if (!isOpen || !source) return null;

  const sourceName = source.source_name || source.supplier_name || 'Industrial Sourcing Entity';
  const sourceType = source.source_type || 'UNKNOWN';
  const trustLevel = source.trust_level || 'MODERATE';
  const trustScore = Math.round((source.trust_score ?? 0.5) * 100);
  const bisStatus = verificationData?.status === 'CONFIRMED' ? 'CONFIRMED' : (source.bis_certification_status || 'REQUIRES_LIVE_VERIFICATION');
  const locStr = typeof source.location === 'object' && source.location !== null
    ? `${source.location.city}, ${source.location.state}`
    : String(source.location || source.state || 'India');

  const evidenceRecords: EvidenceRecord[] = source.evidence_records || [];

  const handleToggleCheck = (key: string) => {
    setChecks((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const allChecksConfirmed = Object.values(checks).every(Boolean);

  const handleConfirmVerification = async () => {
    if (!sourceId) return;
    setSubmitting(true);
    try {
      const res = await submitManualVerification(sourceId, {
        reference_id: verificationData?.reference_id || 'CML-MANUAL',
        action: 'CONFIRM_MANUAL_VERIFICATION',
        verified_by: verifiedBy,
        checklist_confirmed: checks,
        notes: 'Confirmed on official BIS portal (manakonline.in) by procurement buyer.'
      });
      setVerificationData(res);
      setSuccessMsg('Manual verification recorded in audit trail. Status updated to CONFIRMED.');
    } catch (e: any) {
      console.error('Failed to submit manual verification:', e);
      alert('Error recording manual verification. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const getMethodBadge = (method?: string, status?: string) => {
    const m = (method || 'REGISTRY').toUpperCase();
    const s = (status || '').toUpperCase();
    if (s === 'CONFIRMED' || m === 'MANUAL') {
      return <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-DEFAULT text-[9px] font-bold uppercase">MANUALLY VERIFIED</span>;
    }
    if (m === 'AUTOMATED') {
      return <span className="bg-purple-50 text-purple-800 border border-purple-200 px-2 py-0.5 rounded-DEFAULT text-[9px] font-bold uppercase">AUTOMATICALLY VERIFIED</span>;
    }
    if (s === 'REQUIRES_LIVE_VERIFICATION' || s === 'REQUIRES_VERIFICATION') {
      return <span className="bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-DEFAULT text-[9px] font-bold uppercase">REQUIRES VERIFICATION</span>;
    }
    if (m === 'REGISTRY') {
      return <span className="bg-surface-container text-primary border border-surface-container-high px-2 py-0.5 rounded-DEFAULT text-[9px] font-bold uppercase">REGISTRY EVIDENCE</span>;
    }
    return <span className="bg-surface-container text-secondary border border-surface-container-high px-2 py-0.5 rounded-DEFAULT text-[9px] font-bold uppercase">UNKNOWN</span>;
  };

  const getFreshnessBadge = (fresh?: string) => {
    const f = (fresh || 'UNKNOWN').toUpperCase();
    if (f === 'CURRENT') return <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 px-1.5 py-0.5 rounded-DEFAULT text-[9px] font-bold">CURRENT</span>;
    if (f === 'AGING') return <span className="bg-amber-50 text-amber-800 border border-amber-200 px-1.5 py-0.5 rounded-DEFAULT text-[9px] font-bold">AGING</span>;
    if (f === 'STALE') return <span className="bg-rose-50 text-rose-800 border border-rose-200 px-1.5 py-0.5 rounded-DEFAULT text-[9px] font-bold">STALE</span>;
    return <span className="bg-surface-container text-secondary border border-surface-container-high px-1.5 py-0.5 rounded-DEFAULT text-[9px] font-bold">UNKNOWN FRESHNESS</span>;
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-inverse-surface/60 backdrop-blur-sm flex justify-end animate-in fade-in duration-200">
      <div
        className="w-full max-w-2xl bg-surface border-l border-surface-container-high h-full shadow-2xl flex flex-col justify-between overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-surface-container-high flex items-start justify-between bg-surface-container-lowest sticky top-0 z-10 shadow-xs">
          <div className="space-y-1 pr-4">
            <div className="flex items-center space-x-2 flex-wrap gap-1">
              <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-DEFAULT bg-surface-container text-primary border border-surface-container-high flex items-center space-x-1">
                <Layers className="w-3 h-3" />
                <span>Evidence & Provenance Audit</span>
              </span>
              <span className="text-[10px] text-secondary font-mono">
                {source.source_id || source.supplier_id}
              </span>
              {getMethodBadge(verificationData?.verification_method, verificationData?.status || bisStatus)}
            </div>
            <h2 className="text-xl font-bold text-on-surface tracking-tight">{sourceName}</h2>
            <p className="text-xs text-secondary flex items-center space-x-1">
              <MapPin className="w-3.5 h-3.5 text-error" />
              <span>{locStr}</span>
              <span className="text-secondary/40">•</span>
              <span className="text-primary font-medium">{sourceType}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-DEFAULT bg-surface-container hover:bg-surface-container-high text-secondary hover:text-on-surface transition"
            aria-label="Close evidence drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 flex-1">
          {/* Trust Scorecard & BIS Status Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {/* Trust Breakdown Card */}
            <div className="bg-surface-container-lowest p-4 rounded-DEFAULT border border-surface-container-high space-y-2 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-secondary">Source Trust Rating</span>
                <span
                  className={`text-xs font-bold px-2.5 py-0.5 rounded-DEFAULT border ${
                    trustLevel === 'HIGH'
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : trustLevel === 'MODERATE'
                      ? 'bg-surface-container text-primary border-surface-container-high'
                      : 'bg-rose-50 text-rose-800 border-rose-200'
                  }`}
                >
                  {trustLevel} TRUST ({trustScore}%)
                </span>
              </div>
              {source.trust_breakdown && (
                <div className="grid grid-cols-2 gap-2 text-[10px] pt-1">
                  <div className="bg-surface-container-low p-1.5 rounded-DEFAULT border border-surface-container-high">
                    <span className="text-secondary block">Identity Assurance</span>
                    <strong className="text-emerald-700">{Math.round(source.trust_breakdown.identity_evidence * 100)}%</strong>
                  </div>
                  <div className="bg-surface-container-low p-1.5 rounded-DEFAULT border border-surface-container-high">
                    <span className="text-secondary block">BIS Documentation</span>
                    <strong className="text-amber-700">{Math.round(source.trust_breakdown.bis_evidence * 100)}%</strong>
                  </div>
                  <div className="bg-surface-container-low p-1.5 rounded-DEFAULT border border-surface-container-high">
                    <span className="text-secondary block">Freshness</span>
                    <strong className="text-primary">{Math.round(source.trust_breakdown.evidence_freshness * 100)}%</strong>
                  </div>
                  <div className="bg-surface-container-low p-1.5 rounded-DEFAULT border border-surface-container-high">
                    <span className="text-secondary block">Completeness</span>
                    <strong className="text-purple-700">{Math.round(source.trust_breakdown.evidence_completeness * 100)}%</strong>
                  </div>
                </div>
              )}
            </div>

            {/* Technical Suitability Metric */}
            <div className="bg-surface-container-lowest p-4 rounded-DEFAULT border border-surface-container-high space-y-2 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-secondary">Technical Suitability</span>
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-DEFAULT bg-surface-container text-primary border border-surface-container-high">
                  {Math.round(source.suitability_score * 100)}% MATCH
                </span>
              </div>
              <p className="text-[11px] text-secondary leading-relaxed">
                Technical alignment based on category matching, standard conformance, and physical unit specifications.
              </p>
              <div className="pt-1 text-[10px] text-secondary">
                <span className="text-secondary">Conforming IS: </span>
                <span className="font-mono text-primary font-semibold">{source.relevant_standards.join(', ')}</span>
              </div>
            </div>
          </div>

          {/* BIS Certification Status Alert */}
          {bisStatus === 'CONFIRMED' ? (
            <div className="bg-emerald-50 border border-emerald-200 rounded-DEFAULT p-4 text-xs space-y-1.5">
              <div className="flex items-center space-x-2 font-bold text-emerald-800">
                <UserCheck className="w-4 h-4 text-emerald-600" />
                <span>BIS Status: MANUALLY VERIFIED BY BUYER (CONFIRMED)</span>
              </div>
              <p className="text-secondary text-[11px] leading-relaxed">
                A procurement buyer has explicitly audited the official BIS portal (manakonline.in) and verified the active license status.
              </p>
            </div>
          ) : bisStatus === 'REQUIRES_LIVE_VERIFICATION' ? (
            <div className="bg-amber-50 border border-amber-200 rounded-DEFAULT p-4 text-xs space-y-1.5">
              <div className="flex items-center space-x-2 font-bold text-amber-800">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>BIS Status: Stored CML Evidence Available — Live Portal Verification Required</span>
              </div>
              <p className="text-secondary text-[11px] leading-relaxed">
                This entity operates documented statutory manufacturing facilities. However, BharatBuy does not access live unauthenticated BIS databases.
                <strong> Verification is required on the official BIS portal (manakonline.in) prior to buyer approval.</strong>
              </p>
            </div>
          ) : bisStatus === 'NOT_APPLICABLE' ? (
            <div className="bg-surface-container-low border border-surface-container-high rounded-DEFAULT p-4 text-xs space-y-1.5">
              <div className="flex items-center space-x-2 font-bold text-primary">
                <Compass className="w-4 h-4 text-primary" />
                <span>BIS Status: Sourcing Region — No Supplier-Level CML Attached</span>
              </div>
              <p className="text-secondary text-[11px] leading-relaxed">
                This entry represents a geographic manufacturing corridor.
                <strong> Individual supplier audit is required: buyer must inspect the specific vendor&apos;s BIS mark license.</strong>
              </p>
            </div>
          ) : (
            <div className="bg-rose-50 border border-rose-200 rounded-DEFAULT p-4 text-xs space-y-1.5">
              <div className="flex items-center space-x-2 font-bold text-rose-800">
                <AlertTriangle className="w-4 h-4 text-error" />
                <span>BIS Status: No Factory BIS License Record</span>
              </div>
              <p className="text-secondary text-[11px] leading-relaxed">
                Commercial distributor or channel partner without primary factory license. Buyer must demand original manufacturer test certificates and CML schedule.
              </p>
            </div>
          )}

          {/* Interactive Buyer Verification Workflow Section */}
          <div className="bg-surface-container-lowest border border-amber-300 rounded-DEFAULT p-5 space-y-4 shadow-xs">
            <div className="flex items-center justify-between pb-2 border-b border-surface-container-high">
              <div className="space-y-0.5">
                <h3 className="text-sm font-bold text-on-surface flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-amber-600" />
                  <span>Guided Buyer Verification Workflow</span>
                </h3>
                <p className="text-[11px] text-secondary">
                  Official BIS validation procedure for procurement compliance officers.
                </p>
              </div>
              <span className="text-[10px] text-amber-900 font-semibold uppercase px-2 py-0.5 rounded-DEFAULT bg-amber-100 border border-amber-200">
                Portal Audit Required
              </span>
            </div>

            {/* Details Box */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs bg-surface-container-low p-3 rounded-DEFAULT border border-surface-container-high">
              <div>
                <span className="text-secondary block text-[10px]">BIS License Reference:</span>
                <span className="font-mono text-amber-800 font-bold">
                  {verificationData?.reference_id || 'CM/L-CHECK REQUIRED'}
                </span>
              </div>
              <div>
                <span className="text-secondary block text-[10px]">Governing Standard:</span>
                <span className="font-mono text-primary font-semibold">
                  {verificationData?.standard_code || source.relevant_standards[0] || 'IS Standard'}
                </span>
              </div>
              <div>
                <span className="text-secondary block text-[10px]">Current Validity:</span>
                <span className="font-semibold text-on-surface">
                  {verificationData?.validity_state || 'UNKNOWN'}
                </span>
              </div>
            </div>

            {/* Official Link Button */}
            <div className="flex items-center justify-between gap-3 pt-1">
              <a
                href={verificationData?.official_verification_url || "https://www.manakonline.in/MANAK/conFormityAssessmentAction"}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-2 bg-primary hover:bg-primary-container text-on-primary px-4 py-2 rounded-DEFAULT text-xs font-semibold transition shadow-sm"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Open Official BIS Verification Portal (Manakonline)</span>
              </a>
              <span className="text-[10px] text-secondary italic">Opens official BIS Manakonline database in new tab</span>
            </div>

            {/* Mandatory Confirmation Checklist */}
            <div className="space-y-2 pt-2 border-t border-surface-container-high">
              <span className="text-[11px] font-bold text-on-surface block">
                Buyer Must Confirm on Official Portal:
              </span>
              <div className="space-y-1.5 text-xs">
                <label className="flex items-center space-x-2 cursor-pointer text-on-surface hover:text-primary p-2 rounded-DEFAULT bg-surface-container-low hover:bg-surface-container transition-colors">
                  <input
                    type="checkbox"
                    checked={checks.license_exists}
                    onChange={() => handleToggleCheck('license_exists')}
                    className="rounded-DEFAULT border-outline-variant text-primary focus:ring-0 accent-primary"
                  />
                  <span>1. License / reference exists in official BIS database</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer text-on-surface hover:text-primary p-2 rounded-DEFAULT bg-surface-container-low hover:bg-surface-container transition-colors">
                  <input
                    type="checkbox"
                    checked={checks.product_category_matches}
                    onChange={() => handleToggleCheck('product_category_matches')}
                    className="rounded-DEFAULT border-outline-variant text-primary focus:ring-0 accent-primary"
                  />
                  <span>2. Product category matches certified manufacturing scope</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer text-on-surface hover:text-primary p-2 rounded-DEFAULT bg-surface-container-low hover:bg-surface-container transition-colors">
                  <input
                    type="checkbox"
                    checked={checks.applicable_standard_matches}
                    onChange={() => handleToggleCheck('applicable_standard_matches')}
                    className="rounded-DEFAULT border-outline-variant text-primary focus:ring-0 accent-primary"
                  />
                  <span>3. Applicable Indian Standard matches cited IS specification</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer text-on-surface hover:text-primary p-2 rounded-DEFAULT bg-surface-container-low hover:bg-surface-container transition-colors">
                  <input
                    type="checkbox"
                    checked={checks.license_currently_valid}
                    onChange={() => handleToggleCheck('license_currently_valid')}
                    className="rounded-DEFAULT border-outline-variant text-primary focus:ring-0 accent-primary"
                  />
                  <span>4. License is currently active, valid, and unexpired</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer text-on-surface hover:text-primary p-2 rounded-DEFAULT bg-surface-container-low hover:bg-surface-container transition-colors">
                  <input
                    type="checkbox"
                    checked={checks.manufacturer_site_matches}
                    onChange={() => handleToggleCheck('manufacturer_site_matches')}
                    className="rounded-DEFAULT border-outline-variant text-primary focus:ring-0 accent-primary"
                  />
                  <span>5. Manufacturer name and factory site address match supplier</span>
                </label>
              </div>
            </div>

            {/* Officer Affirmation & Action */}
            <div className="pt-2 border-t border-surface-container-high space-y-3">
              <div className="flex items-center space-x-2">
                <span className="text-[11px] text-secondary flex-shrink-0">Verified By:</span>
                <input
                  type="text"
                  value={verifiedBy}
                  onChange={(e) => setVerifiedBy(e.target.value)}
                  placeholder="Officer email or name"
                  className="bg-surface-container-lowest border border-outline-variant text-on-surface text-xs rounded-DEFAULT px-3 py-1.5 flex-1 focus:border-primary focus:outline-none font-mono"
                />
              </div>

              {successMsg && (
                <div className="space-y-1.5">
                  <div className="p-2.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-DEFAULT text-xs flex items-center space-x-2">
                    <CheckSquare className="w-4 h-4 flex-shrink-0 text-emerald-600" />
                    <span>{successMsg}</span>
                  </div>
                  <div className="p-2 bg-amber-50 border border-amber-200 text-amber-900 rounded-DEFAULT text-[11px] font-medium flex items-center space-x-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                    <span>Buyer confirmation recorded manually. BharatBuy did not perform automated BIS verification.</span>
                  </div>
                </div>
              )}

              <button
                disabled={!allChecksConfirmed || submitting}
                onClick={handleConfirmVerification}
                className={`w-full py-2.5 rounded-DEFAULT text-xs font-bold transition flex items-center justify-center space-x-2 ${
                  allChecksConfirmed && !submitting
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm'
                    : 'bg-surface-container text-secondary cursor-not-allowed border border-surface-container-high'
                }`}
              >
                <UserCheck className="w-4 h-4" />
                <span>
                  {submitting
                    ? 'Recording Audit Entry...'
                    : allChecksConfirmed
                    ? 'Record Buyer Verification (Mark as Confirmed)'
                    : 'Confirm All 5 Checkpoints Above to Record Verification'}
                </span>
              </button>
            </div>
          </div>

          {/* Traceable Claim -> Evidence Chain */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-1 border-b border-surface-container-high">
              <h3 className="text-sm font-bold text-on-surface flex items-center space-x-2">
                <FileCheck className="w-4 h-4 text-emerald-600" />
                <span>Traceable Procurement Claims & Evidence Chain ({evidenceRecords.length})</span>
              </h3>
              <span className="text-[10px] text-secondary font-mono">Zero-Fabrication Audit</span>
            </div>

            {evidenceRecords.length > 0 ? (
              <div className="space-y-3">
                {evidenceRecords.map((ev, idx) => {
                  const isConfirmed = ev.verification_status === 'CONFIRMED' || ev.verification_method === 'MANUAL';
                  const isPartial = ev.verification_status === 'PARTIAL';
                  const isRequiresLive = ev.verification_status === 'REQUIRES_LIVE_VERIFICATION' || ev.verification_status === 'REQUIRES_VERIFICATION';
                  const isDocumented = ev.verification_status === 'VERIFIED';
                  return (
                    <div
                      key={idx}
                      className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-4 space-y-2 text-xs shadow-xs"
                    >
                      {/* Top Claim & Badges */}
                      <div className="flex items-start justify-between gap-2 flex-wrap">
                        <div className="space-y-1">
                          <div className="flex items-center space-x-1.5">
                            <span className="text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-DEFAULT bg-surface-container text-on-surface border border-surface-container-high">
                              {ev.evidence_type}
                            </span>
                            {getMethodBadge(ev.verification_method, ev.verification_status)}
                            {getFreshnessBadge(ev.freshness_state)}
                          </div>
                          <h4 className="font-semibold text-on-surface">{ev.title}</h4>
                        </div>
                        <span
                          className={`text-[9px] font-bold px-2 py-0.5 rounded-DEFAULT border uppercase ${
                            isConfirmed
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : isDocumented
                              ? 'bg-surface-container text-primary border-surface-container-high'
                              : isPartial || isRequiresLive
                              ? 'bg-amber-50 text-amber-800 border-amber-200'
                              : 'bg-rose-50 text-rose-800 border-rose-200'
                          }`}
                        >
                          {isConfirmed ? 'CONFIRMED (LIVE)' : isDocumented ? 'DOCUMENTED RECORD' : ev.verification_status}
                        </span>
                      </div>

                      {/* Supports Claim */}
                      <div className="bg-surface-container-low p-2.5 rounded-DEFAULT border border-surface-container-high space-y-1">
                        <strong className="text-[10px] text-amber-800 uppercase tracking-wide block">
                          Traceable Claim:
                        </strong>
                        <p className="text-[11px] text-on-surface leading-relaxed font-medium">
                          &ldquo;{ev.supports_claim || ev.claim}&rdquo;
                        </p>
                      </div>

                      {/* Description & Evidence */}
                      <p className="text-secondary text-[11px] leading-relaxed">
                        {ev.description}
                      </p>

                      {/* Metadata Footer */}
                      <div className="flex flex-wrap items-center justify-between pt-2 border-t border-surface-container-high text-[10px] text-secondary gap-2">
                        <span className="flex items-center space-x-1">
                          <Building className="w-3 h-3 text-secondary" />
                          <span>Authority: <strong className="text-on-surface">{ev.source}</strong></span>
                        </span>
                        {ev.reference_id && (
                          <span className="font-mono text-secondary">
                            Ref: {ev.reference_id}
                          </span>
                        )}
                        {ev.verified_at && (
                          <span className="flex items-center space-x-1 text-emerald-700">
                            <Clock className="w-3 h-3" />
                            <span>Verified: {ev.verified_at}</span>
                          </span>
                        )}
                        {ev.retrieved_at && !ev.verified_at && (
                          <span className="flex items-center space-x-1 text-secondary">
                            <Calendar className="w-3 h-3" />
                            <span>Audited: {ev.retrieved_at}</span>
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-surface-container-low p-4 rounded-DEFAULT border border-surface-container-high text-center text-xs text-secondary">
                No explicit evidence records attached.
              </div>
            )}
          </div>

          {/* Audit Trail History */}
          {verificationData?.audit_trail && verificationData.audit_trail.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-surface-container-high">
              <h4 className="text-xs font-bold text-on-surface flex items-center space-x-1.5">
                <History className="w-3.5 h-3.5 text-primary" />
                <span>Verification Audit Trail ({verificationData.audit_trail.length})</span>
              </h4>
              <div className="space-y-1.5">
                {verificationData.audit_trail.map((log: AuditLogEntry, lIdx: number) => (
                  <div key={lIdx} className="bg-surface-container-low p-2.5 rounded-DEFAULT border border-surface-container-high text-[11px] space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-amber-800">{log.action}</span>
                      <span className="text-[9px] text-secondary font-mono">{log.timestamp}</span>
                    </div>
                    <div className="text-secondary flex items-center space-x-2">
                      <span>Actor: <strong className="text-on-surface">{log.actor}</strong></span>
                      <span className="text-secondary/40">•</span>
                      <span>Method: <strong className="text-on-surface">{log.verification_method}</strong></span>
                    </div>
                    {log.notes && <p className="text-secondary text-[10px] italic">{log.notes}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer Disclaimer & Actions */}
        <div className="p-4 border-t border-surface-container-high bg-surface-container-lowest space-y-2">
          <div className="flex items-start space-x-2 text-[10px] text-secondary">
            <Info className="w-3.5 h-3.5 text-primary flex-shrink-0 mt-0.5" />
            <span>
              <strong>Statutory Disclosure:</strong> BharatBuy provides evidence-backed procurement intelligence. Certification validity and supplier eligibility should be independently verified before buyer approval.
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-full py-2.5 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-DEFAULT text-xs font-semibold transition border border-surface-container-high"
          >
            Close Evidence Audit
          </button>
        </div>
      </div>
    </div>
  );
};
