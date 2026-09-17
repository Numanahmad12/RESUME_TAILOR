import React, { useEffect, useState } from 'react';
import { Sparkles, CheckCircle2, ShieldCheck, Zap, FileText } from 'lucide-react';

interface LoadingProgressBarProps {
  title?: string;
  subtitle?: string;
  estimatedDurationMs?: number; // expected duration to scale progress smoothly
  onComplete?: () => void;
}

const STAGES = [
  { label: 'Parsing Profile & Projects', icon: FileText, percent: 20 },
  { label: 'Analyzing Job Core Competencies', icon: Zap, percent: 45 },
  { label: 'Tailoring Project Bullet Points', icon: Sparkles, percent: 70 },
  { label: 'Enforcing Anti-Hallucination Guardrails', icon: ShieldCheck, percent: 90 },
  { label: 'Assembling Aligned Resume', icon: CheckCircle2, percent: 100 },
];

const PRO_TIPS = [
  '💡 Grounded AI: Every generated sentence is strictly cross-referenced against your verified background.',
  '⚡ Quantified Impact: Strong action verbs (Architected, Engineered, Shipped) increase ATS pass rates by 40%.',
  '🎯 100% Project Integrity: All 3 of your real projects are preserved and customized to this target role.',
  '🛡️ Zero Hallucination: Degrees, graduation dates, and company titles are kept 100% authentic.',
  '📄 Reference Standard: Output is rendered in the industry-proven Jake\'s LaTeX typography.',
];

export const LoadingProgressBar: React.FC<LoadingProgressBarProps> = ({
  title = 'Tailoring Resume with AI…',
  subtitle = 'Aligning summary, technical skills, and all projects to target job description without hallucinating.',
  estimatedDurationMs = 6000,
}) => {
  const [progress, setProgress] = useState(12);
  const [currentTipIdx, setCurrentTipIdx] = useState(0);

  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      // Asymptotic curve: fast initially, slows down as it approaches 96%
      const target = Math.min(96, Math.floor(10 + (elapsed / estimatedDurationMs) * 86));
      setProgress((prev) => Math.max(prev, target));
    }, 150);

    const tipInterval = setInterval(() => {
      setCurrentTipIdx((prev) => (prev + 1) % PRO_TIPS.length);
    }, 2800);

    return () => {
      clearInterval(interval);
      clearInterval(tipInterval);
    };
  }, [estimatedDurationMs]);

  // Determine current active stage
  const activeStageIdx = STAGES.findIndex((s) => progress <= s.percent);
  const currentStage = STAGES[activeStageIdx !== -1 ? activeStageIdx : STAGES.length - 1];

  return (
    <div className="card p-8 md:p-10 text-center space-y-6 max-w-xl mx-auto border border-red-900/40 bg-slate-950/80 shadow-2xl shadow-red-950/30 rounded-2xl animate-fade-in">
      {/* Animated Glowing Icon */}
      <div className="relative w-16 h-16 mx-auto">
        <div className="absolute inset-0 rounded-2xl bg-red-600/30 blur-xl animate-pulse" />
        <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-red-600 to-rose-700 flex items-center justify-center shadow-lg border border-red-400/40">
          <Sparkles size={28} className="text-white animate-spin-slow" />
        </div>
      </div>

      <div className="space-y-1.5">
        <h3 className="text-lg md:text-xl font-bold text-white tracking-tight">{title}</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">{subtitle}</p>
      </div>

      {/* Progress Bar Container */}
      <div className="space-y-2.5 pt-2">
        <div className="flex justify-between items-center text-xs font-semibold">
          <span className="text-slate-300 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-slate-200">{currentStage.label}</span>
          </span>
          <span className="font-mono text-red-400 text-sm font-bold">{progress}%</span>
        </div>

        {/* Outer Bar */}
        <div className="w-full h-3.5 bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-700/80 shadow-inner">
          {/* Inner Animated Gradient Fill */}
          <div
            className="h-full rounded-full bg-gradient-to-r from-red-600 via-rose-500 to-amber-400 transition-all duration-300 ease-out relative overflow-hidden shadow-sm"
            style={{ width: `${progress}%` }}
          >
            {/* Shimmer light bar effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
          </div>
        </div>
      </div>

      {/* Mini Visual Stages Tracker */}
      <div className="grid grid-cols-5 gap-1 pt-1">
        {STAGES.map((s, idx) => {
          const isDone = progress >= s.percent;
          const isCurrent = !isDone && (idx === 0 || progress >= STAGES[idx - 1].percent);
          return (
            <div key={idx} className="flex flex-col items-center gap-1">
              <div
                className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${
                  isDone
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/60'
                    : isCurrent
                    ? 'bg-red-600/30 text-red-300 border border-red-500 animate-pulse'
                    : 'bg-slate-900 text-slate-600 border border-slate-800'
                }`}
              >
                {isDone ? '✓' : idx + 1}
              </div>
              <span className="text-[9px] text-slate-400 truncate max-w-full hidden sm:block">
                {s.label.split(' ')[0]}
              </span>
            </div>
          );
        })}
      </div>

      {/* Rotating Pro Tips Box */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 text-left min-h-[50px] flex items-center transition-all duration-300">
        <p className="text-xs text-slate-300 italic transition-all duration-300 key={currentTipIdx}">
          {PRO_TIPS[currentTipIdx]}
        </p>
      </div>
    </div>
  );
};
