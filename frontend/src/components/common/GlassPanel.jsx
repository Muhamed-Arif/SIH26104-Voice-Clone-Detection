import React from 'react'

export default function GlassPanel({
  title,
  subtitle,
  icon: Icon,
  action,
  children,
  className = '',
  glowing = false,
  highlightColor = 'cyan',
}) {
  const glowStyles = {
    cyan: 'shadow-[0_0_20px_rgba(6,182,212,0.06)] border-cyan-500/20',
    rose: 'shadow-[0_0_20px_rgba(244,63,94,0.08)] border-rose-500/30',
    emerald: 'shadow-[0_0_20px_rgba(16,185,129,0.08)] border-emerald-500/30',
    amber: 'shadow-[0_0_20px_rgba(245,158,11,0.08)] border-amber-500/30',
    default: 'border-slate-800/80 shadow-[0_4px_24px_rgba(0,0,0,0.4)]',
  }

  const borderGlow = glowing ? (glowStyles[highlightColor] || glowStyles.default) : glowStyles.default

  return (
    <div
      className={`relative rounded-xl bg-slate-900/40 backdrop-blur-xl border ${borderGlow} transition-all duration-300 ${className}`}
    >
      {/* Subtle tactical corner markers */}
      <div className="pointer-events-none absolute top-0 left-0 w-2 h-2 border-t border-l border-cyan-500/40 rounded-tl-sm" />
      <div className="pointer-events-none absolute top-0 right-0 w-2 h-2 border-t border-r border-cyan-500/40 rounded-tr-sm" />
      <div className="pointer-events-none absolute bottom-0 left-0 w-2 h-2 border-b border-l border-cyan-500/40 rounded-bl-sm" />
      <div className="pointer-events-none absolute bottom-0 right-0 w-2 h-2 border-b border-r border-cyan-500/40 rounded-br-sm" />

      {(title || subtitle || Icon || action) && (
        <div className="flex items-center justify-between border-b border-slate-800/60 px-4 py-3">
          <div className="flex items-center gap-2.5">
            {Icon && (
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Icon className="h-4 w-4" />
              </div>
            )}
            <div>
              {title && (
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-[11px] text-slate-400">{subtitle}</p>
              )}
            </div>
          </div>
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}

      <div className="p-4">{children}</div>
    </div>
  )
}
