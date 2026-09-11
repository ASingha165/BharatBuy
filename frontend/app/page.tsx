'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { SearchBox } from '../components/SearchBox';
import { RecommendationCard } from '../components/RecommendationCard';
import { StandardsGraph } from '../components/StandardsGraph';
import { StandardDetails } from '../components/StandardDetails';
import { LoadingState } from '../components/LoadingState';
import { ProcurementAnalysisForm } from '../components/ProcurementAnalysisForm';
import { PackageEvaluationSummary } from '../components/PackageEvaluationSummary';
import { ItemEvaluationList } from '../components/ItemEvaluationList';
import { SourcingRecommendations } from '../components/SourcingRecommendations';
import { SourcingMap } from '../components/SourcingMap';
import { WorkflowNavigation } from '../components/WorkflowNavigation';
import { getRecommendations, analyzeProcurement } from '../lib/api';
import { useAuth } from '../lib/auth-context';
import {
  RecommendationResponse,
  ProcurementAnalysisRequest,
  ProcurementAnalysisResponse
} from '../types';
import {
  Shield,
  Layers,
  Bot,
  AlertCircle,
  FileSearch,
  Building2,
  Compass,
  ArrowRight,
  BookOpen,
  Lock
} from 'lucide-react';

export default function Home() {
  const { user, loading: isAuthLoading, authState } = useAuth();
  const router = useRouter();

  // Mode: 'procurement' (Multi-item package) vs 'search' (Single IS query)
  const [activeTab, setActiveTab] = useState<'procurement' | 'search'>('procurement');

  // Single Standard Search State
  const [searchData, setSearchData] = useState<RecommendationResponse | null>(null);
  const [isSearchLoading, setIsSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Authentication protection redirect
  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push('/signin');
    }
  }, [user, isAuthLoading, router]);

  // Multi-Item Procurement Analysis State
  const [procurementData, setProcurementData] = useState<ProcurementAnalysisResponse | null>(null);
  const [isProcurementLoading, setIsProcurementLoading] = useState(false);
  const [procurementError, setProcurementError] = useState<string | null>(null);
  const [selectedHubId, setSelectedHubId] = useState<string | null>(null);

  // Shared Modals / Visualizers
  const [selectedGraphStandard, setSelectedGraphStandard] = useState<string | null>(null);
  const [selectedDetailStandard, setSelectedDetailStandard] = useState<string | null>(null);

  // Single Search Handler
  const handleSearch = async (query: string, topK: number) => {
    if (!user || authState !== 'SIGNED_IN') {
      setSearchError('Authentication required. Please sign in with your enterprise credentials to access recommendations.');
      router.push('/signin');
      return;
    }
    setIsSearchLoading(true);
    setSearchError(null);
    try {
      const res = await getRecommendations(query, topK);
      setSearchData(res);
      if (res.results && res.results.length > 0) {
        setSelectedGraphStandard(res.results[0].standard_id);
      }
    } catch (err: any) {
      setSearchError(err.response?.data?.detail || 'Failed to retrieve recommendations from backend API.');
    } finally {
      setIsSearchLoading(false);
    }
  };

  // Procurement Package Handler
  const handleProcurementSubmit = async (request: ProcurementAnalysisRequest) => {
    if (!user || authState !== 'SIGNED_IN') {
      setProcurementError('Authentication required. Please sign in with your enterprise credentials to analyze procurement packages.');
      router.push('/signin');
      return;
    }
    setIsProcurementLoading(true);
    setProcurementError(null);
    try {
      const res = await analyzeProcurement(request);
      setProcurementData(res);
      if (res.items && res.items.length > 0 && res.items[0].primary_standard) {
        setSelectedGraphStandard(res.items[0].primary_standard.standard_id);
      }
      if (res.recommendations && res.recommendations.length > 0) {
        const first = res.recommendations[0];
        setSelectedHubId(first.source_id || first.supplier_id || null);
      }
      setIsProcurementLoading(false);
      // Smooth scroll down to results
      setTimeout(() => {
        const resultsEl = document.getElementById('procurement-results-view');
        if (resultsEl) {
          resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 200);

      // Persist procurement request in Cloud Firestore for authenticated user
      if (user && res.request_id) {
        void import('../lib/firestore-service').then(({ recordProcurementRequestFirestore }) =>
          recordProcurementRequestFirestore(
            { uid: user.id },
            {
              requestId: res.request_id,
              organizationName: request.company,
              requirements: request.requirements || request.description,
              normalizedMetadata: {
                total_items: res.items?.length || 0,
                overall_readiness_score: res.package_evaluation?.overall_readiness_score,
                decision_status: res.package_evaluation?.decision_summary?.decision_status || 'ANALYZED'
              },
              status: 'COMPLETED',
              items: res.items?.map((it: any) => ({
                item_id: it.item_id,
                product_type: it.product_type,
                specifications: it.specifications,
                matched_standards: it.matched_standards?.map((s: any) => s.is_code),
                compliance_status: it.compliance_status
              }))
            }
          )
        ).catch((fsErr) => {
          console.warn('[FIRESTORE] Client request record note:', fsErr);
        });
      }
    } catch (err: any) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (!err.response) {
        // Network error — backend not reachable at all
        setProcurementError('Unable to connect to the procurement engine. Please verify the backend server is running on port 8000.');
      } else if (status === 400 || status === 422) {
        // Validation error from backend
        const msg = typeof detail === 'string' ? detail : 'Please check the procurement information and try again.';
        setProcurementError(msg);
      } else if (status === 401) {
        setProcurementError('Your session has expired. Please sign in again.');
        router.push('/signin');
      } else if (status === 403) {
        setProcurementError('You do not have permission to perform this analysis.');
      } else if (status === 500) {
        setProcurementError('Procurement analysis encountered a server error. Please try again or contact support.');
      } else {
        // Other HTTP errors — surface the detail without exposing stack traces
        const msg = typeof detail === 'string' ? detail : `Analysis request failed (HTTP ${status ?? 'unknown'}).`;
        setProcurementError(msg);
      }
    } finally {
      setIsProcurementLoading(false);
    }
  };

  if (isAuthLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <LoadingState />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-md mx-auto px-4 py-20 text-center">
        <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-6 space-y-4 shadow-sm">
          <div className="w-10 h-10 rounded-DEFAULT bg-surface-container border border-surface-container-high flex items-center justify-center mx-auto text-primary">
            <Lock className="w-5 h-5" />
          </div>
          <h2 className="text-base font-semibold text-on-surface">Enterprise Access Required</h2>
          <p className="text-xs text-secondary leading-relaxed">
            Please sign in with your enterprise credentials to access the BharatBuy Procurement Workbench.
          </p>
          <button
            onClick={() => router.push('/signin')}
            className="w-full py-2.5 px-4 bg-primary hover:bg-primary-container text-on-primary text-xs font-semibold rounded-DEFAULT transition-colors flex items-center justify-center gap-2 font-mono"
          >
            <span>Go to Sign In</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Hero Banner (Stitch Industrial Precision) */}
      <div className="relative overflow-hidden rounded-DEFAULT bg-surface-container-lowest border border-surface-container-high p-6 sm:p-8 shadow-sm">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 bg-surface-container border border-surface-container-high rounded-DEFAULT px-2.5 py-0.5 text-[11px] font-mono font-semibold text-primary shadow-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>BHARATBUY / AI PROCUREMENT INTELLIGENCE</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-on-surface tracking-tight leading-snug">
            Indian Standards Intelligence &amp; Sourcing Engine
          </h1>

          <p className="text-secondary text-xs sm:text-sm leading-relaxed max-w-2xl">
            Evaluate entire procurement packages against <strong className="text-on-surface font-mono">550+ Indian Standards (BIS)</strong>, verify mandatory conformity schemes (ISI Mark / CRS), compute statutory compliance, and discover verified manufacturing entities across India.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono text-secondary border-t border-surface-container-high pt-3 mt-2">
            <div className="flex items-center gap-2">
              <Shield className="w-3.5 h-3.5 text-primary shrink-0" />
              <span>559 BIS Standards Indexed</span>
            </div>
            <div className="flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span>Hybrid BM25 + Vector Retrieval</span>
            </div>
            <div className="flex items-center gap-2">
              <Bot className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>Grounded AI Anti-Hallucination</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Switcher Tabs */}
      <div className="flex items-center p-1 bg-surface-container border border-surface-container-high rounded-DEFAULT max-w-xl mx-auto shadow-xs">
        <button
          onClick={() => setActiveTab('procurement')}
          className={`flex-1 py-2 px-3 rounded-DEFAULT text-xs font-mono font-bold flex items-center justify-center gap-2 transition ${
            activeTab === 'procurement'
              ? 'bg-surface-container-lowest text-primary shadow-xs border border-surface-container-high'
              : 'text-secondary hover:text-on-surface'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span>Procurement Package Analysis</span>
        </button>

        <button
          onClick={() => setActiveTab('search')}
          className={`flex-1 py-2 px-3 rounded-DEFAULT text-xs font-mono font-bold flex items-center justify-center gap-2 transition ${
            activeTab === 'search'
              ? 'bg-surface-container-lowest text-primary shadow-xs border border-surface-container-high'
              : 'text-secondary hover:text-on-surface'
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          <span>Single Standard Search &amp; Graph</span>
        </button>
      </div>

      {/* ======================================================== */}
      {/* TAB 1: STARTUP PROCUREMENT PACKAGE ANALYSIS VIEW */}
      {/* ======================================================== */}
      {activeTab === 'procurement' && (
        <div className="space-y-6">
          {/* Primary 9-Step Audit Pipeline Navigation */}
          <WorkflowNavigation
            hasResults={!!procurementData}
            synthesisType={procurementData?.explanation?.synthesis_type}
          />

          {/* 1. Requirements Input Form */}
          <div id="workflow-requirements" className="scroll-mt-24">
            <ProcurementAnalysisForm
              onSubmit={handleProcurementSubmit}
              isLoading={isProcurementLoading}
            />
          </div>

          {/* Error Banner */}
          {procurementError && (
            <div className="bg-rose-50 border border-rose-200 rounded-DEFAULT p-3.5 flex items-center gap-3 text-rose-800 text-xs shadow-xs">
              <AlertCircle className="w-4 h-4 text-error shrink-0" />
              <div>
                <span className="font-bold block font-mono">Analysis Error</span>
                <span>{procurementError}</span>
              </div>
            </div>
          )}

          {/* Loading Animation */}
          {isProcurementLoading && <LoadingState />}

          {/* Results Container */}
          {!isProcurementLoading && procurementData && (
            <div id="procurement-results-view" className="space-y-6 pt-2">
              {/* Package Evaluation (Normalization, Explanation, Buyer Approval) */}
              <PackageEvaluationSummary
                evaluation={procurementData.package_evaluation}
                explanation={procurementData.explanation}
                company={procurementData.company}
              />

              {/* 3. Interactive Standards Knowledge Graph */}
              {selectedGraphStandard && (
                <div id="workflow-standards" className="scroll-mt-24">
                  <StandardsGraph
                    standardId={selectedGraphStandard}
                    onSelectStandard={(id) => {
                      setSelectedGraphStandard(id);
                      setSelectedDetailStandard(id);
                    }}
                  />
                </div>
              )}

              {/* 4. Item-by-Item Standards & Compliance Matrix */}
              <ItemEvaluationList
                items={procurementData.items}
                onSelectStandard={(id) => setSelectedDetailStandard(id)}
                onSelectGraph={(id) => {
                  setSelectedGraphStandard(id);
                  const graphEl = document.getElementById('workflow-standards');
                  if (graphEl) {
                    graphEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  }
                }}
              />

              {/* 5. Leaflet Sourcing Map */}
              {procurementData.map_points && procurementData.map_points.length > 0 && (
                <div id="workflow-sourcing" className="scroll-mt-24">
                  <SourcingMap
                    points={procurementData.map_points}
                    selectedPointId={selectedHubId}
                    onSelectPoint={(id) => setSelectedHubId(id)}
                  />
                </div>
              )}

              {/* 6. Sourcing Hubs & Supplier Recommendations (Evidence) */}
              <SourcingRecommendations
                recommendations={procurementData.recommendations}
                selectedHubId={selectedHubId}
                onSelectHub={(id) => {
                  setSelectedHubId(id);
                  const mapEl = document.getElementById('workflow-sourcing');
                  if (mapEl) {
                    mapEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  }
                }}
              />
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 2: SINGLE STANDARD SEARCH & GRAPH VIEW */}
      {/* ======================================================== */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          <SearchBox onSearch={handleSearch} isLoading={isSearchLoading} />

          {searchError && (
            <div className="bg-rose-50 border border-rose-200 rounded-DEFAULT p-3.5 flex items-center gap-3 text-rose-800 text-xs shadow-xs">
              <AlertCircle className="w-4 h-4 text-error shrink-0" />
              <div>
                <span className="font-bold block font-mono">Search Error</span>
                <span>{searchError}</span>
              </div>
            </div>
          )}

          {isSearchLoading && <LoadingState />}

          {!isSearchLoading && searchData && (
            <div className="space-y-6">
              {/* Grounded Gemini Technical Explanation */}
              {searchData.explanation && (
                <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-5 shadow-sm space-y-2">
                  <div className="flex items-center gap-2 font-bold text-on-surface text-xs font-mono pb-2 border-b border-surface-container-high">
                    <Bot className="w-4 h-4 text-primary" />
                    <span>Grounded AI Technical Explanation</span>
                    <span className="text-[10px] bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-DEFAULT border border-emerald-200 font-normal font-mono">
                      Deterministic Match
                    </span>
                  </div>
                  <div className="text-xs sm:text-sm text-secondary leading-relaxed whitespace-pre-line font-sans">
                    {searchData.explanation}
                  </div>
                </div>
              )}

              {/* Interactive React Flow Knowledge Graph */}
              {selectedGraphStandard && (
                <StandardsGraph
                  standardId={selectedGraphStandard}
                  onSelectStandard={(id) => {
                    setSelectedGraphStandard(id);
                    setSelectedDetailStandard(id);
                  }}
                />
              )}

              {/* Recommendations Header */}
              <div className="flex items-center justify-between pb-2 border-b border-surface-container-high">
                <h2 className="text-base font-bold text-on-surface flex items-center gap-2 font-mono">
                  <BookOpen className="w-4 h-4 text-primary" />
                  <span>Recommended Indian Standards ({searchData.total_found})</span>
                </h2>
                <span className="text-xs text-secondary font-mono">
                  Query: &quot;<span className="text-on-surface italic">{searchData.query}</span>&quot;
                </span>
              </div>

              {/* Cards List */}
              {searchData.results.length > 0 ? (
                <div className="space-y-3">
                  {searchData.results.map((item, idx) => (
                    <RecommendationCard
                      key={item.standard_id}
                      item={item}
                      rank={idx + 1}
                      onSelectGraph={(id) => {
                        setSelectedGraphStandard(id);
                        window.scrollTo({ top: 700, behavior: 'smooth' });
                      }}
                      onViewDetails={(id) => setSelectedDetailStandard(id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-8 text-center text-secondary space-y-2 font-mono shadow-xs">
                  <FileSearch className="w-8 h-8 text-secondary/40 mx-auto" />
                  <h3 className="text-sm font-semibold text-on-surface">No Matching Indian Standards Found</h3>
                  <p className="text-xs text-secondary max-w-md mx-auto">
                    Try refining your query terms (e.g., &quot;1.1 kV electrical cables&quot;, &quot;Portland cement&quot;, or &quot;structural steel TMT bars&quot;).
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Shared Full Details Modal/Drawer */}
      {selectedDetailStandard && (
        <StandardDetails
          standardId={selectedDetailStandard}
          onClose={() => setSelectedDetailStandard(null)}
          onSelectRelated={(id) => {
            setSelectedDetailStandard(id);
            setSelectedGraphStandard(id);
          }}
        />
      )}
    </div>
  );
}
