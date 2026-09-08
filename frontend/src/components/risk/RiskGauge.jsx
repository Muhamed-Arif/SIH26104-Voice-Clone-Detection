import React from 'react'
import { ShieldAlertIcon } from '../common/Icons'

export default function RiskGauge({
  risk_level = null, // 'low' | 'moderate' | 'high' | 'critical' | null
  score = null, // 0 to 10
}) {
  const isAnalyzed = risk_level !== null

  const getRiskDetails = () => {
    switch (risk_level?.toLowerCase()) {
      case 'critical':
      case 'high':
        return {
          label: 'CRITICAL RISK',
          color: 'text-rose-400',
          bgColor: 'bg-rose-500',
          borderColor: 'border-rose-500/40',
          barWidth: `${Math.round((score || 9.2) * 10)}%`,
          desc: 'High probability synthetic speech clone detected.',
        }
      case 'moderate':
        return {
          label: 'MODERATE RISK',
          color: 'text-amber-400',
          bgColor: 'bg-amber-500',
          borderColor: 'border-amber-500/40',
          barWidth: `${Math.round((score || 5.5) * 10)}%`,
          desc: 'Atypical acoustic artifacts. Secondary inspection recommended.',
        }
      case 'low':
        return {
          label: 'LOW RISK',
          color: 'text-emerald-400',
          bgColor: 'bg-emerald-500',
          borderColor: 'border-emerald-500/40',
          barWidth: `${Math.round((score || 0.6) * 10)}%`,
          desc: 'Authentic human vocal dynamics confirmed.',
        }
      default:
        return {
          label: 'NOT ANALYZED',
          color: 'text-slate-400',
          bgColor: 'bg-slate-700',
          borderColor: 'border-slate-800/80',
          barWidth: '0%',
          desc: 'Awaiting audio ingestion and model inference evaluation.',
        }
    }
  }

  const current = getRiskDetails()

  return (
    <div className={`rounded-xl border ${current.borderColor} bg-slate-950/70 p-4 backdrop-blur-md space-y-4`}>
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <ShieldAlertIcon className={`h-4 w-4 ${isAnalyzed ? current.color : 'text-slate-400'}`} />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Acoustic Risk Index
          </span>
        </div>
        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border bg-slate-900 ${current.color} ${current.borderColor}`}>
          {current.label}
        </span>
      </div>

      <div className="flex items-end justify-between font-mono">
        <div>
          <span className="text-[10px] text-slate-400 uppercase block">Severity Score</span>
          <div className={`text-2xl font-bold ${current.color}`}>
            {isAnalyzed && score !== null ? `${score.toFixed(1)} / 10` : '0.0 / 10'}
          </div>
        </div>
        <span className="text-[10px] text-slate-400 uppercase">
          {isAnalyzed ? 'CALCULATED' : 'STANDBY'}
        </span>
      </div>

      {/* Meter Bar */}
      <div className="space-y-1 font-mono text-[10px]">
        <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
          <div
            style={{ width: current.barWidth }}
            className={`h-full rounded-full transition-all duration-500 ${current.bgColor}`}
          />
        </div>
        <div className="flex justify-between text-slate-400">
          <span>0.0 (HUMAN)</span>
          <span>5.0 (SUSPECT)</span>
          <span>10.0 (SYNTHETIC)</span>
        </div>
      </div>

      <p className="text-[11px] text-slate-400 leading-relaxed font-mono">
        {current.desc}
      </p>
    </div>
  )
}
