import React from 'react'
import { BarChartIcon, InfoIcon } from '../common/Icons'

export default function ConfidenceMeter({
  confidence = null,
  human_probability = null,
  synthetic_probability = null,
}) {
  const hasInference =
    confidence !== null &&
    (human_probability !== null || synthetic_probability !== null)

  const humanPct = human_probability !== null ? Math.round(human_probability * 100) : 0
  const synthPct = synthetic_probability !== null ? Math.round(synthetic_probability * 100) : 0

  return (
    <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <BarChartIcon className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Confidence & Probability Distribution
          </span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
          {hasInference ? `CONFIDENCE: ${confidence}` : 'UNVERIFIED'}
        </span>
      </div>

      {!hasInference ? (
        <div className="rounded-lg bg-slate-900/50 border border-slate-800/80 p-4 text-center space-y-2">
          <div className="flex items-center justify-center text-slate-500">
            <InfoIcon className="h-5 w-5" />
          </div>
          <div className="text-xs font-mono font-medium text-slate-300">
            Awaiting model inference
          </div>
          <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
            Audio stream must be submitted to the deep learning ensemble before classification confidence can be calculated.
          </p>
        </div>
      ) : (
        <div className="space-y-3 font-mono text-xs">
          {/* Human Probability Bar */}
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-emerald-400">Human Probability</span>
              <span className="text-slate-200 font-bold">{humanPct}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
              <div
                style={{ width: `${humanPct}%` }}
                className="h-full rounded-full bg-emerald-400 transition-all duration-500"
              />
            </div>
          </div>

          {/* Synthetic Probability Bar */}
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-rose-400">Synthetic Probability</span>
              <span className="text-slate-200 font-bold">{synthPct}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
              <div
                style={{ width: `${synthPct}%` }}
                className="h-full rounded-full bg-rose-500 transition-all duration-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* Dual Inactive Indicator Gauges when awaiting inference */}
      {!hasInference && (
        <div className="grid grid-cols-2 gap-3 text-xs font-mono">
          <div className="rounded-lg bg-slate-900/30 border border-slate-800/60 p-2.5 space-y-1.5 opacity-60">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-400">P(Human)</span>
              <span className="text-slate-400">--%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-slate-800" />
          </div>

          <div className="rounded-lg bg-slate-900/30 border border-slate-800/60 p-2.5 space-y-1.5 opacity-60">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-400">P(Synthetic)</span>
              <span className="text-slate-400">--%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-slate-800" />
          </div>
        </div>
      )}
    </div>
  )
}
