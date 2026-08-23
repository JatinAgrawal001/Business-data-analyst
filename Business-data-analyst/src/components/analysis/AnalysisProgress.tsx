import React, { useState, useEffect } from 'react';
import { Sparkles, CheckCircle2, Loader2, Play } from 'lucide-react';

interface AnalysisProgressProps {
  isRunning?: boolean;
  onComplete?: () => void;
  onRun?: () => void;
}

export const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  isRunning = false,
  onComplete,
  onRun
}) => {
  const [progress, setProgress] = useState(isRunning ? 0 : 100);
  const [activeStep, setActiveStep] = useState(isRunning ? 0 : 4);

  const steps = [
    { title: 'Schema Ingestion & Type Inference', desc: 'Validating generic column formats & missingness' },
    { title: 'Descriptive Statistics & Variances', desc: 'Computing mean, quantiles, and standard deviations' },
    { title: 'Pearson Correlation Engine', desc: 'Mapping cross-variable dependency matrix' },
    { title: 'Z-Score Anomaly & Outlier Scan', desc: 'Detecting statistical deviations > 1.9σ' },
    { title: 'Predictive Horizon & Synthesis', desc: 'Constructing Holt-Winters forecast & executive insights' }
  ];

  const onCompleteRef = React.useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    if (!isRunning) {
      setProgress(100);
      setActiveStep(4);
      return;
    }

    setProgress(10);
    setActiveStep(0);

    let currentProgress = 10;
    const interval = setInterval(() => {
      currentProgress += 18;
      if (currentProgress >= 100) {
        currentProgress = 100;
        clearInterval(interval);
        setProgress(100);
        setActiveStep(4);
        setTimeout(() => {
          onCompleteRef.current?.();
        }, 100);
        return;
      }

      setProgress(currentProgress);
      const nextStep = Math.min(4, Math.floor((currentProgress / 100) * 5));
      setActiveStep(nextStep);
    }, 400);

    return () => clearInterval(interval);
  }, [isRunning]);

  return (
    <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 font-display">
              Autonomous Intelligence Pipeline
            </h4>
            <p className="text-xs text-slate-400">
              {progress < 100 ? 'Running deep statistical profiling...' : 'Dataset profiling completed'}
            </p>
          </div>
        </div>

        {onRun && progress === 100 && (
          <button
            onClick={onRun}
            className="px-3 py-1.5 bg-indigo-600/90 hover:bg-indigo-600 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shadow-sm"
          >
            <Play className="w-3 h-3 fill-current" />
            <span>Re-run Analysis</span>
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-5">
        <div className="flex justify-between text-xs mb-1.5 font-mono">
          <span className="text-slate-400">{steps[activeStep]?.title}</span>
          <span className="text-indigo-400 font-bold">{progress}%</span>
        </div>
        <div className="h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-400 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Step Indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
        {steps.map((step, idx) => {
          const isDone = idx < activeStep || progress === 100;
          const isCurrent = idx === activeStep && progress < 100;

          return (
            <div
              key={idx}
              className={`p-2.5 rounded-xl border transition-all ${
                isDone
                  ? 'bg-slate-950/60 border-slate-800/80 text-slate-300'
                  : isCurrent
                  ? 'bg-indigo-950/40 border-indigo-500/50 text-indigo-200'
                  : 'bg-slate-950/20 border-slate-850 text-slate-600'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-1">
                {isDone ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                ) : isCurrent ? (
                  <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin shrink-0" />
                ) : (
                  <div className="w-3.5 h-3.5 rounded-full border border-slate-700 shrink-0" />
                )}
                <span className="text-[11px] font-semibold truncate">{step.title}</span>
              </div>
              <p className="text-[10px] text-slate-400 line-clamp-1">{step.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
