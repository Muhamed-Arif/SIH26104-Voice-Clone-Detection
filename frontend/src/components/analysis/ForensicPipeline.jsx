import React from 'react'
import {
  CpuIcon,
  CheckCircleIcon,
  PlayIcon,
  RefreshCwIcon,
  AlertTriangleIcon,
} from '../common/Icons'

const PIPELINE_STAGES = [
  {
    id: '01',
    name: 'INGEST',
    subtext: 'PCM Stream Ingestion & Normalization (-3 dBFS)',
  },
  {
    id: '02',
    name: 'PREPROCESS',
    subtext: 'Silence Trimming, VAD & STFT Mel Filterbanks',
  },
  {
    id: '03',
    name: 'FEATURE EXTRACTION',
    subtext: 'M2 audio preparation and quality validation',
  },
  {
    id: '04',
    name: 'SPEAKER EMBEDDING',
    subtext: 'M1 authenticity probability and backend risk scoring',
  },
  {
    id: '05',
    name: 'SYNTHETIC VOICE CLASSIFICATION',
    subtext: 'High-frequency Phase & Vocoder Anomaly Verification',
  },
]

export default function ForensicPipeline({
  hasAudio = false,
  isAnalyzing = false,
  activeStage = 0, // 0 to 4 (or 5 for finished)
  progress = 0, // 0 to 100
  onAnalyzeClick,
  onResetClick,
  isComplete = false,
}) {
  return (
    <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-4 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <CpuIcon className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Forensic Analysis Pipeline
          </span>
        </div>
        <span
          className={`text-[10px] px-2 py-0.5 rounded border ${
            isAnalyzing
              ? 'bg-cyan-950/60 border-cyan-500/50 text-cyan-300'
              : isComplete
              ? 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300'
              : 'bg-slate-900 border-slate-800 text-slate-400'
          }`}
        >
          {isAnalyzing
            ? 'ANALYSIS IN PROGRESS'
            : isComplete
            ? 'PIPELINE COMPLETE'
            : hasAudio
            ? 'READY FOR ANALYSIS'
            : 'AWAITING AUDIO'}
        </span>
      </div>

      {/* Demo Warning Banner */}
      {isAnalyzing && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-950/30 p-2.5 text-xs text-amber-300 flex items-start gap-2">
          <AlertTriangleIcon className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
          <div className="space-y-0.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 block">
              DEMO / BACKEND NOT CONNECTED
            </span>
            <p className="text-[11px] leading-relaxed text-amber-200 font-sans">
              Simulating 5-stage inference pass for presentation. No real model prediction is fabricated.
            </p>
          </div>
        </div>
      )}

      {/* Vertical Pipeline Stages */}
      <div className="space-y-2.5">
        {PIPELINE_STAGES.map((stage, idx) => {
          const isDone = isComplete || (isAnalyzing && idx < activeStage)
          const isCurrent = isAnalyzing && idx === activeStage

          let statusLabel = 'PENDING'
          let statusColor = 'text-slate-500'
          let borderStyle = 'border-slate-800/60 bg-slate-900/30'

          if (isDone) {
            statusLabel = 'COMPLETED'
            statusColor = 'text-emerald-400'
            borderStyle = 'border-emerald-500/30 bg-emerald-950/10'
          } else if (isCurrent) {
            statusLabel = 'PROCESSING...'
            statusColor = 'text-cyan-400'
            borderStyle = 'border-cyan-500/50 bg-cyan-950/20 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
          }

          return (
            <div
              key={stage.id}
              className={`rounded-lg border p-3 transition-all duration-300 ${borderStyle}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="text-[11px] font-bold text-slate-400">
                    {stage.id}
                  </span>
                  <div>
                    <h4
                      className={`text-xs font-semibold ${
                        isCurrent
                          ? 'text-cyan-300'
                          : isDone
                          ? 'text-slate-200'
                          : 'text-slate-400'
                      }`}
                    >
                      {stage.name}
                    </h4>
                    <p className="text-[10px] text-slate-500 font-sans mt-0.5">
                      {stage.subtext}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 text-[10px]">
                  {isDone && <CheckCircleIcon className="h-3.5 w-3.5 text-emerald-400" />}
                  {isCurrent && (
                    <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
                  )}
                  <span className={statusColor}>{statusLabel}</span>
                </div>
              </div>

              {/* Progress bar for currently processing stage */}
              {isCurrent && (
                <div className="mt-2.5 h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    style={{ width: `${progress}%` }}
                    className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-150"
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Action Button */}
      <div className="pt-2">
        {!isComplete ? (
          <button
            type="button"
            disabled={!hasAudio || isAnalyzing}
            onClick={onAnalyzeClick}
            className={`w-full flex items-center justify-center gap-2 rounded-xl py-3 px-4 text-xs font-bold uppercase tracking-wider transition-all duration-200 border ${
              !hasAudio
                ? 'bg-slate-900 border-slate-800 text-slate-500 cursor-not-allowed'
                : isAnalyzing
                ? 'bg-cyan-950/60 border-cyan-500/40 text-cyan-400 cursor-wait'
                : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 border-cyan-400/30 text-white shadow-[0_0_20px_rgba(6,182,212,0.25)]'
            }`}
          >
            {isAnalyzing ? (
              <>
                <span className="h-3 w-3 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
                <span>EXECUTING PIPELINE (DEMO)...</span>
              </>
            ) : (
              <>
                <PlayIcon className="h-3.5 w-3.5" />
                <span>ANALYZE VOICE</span>
              </>
            )}
          </button>
        ) : (
          <button
            type="button"
            onClick={onResetClick}
            className="w-full flex items-center justify-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-900 hover:border-slate-700 py-3 px-4 text-xs font-bold uppercase tracking-wider text-slate-300 hover:text-white transition-all"
          >
            <RefreshCwIcon className="h-3.5 w-3.5 text-cyan-400" />
            <span>RESET PIPELINE</span>
          </button>
        )}
      </div>

      {/* Pipeline Notice */}
      <p className="text-[10px] text-slate-500 text-center">
        POST /analyze payload configured with multipart/form-data.
      </p>
    </div>
  )
}
