import React from 'react';
import { 
  ShieldAlert, Play, Pause, RotateCcw, FastForward, 
  ChevronRight, BarChart3, Radio, Volume2, Cpu 
} from 'lucide-react';
import { ReplayStatus, OverallStats } from '../types';

interface HeaderProps {
  stats: OverallStats | null;
  replayStatus: ReplayStatus | null;
  onStart: (speed: number) => void;
  onPause: () => void;
  onReset: () => void;
  onNextStage: () => void;
  onProcessStep: () => void;
  onProcessAll: () => void;
  onOpenEval: () => void;
  speed: number;
  setSpeed: (s: number) => void;
}

export const Header: React.FC<HeaderProps> = ({
  stats,
  replayStatus,
  onStart,
  onPause,
  onReset,
  onNextStage,
  onProcessStep,
  onProcessAll,
  onOpenEval,
  speed,
  setSpeed
}) => {
  const isRunning = replayStatus?.is_running ?? false;
  const currentStage = replayStatus?.current_stage ?? 'stage_1';

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 sticky top-0 z-30 shadow-lg">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Brand & Subtitle */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-red-600/20 border border-red-500/40 rounded-xl text-red-500 shadow-inner">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
                NEXUS <span className="text-red-500">RESQ</span>
              </h1>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                Decision Support
              </span>
              <span className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                LIVE
              </span>
            </div>
            <p className="text-xs text-slate-400">
              AI Emergency Incident Intelligence & Response Assistant
            </p>
          </div>
        </div>

        {/* System Engine Badges */}
        <div className="hidden xl:flex items-center gap-3 text-xs text-slate-400">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>AI: <strong className="text-slate-200">Local Multi-Factor</strong></span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60">
            <Volume2 className="w-3.5 h-3.5 text-amber-400" />
            <span>STT: <strong className="text-slate-200">Voice Recognition</strong></span>
          </div>
          <button
            onClick={onOpenEval}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 transition-all font-semibold cursor-pointer"
          >
            <BarChart3 className="w-3.5 h-3.5 text-indigo-400" />
            <span>View Benchmark</span>
          </button>
        </div>

        {/* Stream Replay Controls */}
        <div className="flex flex-wrap items-center gap-2 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800 shadow-inner">
          {/* Current Stage Indicator */}
          <div className="px-3 py-1 bg-slate-800 rounded-lg text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
            <span>{currentStage.replace('_', ' ')}</span>
          </div>

          {/* Action buttons */}
          <button
            onClick={onProcessStep}
            className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition cursor-pointer"
            title="Process Single Report"
          >
            Step
          </button>

          <button
            onClick={onProcessAll}
            className="px-3 py-1.5 bg-sky-600/80 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold transition cursor-pointer shadow-sm"
            title="Process All in Current Stage"
          >
            Process Stage
          </button>

          {isRunning ? (
            <button
              onClick={onPause}
              className="flex items-center gap-1 px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold transition cursor-pointer shadow-sm"
            >
              <Pause className="w-3.5 h-3.5" /> Pause
            </button>
          ) : (
            <button
              onClick={() => onStart(speed)}
              className="flex items-center gap-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition cursor-pointer shadow-sm"
            >
              <Play className="w-3.5 h-3.5" /> Replay
            </button>
          )}

          {/* Speed Selector */}
          <div className="flex items-center bg-slate-900 rounded-lg border border-slate-800 overflow-hidden text-xs">
            {[1, 5, 20].map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`px-2 py-1 font-semibold transition cursor-pointer ${
                  speed === s ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Next Stage Button */}
          <button
            onClick={onNextStage}
            className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition cursor-pointer shadow-sm"
            title="Advance to Next Stage with Persistent Memory"
          >
            Next Stage <ChevronRight className="w-3.5 h-3.5" />
          </button>

          {/* Reset Button */}
          <button
            onClick={onReset}
            className="p-1.5 text-slate-400 hover:text-red-400 rounded-lg hover:bg-slate-800 transition cursor-pointer"
            title="Reset All Memory and Incidents"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
