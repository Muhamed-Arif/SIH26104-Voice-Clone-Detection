import React from 'react'
import { FingerprintIcon } from '../common/Icons'

function Meter({ label, value = null, suffix = '%', dangerHigh = true, description }) {
  const pct = value === null ? null : Math.max(0, Math.min(100, Math.round(value * 100)))
  const danger = pct !== null && (dangerHigh ? pct >= 70 : pct <= 30)

  return (
    <div className="rounded-lg bg-slate-900/50 border border-slate-800/70 p-3 space-y-1.5">
      <div className="flex items-center justify-between gap-3">
        <span className="text-slate-300 font-medium">{label}</span>
        <span className={pct !== null ? (danger ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold') : 'text-slate-400'}>
          {pct !== null ? `${pct}${suffix}` : 'STANDBY'}
        </span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
        <div
          style={{ width: pct !== null ? `${pct}%` : '0%' }}
          className={`h-full rounded-full transition-all duration-500 ${danger ? 'bg-rose-500' : 'bg-cyan-500'}`}
        />
      </div>
      <p className="text-[10px] text-slate-400 font-sans leading-relaxed">{description}</p>
    </div>
  )
}

export default function ReasonCodes({ evidence = null }) {
  const hasEvidence = evidence !== null && typeof evidence === 'object'
  const reasonCodes = hasEvidence && Array.isArray(evidence.reasonCodes) ? evidence.reasonCodes : []

  return (
    <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <FingerprintIcon className="h-4 w-4 text-cyan-400" />
          <span className="font-semibold uppercase tracking-wider text-slate-200">
            Detection Evidence
          </span>
        </div>
        <span className="text-[10px] text-slate-400">
          {hasEvidence ? 'LIVE TELEMETRY' : 'AWAITING TELEMETRY'}
        </span>
      </div>

      <div className="space-y-2.5">
        <Meter
          label="Synthetic Probability"
          value={hasEvidence ? evidence.syntheticProbability : null}
          description="Probability returned by the active M1 authenticity model for the current audio chunk."
        />
        <Meter
          label="Risk Engine Score"
          value={hasEvidence ? evidence.riskScore : null}
          description="Backend risk score after combining model output, quality checks, and prevention policy."
        />
        <Meter
          label="Prediction Confidence"
          value={hasEvidence ? evidence.confidence : null}
          dangerHigh={false}
          description="Confidence attached to the current REAL / AI_GENERATED model decision."
        />
      </div>

      {reasonCodes.length > 0 && (
        <div className="rounded-lg bg-slate-900/40 border border-slate-800/60 p-2.5">
          <span className="text-[10px] text-slate-400 block mb-1.5">BACKEND REASON CODES</span>
          <div className="flex flex-wrap gap-1.5">
            {reasonCodes.map((code) => (
              <span key={code} className="rounded border border-cyan-500/20 bg-cyan-950/20 px-2 py-0.5 text-[10px] text-cyan-300">
                {code}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
