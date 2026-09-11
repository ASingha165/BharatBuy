'use client';

import React, { useEffect, useState } from 'react';
import { Clock3, RefreshCw, Search, Trash2, History as HistoryIcon } from 'lucide-react';
import {
  deleteProcurementHistoryFirestore,
  listProcurementHistoryFirestore,
  ProcurementHistoryRecord
} from '../lib/firestore-service';

interface ProcurementHistoryProps {
  uid: string;
  onLoad: (record: ProcurementHistoryRecord) => void;
  onRefresh: (record: ProcurementHistoryRecord) => void;
}

export const ProcurementHistory: React.FC<ProcurementHistoryProps> = ({ uid, onLoad, onRefresh }) => {
  const [records, setRecords] = useState<ProcurementHistoryRecord[]>([]);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);

  const loadHistory = async () => {
    setLoading(true);
    const result = await listProcurementHistoryFirestore({ uid });
    setRecords(result.records);
    setNotice(result.error ? 'History could not be loaded from Firebase.' : null);
    setLoading(false);
  };

  useEffect(() => {
    void loadHistory();
  }, [uid]);

  const filteredRecords = records.filter((record) => {
    const matchesQuery = !query.trim() || `${record.company_name} ${record.procurement_id}`.toLowerCase().includes(query.trim().toLowerCase());
    const matchesStatus = status === 'ALL' || record.request_status === status;
    return matchesQuery && matchesStatus;
  });

  const handleDelete = async (record: ProcurementHistoryRecord) => {
    if (!window.confirm(`Delete history record ${record.procurement_id}?`)) return;
    const deleted = await deleteProcurementHistoryFirestore(uid, record.procurement_id);
    if (deleted) {
      setRecords((current) => current.filter((item) => item.procurement_id !== record.procurement_id));
    } else {
      setNotice('History record could not be deleted.');
    }
  };

  return (
    <section className="space-y-4" aria-labelledby="history-heading">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between border-b border-surface-container-high pb-4">
        <div>
          <div className="flex items-center gap-2 text-primary font-mono text-xs font-bold uppercase">
            <HistoryIcon className="w-4 h-4" /> Procurement History
          </div>
          <h2 id="history-heading" className="text-xl font-bold text-on-surface mt-1">Saved analysis snapshots</h2>
          <p className="text-xs text-secondary mt-1">Historical snapshots retain their original timestamps and do not imply current verification.</p>
        </div>
        <button type="button" onClick={() => void loadHistory()} className="text-xs font-mono text-primary border border-primary rounded-DEFAULT px-3 py-2 flex items-center gap-2">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh history
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-2">
        <label className="flex items-center gap-2 bg-surface-container-low border border-surface-container-high rounded-DEFAULT px-3 py-2">
          <Search className="w-4 h-4 text-secondary" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search company or procurement ID" className="w-full bg-transparent text-xs outline-none" />
        </label>
        <select value={status} onChange={(event) => setStatus(event.target.value)} className="bg-surface-container-low border border-surface-container-high rounded-DEFAULT px-3 py-2 text-xs">
          <option value="ALL">All statuses</option>
          <option value="COMPLETED">Completed</option>
        </select>
      </div>

      {notice && <div className="bg-amber-50 border border-amber-200 text-amber-900 rounded-DEFAULT px-3 py-2 text-xs">{notice}</div>}
      {loading ? <div className="text-sm text-secondary py-8">Loading history...</div> : filteredRecords.length === 0 ? <div className="text-sm text-secondary py-8 text-center border border-dashed border-surface-container-high rounded-DEFAULT">No saved procurement analyses found.</div> : (
        <div className="space-y-3">
          {filteredRecords.map((record) => (
            <article key={record.procurement_id} className="border border-surface-container-high rounded-DEFAULT bg-surface-container-lowest p-4 space-y-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="font-mono text-xs text-primary font-bold">{record.procurement_id}</div>
                  <h3 className="font-bold text-on-surface">{record.company_name}</h3>
                  <div className="text-[11px] text-secondary flex items-center gap-1 mt-1"><Clock3 className="w-3 h-3" /> {new Date(record.analysis_created_at).toLocaleString()} · {record.items.length} SKUs</div>
                </div>
                <span className="text-[10px] uppercase font-mono font-bold px-2 py-1 rounded-DEFAULT bg-surface-container border border-surface-container-high">{record.request_status}</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-[11px] text-secondary">
                <span>Budget: {record.budget.total_budget == null ? 'Unknown' : `INR ${record.budget.total_budget.toLocaleString('en-IN')}`}</span>
                <span>Range: {record.search.radius == null ? 'Unknown' : `${record.search.radius} km`}</span>
                <span>Strategy: {record.sourcing.sourcing_strategy.replace(/_/g, ' ')}</span>
                <span>Official records: {record.sourcing.official_record_count}</span>
                <span>GST verified: {record.sourcing.verified_supplier_count}</span>
              </div>
              <div className="text-[10px] text-amber-800 bg-amber-50 border border-amber-200 rounded-DEFAULT px-2 py-1">Historical snapshot — verification status may have changed since this analysis.</div>
              <div className="flex flex-wrap gap-2 pt-1">
                <button type="button" onClick={() => onLoad(record)} className="text-xs font-mono font-bold bg-primary text-white rounded-DEFAULT px-3 py-2">LOAD ANALYSIS</button>
                <button type="button" onClick={() => onRefresh(record)} className="text-xs font-mono text-primary border border-primary rounded-DEFAULT px-3 py-2 flex items-center gap-1"><RefreshCw className="w-3 h-3" /> REFRESH ANALYSIS</button>
                <button type="button" onClick={() => void handleDelete(record)} title="Delete history record" className="text-xs text-error border border-rose-200 rounded-DEFAULT px-3 py-2 flex items-center gap-1"><Trash2 className="w-3 h-3" /> DELETE</button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
};
