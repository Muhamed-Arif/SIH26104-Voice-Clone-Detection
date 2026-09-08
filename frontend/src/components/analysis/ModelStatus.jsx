import React from 'react'
import { CpuIcon } from '../common/Icons'

export default function ModelStatus({
  modelVersion = null,
  latency = null,
}) {
  return (
    <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-3 font-mono">
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <CpuIcon className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Authenticity Detection Pipeline
          </span>
        </div>
        <span className="text-[10px] text-emerald-400 flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>BACKEND CONNECTED</span>
        </span>
      </div>

      <div className="space-y-2 text-xs">
        <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/70 flex justify-between items-center">
          <div>
            <span className="text-slate-200 block font-semibold text-[11px]">
              M2 Live Audio DSP
            </span>
            <span className="text-[10px] text-slate-400">2-second windows / 1-second hop / native-rate capture</span>
          </div>
          <span className="text-cyan-400 text-[11px]">ACTIVE</span>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/70 flex justify-between items-center gap-3">
          <div className="min-w-0">
            <span className="text-slate-200 block font-semibold text-[11px]">
              M1 Voice Authenticity Classifier
            </span>
            <span className="text-[10px] text-slate-400 block truncate">
              {modelVersion || 'Model version will appear after first inference'}
            </span>
          </div>
          <span className="text-cyan-400 text-[11px] shrink-0">READY</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[10px] pt-1">
        <div className="p-2 rounded bg-slate-900/40 border border-slate-800/60">
          <span className="text-slate-400 block">LAST E2E LATENCY</span>
          <span className="text-cyan-400 font-bold">
            {latency !== null ? `${Math.round(latency)} ms` : '-- ms'}
          </span>
        </div>
        <div className="p-2 rounded bg-slate-900/40 border border-slate-800/60">
          <span className="text-slate-400 block">RISK ENGINE</span>
          <span className="text-emerald-400 font-bold">ENABLED</span>
        </div>
      </div>
    </div>
  )
}
