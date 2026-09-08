import React from 'react'

export default function RiskBadge({
  risk_level = null,
  size = 'md',
  className = '',
}) {
  const configs = {
    critical: {
      bg: 'bg-rose-950/60 border-rose-500/50 text-rose-300',
      dot: 'bg-rose-400',
      label: 'CRITICAL THREAT',
    },
    high: {
      bg: 'bg-rose-950/50 border-rose-500/40 text-rose-300',
      dot: 'bg-rose-400',
      label: 'HIGH RISK',
    },
    moderate: {
      bg: 'bg-amber-950/50 border-amber-500/40 text-amber-300',
      dot: 'bg-amber-400',
      label: 'MODERATE RISK',
    },
    low: {
      bg: 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300',
      dot: 'bg-emerald-400',
      label: 'LOW RISK // AUTHENTIC',
    },
    default: {
      bg: 'bg-slate-900/60 border-slate-800 text-slate-400',
      dot: 'bg-slate-500',
      label: 'NOT ANALYZED // STANDBY',
    },
  }

  const current = (risk_level && configs[risk_level.toLowerCase()]) || configs.default

  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5 gap-1.5',
    md: 'text-xs px-2.5 py-1 gap-2',
    lg: 'text-sm px-3 py-1.5 gap-2.5',
  }

  return (
    <span
      className={`inline-flex items-center rounded-full border font-mono font-semibold uppercase tracking-wider backdrop-blur-sm ${current.bg} ${sizeClasses[size] || sizeClasses.md} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${current.dot}`} />
      <span>{current.label}</span>
    </span>
  )
}
