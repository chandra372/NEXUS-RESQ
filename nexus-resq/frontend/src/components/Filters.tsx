import React from 'react';
import { Search, FilterX } from 'lucide-react';
import { FilterState } from '../types';

interface FiltersProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  stages: string[];
}

export const Filters: React.FC<FiltersProps> = ({ filters, onChange, stages }) => {
  const handleReset = () => {
    onChange({ status: '', priority: '', stage: '', search: '' });
  };

  return (
    <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-md space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Filters</h2>
        {(filters.status || filters.priority || filters.stage || filters.search) && (
          <button
            onClick={handleReset}
            className="flex items-center gap-1 text-[11px] text-red-400 hover:text-red-300 transition cursor-pointer font-medium"
          >
            <FilterX className="w-3 h-3" /> Clear
          </button>
        )}
      </div>

      {/* Search Input */}
      <div>
        <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
          Search Location / Keyword
        </label>
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={filters.search}
            onChange={(e) => onChange({ ...filters, search: e.target.value })}
            placeholder="Velachery, MRTS, fire..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Status Filter */}
      <div>
        <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
          Incident Status
        </label>
        <select
          value={filters.status}
          onChange={(e) => onChange({ ...filters, status: e.target.value })}
          className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
        >
          <option value="">All Statuses</option>
          <option value="ACTIVE">ACTIVE</option>
          <option value="ESCALATING">ESCALATING</option>
          <option value="RESCUE_IN_PROGRESS">RESCUE IN PROGRESS</option>
          <option value="RESOLVED">RESOLVED</option>
          <option value="DETECTED">DETECTED</option>
        </select>
      </div>

      {/* Priority Filter */}
      <div>
        <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
          Priority Level
        </label>
        <select
          value={filters.priority}
          onChange={(e) => onChange({ ...filters, priority: e.target.value })}
          className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
        >
          <option value="">All Priorities</option>
          <option value="CRITICAL">CRITICAL (81-100)</option>
          <option value="HIGH">HIGH (61-80)</option>
          <option value="MEDIUM">MEDIUM (31-60)</option>
          <option value="LOW">LOW (0-30)</option>
        </select>
      </div>

      {/* Stage Filter */}
      <div>
        <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
          Lifecycle Stage
        </label>
        <select
          value={filters.stage}
          onChange={(e) => onChange({ ...filters, stage: e.target.value })}
          className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
        >
          <option value="">All Stages</option>
          {stages.map((stg) => (
            <option key={stg} value={stg}>
              {stg.replace('_', ' ').toUpperCase()}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};
