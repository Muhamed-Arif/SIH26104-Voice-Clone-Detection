import React from 'react'
import { ShieldAlertIcon } from '../common/Icons'

export default function PreventionStatus({
  verdict = 'WAITING',
  preventionStatus = 'STANDBY',
  autoIntercept = true,
}) {
  const action = String(preventionStatus || 'STANDBY').toUpperCase()
  const isTriggered = action === 'BLOCK' || verdict?.toLowerCase() === 'synthetic'

  return (
    <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <ShieldAlertIcon className={`h-4 w-4 ${isTriggered ? 'text-rose-400' : 'text-cyan-400'}`} />
          <span className="font-semibold uppercase tracking-wider text-slate-200">
            Sensitive Action Guard
          </span>
        </div>
        <span
          className={`text-[10px] px-2 py-0.5 rounded border ${
            isTriggered
              ? 'bg-rose-950/60 border-rose-500/50 text-rose-300'
              : action === 'ALLOW'
                ? 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300'
                : 'bg-slate-900 border-slate-800 text-slate-400'
          }`}
        >
          {action}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px]">
        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800/70">
          <span className="text-[10px] text-slate-400 block">CURRENT VERDICT</span>
          <span
            className={`font-bold ${
              verdict === 'SYNTHETIC'
                ? 'text-rose-400'
                : verdict === 'HUMAN'
                  ? 'text-emerald-400'
                  : 'text-slate-300'
            }`}
          >
            {verdict}
          </span>
        </div>

        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800/70">
          <span className="text-[10px] text-slate-400 block">POLICY MODE</span>
          <span className="text-cyan-400 font-bold">
            {autoIntercept ? 'AUTO-GATE' : 'ALERT ONLY'}
          </span>
        </div>
      </div>

      <div className={`rounded-lg border p-3 text-[11px] leading-relaxed ${
        isTriggered
          ? 'border-rose-500/30 bg-rose-950/20 text-rose-200'
          : action === 'ALLOW'
            ? 'border-emerald-500/25 bg-emerald-950/15 text-emerald-200'
            : 'border-slate-800/70 bg-slate-900/40 text-slate-400'
      }`}>
        {isTriggered
          ? 'High-risk synthetic speech detected. The prototype blocks the sensitive action and should request secondary verification such as OTP, PIN, or trusted-device approval.'
          : action === 'ALLOW'
            ? 'Voice authenticity risk is low. The sensitive action may continue under the current policy.'
            : 'Waiting for a live authenticity decision before allowing or blocking a sensitive action.'}
      </div>
    </div>
  )
}
