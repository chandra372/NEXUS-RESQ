import React, { useState, useEffect } from 'react';
import { X, Award, CheckCircle, BarChart2, ShieldCheck, RefreshCw } from 'lucide-react';
import { EvaluationResults } from '../types';
import { api } from '../services/api';

interface EvaluationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EvaluationModal: React.FC<EvaluationModalProps> = ({ isOpen, onClose }) => {
  const [results, setResults] = useState<EvaluationResults | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchEval = () => {
    setLoading(true);
    api.getEvaluation()
      .then((data) => {
        setResults(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to run benchmark:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    if (isOpen) {
      fetchEval();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 rounded-xl">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                NEXUS RESQ Evaluation Benchmark
              </h2>
              <p className="text-xs text-slate-400">
                Ground Truth Benchmark Verification (Strictly Isolated Evaluation)
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchEval}
              disabled={loading}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition cursor-pointer"
              title="Re-run evaluation"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          {loading ? (
            <div className="text-center py-16 space-y-3">
              <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
              <p className="text-sm font-semibold text-slate-300">
                Evaluating all 471 reports against Ground Truth...
              </p>
              <p className="text-xs text-slate-500">
                Calculating classification, clustering ARI, and landmark accuracies.
              </p>
            </div>
          ) : !results ? (
            <div className="text-center py-12 text-red-400">
              Failed to load evaluation metrics.
            </div>
          ) : (
            <>
              {/* Primary Score Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 block uppercase">Emergency Intent</span>
                  <span className="text-2xl font-black text-emerald-400 mt-1 block">
                    {results.emergency_classification_accuracy}%
                  </span>
                  <span className="text-[10px] text-emerald-500/80 font-medium">Precision: High</span>
                </div>

                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 block uppercase">Clustering ARI</span>
                  <span className="text-2xl font-black text-indigo-400 mt-1 block">
                    {results.incident_clustering_accuracy_ari}%
                  </span>
                  <span className="text-[10px] text-indigo-400/80 font-medium">Sequential Memory</span>
                </div>

                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 block uppercase">Location Resolution</span>
                  <span className="text-2xl font-black text-cyan-400 mt-1 block">
                    {results.location_accuracy}%
                  </span>
                  <span className="text-[10px] text-cyan-400/80 font-medium">Landmark Mapping</span>
                </div>

                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 block uppercase">Status Accuracy</span>
                  <span className="text-2xl font-black text-amber-400 mt-1 block">
                    {results.status_accuracy}%
                  </span>
                  <span className="text-[10px] text-amber-400/80 font-medium">State Transitions</span>
                </div>
              </div>

              {/* Secondary Metrics */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 block uppercase">Noise Filtering</span>
                  <span className="text-lg font-bold text-slate-200 mt-0.5 block">
                    {results.noise_classification_accuracy}%
                  </span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 block uppercase">Resource Extraction</span>
                  <span className="text-lg font-bold text-slate-200 mt-0.5 block">
                    {results.resource_extraction_accuracy}%
                  </span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 block uppercase">People Count MAE</span>
                  <span className="text-lg font-bold text-slate-200 mt-0.5 block">
                    {results.people_count_mae}
                  </span>
                </div>
              </div>

              {/* Per-Stage Breakdown Table */}
              <div className="bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
                <div className="px-4 py-2.5 bg-slate-900 border-b border-slate-800 font-bold text-slate-200 flex items-center justify-between">
                  <span>Lifecycle Stage Performance Breakdown</span>
                  <span className="text-[10px] text-slate-400 font-normal">
                    Evaluated across {results.total_records_evaluated} records
                  </span>
                </div>
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/60 text-slate-400 text-[10px] uppercase border-b border-slate-800">
                    <tr>
                      <th className="p-2.5">Stage</th>
                      <th className="p-2.5">Reports</th>
                      <th className="p-2.5">Emergency Acc</th>
                      <th className="p-2.5">Location Acc</th>
                      <th className="p-2.5">Resource Acc</th>
                      <th className="p-2.5">Status Acc</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {Object.entries(results.per_stage_results).map(([stage, m]) => (
                      <tr key={stage} className="hover:bg-slate-900/40">
                        <td className="p-2.5 font-bold uppercase text-indigo-400">{stage.replace('_', ' ')}</td>
                        <td className="p-2.5">{m.events_processed}</td>
                        <td className="p-2.5 text-emerald-400 font-semibold">{m.emergency_classification_accuracy}%</td>
                        <td className="p-2.5 text-cyan-400 font-semibold">{m.location_accuracy}%</td>
                        <td className="p-2.5">{m.resource_accuracy}%</td>
                        <td className="p-2.5 text-amber-400 font-semibold">{m.status_accuracy}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Zero-Leakage Guarantee Notice */}
              <div className="p-3 bg-emerald-950/20 border border-emerald-500/30 rounded-xl flex items-center gap-2 text-emerald-300 text-xs">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  <strong>Strict Isolation Guarantee:</strong> ground_truth.json is used exclusively inside the independent benchmark evaluator. Inference discovers incidents purely through raw unlabelled reports.
                </span>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
