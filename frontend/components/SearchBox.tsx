'use client';

import React, { useState } from 'react';
import { Search, Sparkles, SlidersHorizontal, Zap } from 'lucide-react';

interface SearchBoxProps {
  onSearch: (query: string, topK: number) => void;
  isLoading: boolean;
}

const PRESET_QUERIES = [
  {
    label: "1.1 kV Electrical Cables",
    query: "Procurement of PVC and XLPE insulated electrical cables for 1.1 kV underground power distribution mains"
  },
  {
    label: "Reinforced Concrete & Cement",
    query: "High strength Portland Pozzolana Cement and 43/53 grade OPC for reinforced concrete bridge girders and marine structures"
  },
  {
    label: "Structural Steel Sections",
    query: "Hot rolled medium and high tensile structural steel plates and TMT deformed bars Fe 500 for industrial framework"
  },
  {
    label: "Solar PV Modules",
    query: "Crystalline silicon terrestrial photovoltaic modules and solar water pumping systems for agricultural irrigation"
  },
  {
    label: "Fire Safety Extinguishers",
    query: "Selection and testing requirements for portable ABC dry powder and CO2 fire extinguishers in commercial buildings"
  },
  {
    label: "Information Security ISMS",
    query: "Mandatory cyber security management systems, access control and encryption standards under ISO 27001"
  }
];

export const SearchBox: React.FC<SearchBoxProps> = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim(), topK);
    }
  };

  const handlePresetClick = (presetQuery: string) => {
    setQuery(presetQuery);
    if (!isLoading) {
      onSearch(presetQuery, topK);
    }
  };

  return (
    <div className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-6 shadow-sm mb-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-semibold text-on-surface flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-primary" />
            <span>Procurement Requirement Specification</span>
          </label>
          <div className="flex items-center space-x-2 text-xs text-secondary font-mono">
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Top Results:</span>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="bg-surface-container-low border border-surface-container-high text-on-surface rounded-DEFAULT px-2 py-1 focus:outline-none focus:border-primary"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={15}>15</option>
              <option value={20}>20</option>
            </select>
          </div>
        </div>

        <div className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter technical procurement specification (e.g., 'Procurement of electrical cables for 1.1 kV power distribution' or 'Structural steel TMT bars Fe 500 for bridge construction')..."
            rows={3}
            className="w-full bg-surface-container-low border border-outline-variant rounded-DEFAULT p-4 text-on-surface placeholder-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition text-sm resize-none font-sans"
          />

          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="absolute bottom-4 right-4 bg-primary hover:bg-primary-container text-on-primary font-semibold px-5 py-2.5 rounded-DEFAULT flex items-center space-x-2 shadow-sm transition disabled:opacity-50 disabled:cursor-not-allowed text-xs font-mono"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Analyzing IS Database...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Recommend Standards</span>
              </>
            )}
          </button>
        </div>

        <div>
          <span className="text-xs text-secondary font-medium flex items-center space-x-1 mb-2 font-mono">
            <Zap className="w-3 h-3 text-amber-600" />
            <span>Try sample procurement queries:</span>
          </span>
          <div className="flex flex-wrap gap-2">
            {PRESET_QUERIES.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handlePresetClick(preset.query)}
                className="text-xs bg-surface-container-low hover:bg-surface-container border border-surface-container-high hover:border-primary text-secondary hover:text-on-surface px-3 py-1.5 rounded-DEFAULT transition font-mono"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  );
};
