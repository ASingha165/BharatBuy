'use client';

import React, { useState } from 'react';
import { ProcurementAnalysisRequest, ProcurementRequirementItem } from '../types';
import { Plus, Trash2, Building, FileText, CheckSquare, Layers, Send, ShieldAlert, History } from 'lucide-react';

interface ProcurementAnalysisFormProps {
  onSubmit: (request: ProcurementAnalysisRequest) => void;
  isLoading: boolean;
}

const PRESET_SCENARIOS = [
  {
    name: "SOLAR PROJECT",
    description: "500 kW rooftop solar plant (solar PV modules, grid-tie inverter, DC solar cables, mounting structures)",
    company: "SunVayu CleanEnergy Ltd",
    items: [
      {
        item: "Crystalline silicon terrestrial solar PV modules",
        quantity: 300,
        unit: "units",
        specifications: "Terrestrial photovoltaic modules, 450W peak, IS 14286 qualified and CRS certified"
      },
      {
        item: "Grid-tied solar inverters",
        quantity: 6,
        unit: "units",
        specifications: "50 kW grid-tied solar string inverters, anti-islanding protection per IS 16221"
      },
      {
        item: "1.1 kV XLPE insulated solar DC power cables",
        quantity: 2000,
        unit: "meters",
        specifications: "Crosslinked polyethylene cables, 1100 V rating, UV and weather resistant per IS 7098 Part 1"
      },
      {
        item: "Galvanized steel solar mounting structures",
        quantity: 30,
        unit: "sets",
        specifications: "Hot-dip galvanized structural steel sections per IS 2062, corrosion resistant for outdoor solar racking"
      }
    ]
  },
  {
    name: "FACTORY CONSTRUCTION",
    description: "Industrial facility expansion (TMT steel rebar Fe 500D, Portland Pozzolana Cement, structural steel channels)",
    company: "Bharat InfraBuild Projects LLP",
    items: [
      {
        item: "Fe 500 High strength deformed TMT steel reinforcement bars",
        quantity: 45,
        unit: "metric tonnes",
        specifications: "TMT rebar 12mm and 16mm per IS 1786, yield strength 500 MPa, ISI mark certified"
      },
      {
        item: "Portland Pozzolana Cement (Fly Ash Based)",
        quantity: 1200,
        unit: "bags (50kg)",
        specifications: "PPC cement conforming to IS 1489 Part 1 for heavy concrete foundations and columns"
      },
      {
        item: "Structural steel channels and joists",
        quantity: 20,
        unit: "metric tonnes",
        specifications: "Hot rolled medium and high tensile structural steel per IS 2062 Grade E250 for warehouse trusses"
      }
    ]
  },
  {
    name: "IT / OFFICE PROCUREMENT",
    description: "Enterprise hardware & power backup (laptops/tablets, online UPS, Cat6 Ethernet cables)",
    company: "PayNova Solutions Pvt Ltd",
    items: [
      {
        item: "Development workstations and enterprise laptops",
        quantity: 50,
        unit: "units",
        specifications: "Information technology computing equipment, safety per IS 13252 Part 1, mandatory CRS registration"
      },
      {
        item: "Office online backup power system (UPS)",
        quantity: 2,
        unit: "units",
        specifications: "Uninterruptible Power Systems 10 kVA with DC battery link, overload protection per IS 16242 Part 1"
      },
      {
        item: "Category 6 UTP structured Ethernet cabling",
        quantity: 1000,
        unit: "meters",
        specifications: "High-speed 4-pair unshielded twisted pair copper communication cables for enterprise LAN per IS/IEC standards"
      }
    ]
  }
];

export const ProcurementAnalysisForm: React.FC<ProcurementAnalysisFormProps> = ({
  onSubmit,
  isLoading
}) => {
  const [company, setCompany] = useState('');
  const [mode, setMode] = useState<'structured' | 'natural'>('structured');
  const [naturalText, setNaturalText] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [items, setItems] = useState<ProcurementRequirementItem[]>([
    {
      item: '',
      quantity: undefined,
      unit: '',
      specifications: ''
    }
  ]);

  // Helper: quantity display value — show empty string when undefined/null so the
  // initial blank row starts truly blank (Task 6).
  const quantityDisplayValue = (qty: number | undefined): string | number => {
    if (qty === undefined || qty === null) return '';
    return qty;
  };

  const handleAddItem = () => {
    setItems([
      ...items,
      { item: '', quantity: undefined, unit: '', specifications: '' }
    ]);
  };

  const handleRemoveItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, idx) => idx !== index));
    }
  };

  const handleItemChange = (index: number, field: keyof ProcurementRequirementItem, value: any) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: value };
    setItems(updated);
  };

  const handleLoadScenario = (scenario: typeof PRESET_SCENARIOS[0]) => {
    setCompany(scenario.company);
    setItems(scenario.items);
    setMode('structured');
    setValidationError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;
    setValidationError(null);

    if (!company.trim()) {
      setValidationError('Buyer entity name is required.');
      return;
    }

    if (mode === 'natural') {
      if (!naturalText.trim()) {
        setValidationError('Please paste your procurement requirements or tender specifications.');
        return;
      }
      onSubmit({
        company: company.trim(),
        description: naturalText.trim(),
        requirements: [],
        top_k_per_item: 5
      });
    } else {
      // Filter out completely blank rows (item name must be non-empty)
      const validItems = items.filter((i) => i.item.trim().length > 0);
      if (validItems.length === 0) {
        setValidationError('Please enter at least one procurement line item before submitting.');
        return;
      }
      onSubmit({
        company: company.trim(),
        requirements: validItems,
        top_k_per_item: 5
      });
    }
  };

  return (
    <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-5 sm:p-7 shadow-sm">
      {/* Context Header & Batch ID */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-surface-container-high">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            <span className="font-mono text-[11px] text-secondary uppercase tracking-wider font-semibold">
              Statutory Intelligence Workbench
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">
            Procurement Analysis Workbench
          </h2>
          <p className="text-xs sm:text-sm text-secondary mt-0.5">
            Evaluate procurement requirements, Indian Standards (BIS), statutory compliance, and evidence prior to buyer approval.
          </p>
        </div>

        {/* Input Mode Toggle */}
        <div className="flex items-center bg-surface-container p-1 rounded-DEFAULT border border-surface-container-high self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setMode('structured')}
            className={`px-3 py-1.5 rounded-DEFAULT text-xs font-semibold transition ${
              mode === 'structured'
                ? 'bg-primary text-white shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Structured Items
          </button>
          <button
            type="button"
            onClick={() => setMode('natural')}
            className={`px-3 py-1.5 rounded-DEFAULT text-xs font-semibold transition ${
              mode === 'natural'
                ? 'bg-primary text-white shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Natural Language Tender
          </button>
        </div>
      </div>

      {/* Mandatory Statutory Governance Warning Banner */}
      <div className="my-4 p-space-md rounded-DEFAULT bg-surface-container border border-surface-container-high flex items-start gap-space-sm shadow-sm">
        <ShieldAlert className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
        <div className="text-xs">
          <span className="font-bold text-primary uppercase tracking-wide font-mono text-[11px] block">
            Statutory Verification Prerequisite
          </span>
          <p className="text-secondary mt-0.5 leading-relaxed">
            Procurement intelligence is evidence-backed decision support. Certification validity and supplier eligibility should be independently verified before buyer approval.
          </p>
        </div>
      </div>

      {/* Preset Scenarios Strip */}
      <div className="my-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono text-secondary uppercase tracking-wider flex items-center gap-1.5">
            <History className="w-3.5 h-3.5 text-tertiary" />
            <span>Industrial Domain Presets:</span>
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {PRESET_SCENARIOS.map((scenario, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleLoadScenario(scenario)}
              className="text-left bg-surface-container-low hover:bg-surface-container border border-surface-container-high hover:border-primary/40 p-2.5 rounded-DEFAULT transition group shadow-sm"
            >
              <div className="font-mono text-xs font-bold text-on-surface group-hover:text-primary transition flex items-center justify-between">
                <span>{scenario.name}</span>
                <span className="text-[10px] text-primary font-mono bg-surface-container-high px-1.5 py-0.2 rounded-DEFAULT border border-surface-container-highest">
                  LOAD
                </span>
              </div>
              <div className="text-[11px] text-secondary line-clamp-1 mt-1">
                {scenario.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Buyer Entity Name */}
        <div>
          <label className="block text-xs font-semibold text-on-surface mb-1.5 flex items-center gap-1.5">
            <Building className="w-3.5 h-3.5 text-primary" />
            <span>Buyer / Startup Entity Name</span>
          </label>
          <input
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            required
            placeholder="e.g. Bharat Infrastructure & Power Corp"
            className="w-full bg-surface-container-low border border-outline-variant rounded-DEFAULT px-3.5 py-2 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition font-sans"
          />
        </div>

        {mode === 'structured' ? (
          /* Multi-Item Structured Input */
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-on-surface flex items-center gap-1.5">
                <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
                <span>Procurement Line Items</span>
                <span className="font-mono text-[11px] bg-surface-container text-on-surface px-1.5 py-0.2 rounded-DEFAULT ml-1 border border-surface-container-high">
                  {items.length} SKUs
                </span>
              </label>
              <button
                type="button"
                onClick={handleAddItem}
                className="text-xs bg-surface-container hover:bg-surface-container-high text-primary border border-surface-container-high px-2.5 py-1 rounded-DEFAULT flex items-center gap-1 font-mono transition"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Item</span>
              </button>
            </div>

            <div className="space-y-2.5">
              {items.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-3.5 relative space-y-2.5 shadow-sm overflow-hidden"
                >
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary"></div>
                  <div className="flex items-center justify-between pl-1">
                    <span className="font-mono text-[11px] font-bold text-primary bg-surface-container-high border border-surface-container-highest px-2 py-0.5 rounded-DEFAULT">
                      LINE #{idx + 1}
                    </span>
                    {items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(idx)}
                        className="text-secondary hover:text-error p-1 transition"
                        title="Remove line item"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-12 gap-2.5 pl-1">
                    <div className="sm:col-span-6">
                      <label className="text-[11px] text-secondary block mb-1">Item Name / Nomenclature</label>
                      <input
                        type="text"
                        value={item.item}
                        onChange={(e) => handleItemChange(idx, 'item', e.target.value)}
                        placeholder="e.g. 1.1 kV XLPE insulated electrical cables"
                        required
                        className="w-full bg-surface-container-low border border-outline-variant rounded-DEFAULT px-3 py-1.5 text-xs text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary"
                      />
                    </div>

                    <div className="sm:col-span-3">
                      <label className="text-[11px] text-secondary block mb-1">Quantity</label>
                      <input
                        type="number"
                        min={1}
                        placeholder="e.g. 100"
                        value={quantityDisplayValue(item.quantity)}
                        onChange={(e) => {
                          const raw = e.target.value;
                          handleItemChange(idx, 'quantity', raw === '' ? undefined : Number(raw));
                        }}
                        className="w-full bg-surface-container-low border border-outline-variant rounded-DEFAULT px-3 py-1.5 text-xs text-on-surface font-mono focus:outline-none focus:border-primary"
                      />
                    </div>

                    <div className="sm:col-span-3">
                      <label className="text-[11px] text-secondary block mb-1">Unit</label>
                      <input
                        type="text"
                        value={item.unit || ''}
                        onChange={(e) => handleItemChange(idx, 'unit', e.target.value)}
                        placeholder="meters, MT, units"
                        className="w-full bg-surface-container-low border border-outline-variant rounded-DEFAULT px-3 py-1.5 text-xs text-on-surface placeholder:text-on-surface-variant/50 font-mono focus:outline-none focus:border-primary"
                      />
                    </div>

                    <div className="sm:col-span-12">
                      <label className="text-[11px] text-secondary block mb-1">Technical Specifications & Material Requirements</label>
                      <input
                        type="text"
                        value={item.specifications || ''}
                        onChange={(e) => handleItemChange(idx, 'specifications', e.target.value)}
                        placeholder="Voltage rating, grade Fe 500D, compliance codes, test requirements..."
                        className="w-full bg-surface-container-low border border-outline-variant rounded-DEFAULT px-3 py-1.5 text-xs text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Natural Language Paragraph Input */
          <div>
            <label className="block text-xs font-semibold text-on-surface mb-1.5 flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-primary" />
              <span>Paste Procurement Requirement / Tender Specifications</span>
            </label>
            <textarea
              value={naturalText}
              onChange={(e) => setNaturalText(e.target.value)}
              placeholder="Paste procurement specifications (e.g., 'We require 1500 meters of 1.1 kV XLPE insulated electrical cables per IS 7098 Part 1, 35 metric tonnes of Fe 500D TMT steel rebar per IS 1786, and 250 units of crystalline silicon solar PV modules per IS 14286')..."
              rows={5}
              className="w-full bg-surface-container-low border border-outline-variant rounded-DEFAULT p-3.5 text-xs sm:text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary transition resize-none font-mono"
            />
          </div>
        )}

        {/* Inline Validation Error Banner */}
        {validationError && (
          <div className="flex items-start gap-2 bg-rose-50 border border-rose-200 rounded-DEFAULT px-3.5 py-2.5 text-xs text-rose-800">
            <span className="shrink-0 mt-0.5">⚠</span>
            <span>{validationError}</span>
          </div>
        )}

        {/* Action Bar with Primary CTA */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-surface-container-high">
          <span className="font-mono text-[11px] text-secondary flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
            POST /api/v1/procurement/analyze
          </span>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full sm:w-auto h-11 bg-primary hover:bg-primary-container text-on-primary font-mono font-bold text-xs uppercase tracking-wider px-6 rounded-DEFAULT flex items-center justify-center gap-2 shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Executing Intelligence Pipeline...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>ANALYZE PROCUREMENT</span>
                <span className="font-mono text-[10px] bg-white/20 px-1.5 py-0.5 rounded-DEFAULT">
                  {mode === 'structured' ? `${items.length} SKUs` : 'TENDER'}
                </span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
