import React from 'react'

export default function StatusPill({
  status = 'idle',
  label,
  size = 'md',
  pulse = true,
  className = '',
}) {
  const configs = {
    idle: {
      bg: 'bg-cyan-950/40 border-cyan-500/30 text-cyan-300',
      dot: 'bg-cyan-400',
      defaultLabel: 'STANDBY / IDLE',
    },
    analyzing: {
      bg: 'bg-amber-950/40 border-amber-500/40 text-amber-300',
      dot: 'bg-amber-400',
      defaultLabel: 'ANALYZING STREAM',
    },
    human: {
      bg: 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300',
      dot: 'bg-emerald-400',
      defaultLabel: 'VERIFIED HUMAN',
    },
    synthetic: {
      bg: 'bg-rose-950/50 border-rose-500/50 text-rose-300',
      dot: 'bg-rose-400',
      defaultLabel: 'SYNTHETIC CLONE DETECTED',
    },
    unknown: {
      bg: 'bg-orange-950/40 border-orange-500/40 text-orange-300',
      dot: 'bg-orange-400',
      defaultLabel: 'UNKNOWN SIGNATURE',
    },
    inconclusive: {
      bg: 'bg-violet-950/40 border-violet-500/40 text-violet-300',
      dot: 'bg-violet-400',
      defaultLabel: 'INCONCLUSIVE TELEMETRY',
    },
    online: {
      bg: 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300',
      dot: 'bg-emerald-400',
      defaultLabel: 'SYSTEM ONLINE',
    },
  }

  const current = configs[status.toLowerCase()] || configs.idle
  const displayText = label || current.defaultLabel

  const sizeStyles = {
    sm: 'text-[10px] px-2 py-0.5 gap-1.5',
    md: 'text-xs px-2.5 py-1 gap-2',
    lg: 'text-sm px-3 py-1.5 gap-2.5',
  }

  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
  }

  return (
    <span
      className={`inline-flex items-center rounded-full border font-mono font-medium uppercase tracking-wider backdrop-blur-sm transition-all duration-300 ${current.bg} ${sizeStyles[size] || sizeStyles.md} ${className}`}
    >
      <span className="relative flex">
        <span
          className={`rounded-full ${current.dot} ${dotSizes[size] || dotSizes.md} ${
            pulse ? 'animate-ping opacity-75' : ''
          }`}
        />
        <span
          className={`relative inline-flex rounded-full ${current.dot} ${dotSizes[size] || dotSizes.md}`}
        />
      </span>
      <span>{displayText}</span>
    </span>
  )
}
