import React from 'react'
import { CpuIcon, ClockIcon, ActivityIcon, ShieldCheckIcon } from '../common/Icons'
import StatusPill from '../common/StatusPill'

export default function AnalysisPanel({
  status = 'WAITING', // 'WAITING' | 'RECORDING' | 'PROCESSING' | 'WAITING FOR MODEL' | 'COMPLETE'
  audioQuality = 'AWAITING INPUT',
  processingStage = 'INGESTION STANDBY',
  modelStatus = 'ONLINE // AWAITING STREAM',
  duration = 0,
}) {
  const formatTime = (sec) => {
    const mins = Math.floor(sec / 60)
    const s = sec % 60
    return `${mins.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  const getStatusColor = () => {
    switch (status) {
      case 'RECORDING':
        return 'text-rose-400'
      case 'PROCESSING':
        return 'text-amber-400'
      case 'WAITING FOR MODEL':
        return 'text-cyan-400'
      case 'COMPLETE':
        return 'text-emerald-400'
      default:
        return 'text-slate-400'
    }
  }

  const getPillKey = () => {
    switch (status) {
      case 'RECORDING':
        return 'analyzing'
      case 'PROCESSING':
        return 'analyzing'
      case 'COMPLETE':
        return 'human'
      default:
        return 'idle'
    }
  }

  return (
    <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <ActivityIcon className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Analysis Telemetry
          </span>
        </div>
        <StatusPill status={getPillKey()} label={status} size="sm" />
      </div>

      <div className="grid grid-cols-2 gap-3 font-mono">
        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-2.5">
          <span className="text-[10px] text-slate-400 block">ANALYSIS STATUS</span>
          <span className={`text-xs font-bold ${getStatusColor()}`}>{status}</span>
        </div>

        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-2.5">
          <span className="text-[10px] text-slate-400 block">AUDIO QUALITY</span>
          <span className="text-xs font-bold text-slate-200">{audioQuality}</span>
        </div>

        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-2.5">
          <span className="text-[10px] text-slate-400 block">PROCESSING STAGE</span>
          <span className="text-xs font-bold text-cyan-400">{processingStage}</span>
        </div>

        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-2.5">
          <span className="text-[10px] text-slate-400 block">ANALYSIS DURATION</span>
          <span className="text-xs font-bold text-slate-200 flex items-center gap-1">
            <ClockIcon className="h-3 w-3 text-slate-400" />
            <span>{formatTime(duration)}</span>
          </span>
        </div>
      </div>

      {/* Model Diagnostic */}
      <div className="rounded-lg bg-slate-900/40 border border-slate-800/70 p-2.5 text-xs font-mono space-y-1">
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-slate-400 flex items-center gap-1">
            <CpuIcon className="h-3.5 w-3.5 text-cyan-400" />
            <span>MODEL STATUS</span>
          </span>
          <span className="text-emerald-400">{modelStatus}</span>
        </div>
      </div>

      {/* Explicit Backend Disclaimer */}
      <div className="rounded-md bg-slate-900/30 border border-slate-800/60 px-2.5 py-1.5 text-[10px] font-mono text-slate-400 flex items-center gap-2">
        <ShieldCheckIcon className="h-3 w-3 text-cyan-500 shrink-0" />
        <span>Inference pipeline will activate upon live backend endpoint handshake.</span>
      </div>
    </div>
  )
}
