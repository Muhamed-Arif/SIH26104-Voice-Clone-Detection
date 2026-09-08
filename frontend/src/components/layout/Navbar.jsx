import React, { useEffect, useState } from 'react'
import { BellIcon, ShieldCheckIcon } from '../common/Icons'
import StatusPill from '../common/StatusPill'
import { checkBackendHealth } from '../../services/api'

export default function Navbar() {
  const [timeString, setTimeString] = useState('')
  const [health, setHealth] = useState({ status: 'checking', database: '?', model: 'checking' })

  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setTimeString(now.toLocaleTimeString())
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    let cancelled = false
    const refresh = async () => {
      try {
        const response = await checkBackendHealth()
        const data = response.data || {}
        const ml = data.ml || {}
        if (!cancelled) {
          setHealth({
            status: data.status === 'ok' ? 'online' : 'warning',
            database: data.database || 'unknown',
            model: ml.model_version || ml.status || 'unknown',
          })
        }
      } catch (_) {
        if (!cancelled) setHealth({ status: 'offline', database: 'offline', model: 'offline' })
      }
    }
    refresh()
    const timer = setInterval(refresh, 10000)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-slate-800/80 bg-slate-950/70 px-6 backdrop-blur-xl select-none">
      <div className="flex items-center gap-4 min-w-0">
        <div className="flex items-center gap-2">
          <StatusPill
            status={health.status === 'online' ? 'online' : health.status === 'offline' ? 'synthetic' : 'analyzing'}
            label={health.status.toUpperCase()}
            size="sm"
          />
        </div>

        <div className="hidden md:flex items-center gap-2 rounded-md bg-slate-900/60 px-2.5 py-1 text-[11px] font-mono text-slate-300 border border-slate-800/80 min-w-0">
          <span className={`h-1.5 w-1.5 rounded-full ${health.status === 'online' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
          <span>DB:</span>
          <span className="text-cyan-400 font-semibold">{health.database}</span>
          <span className="text-slate-600">•</span>
          <span className="text-slate-400 truncate max-w-[260px]">ML {health.model}</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden lg:flex flex-col items-end">
          <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-400">
            <span className="text-[10px] text-slate-400">LOCAL TIME:</span>
            <span>{timeString || '--:--:--'}</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">PIPELINE: FRONTEND → M2 → M1 → RISK</span>
        </div>

        <div className="h-6 w-px bg-slate-800 hidden sm:block" />

        <button
          type="button"
          aria-label="System Notifications"
          className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/60 text-slate-300 transition-colors hover:border-cyan-500/40 hover:text-cyan-300"
        >
          <BellIcon className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-3 pl-1">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-500/30 bg-gradient-to-tr from-cyan-950 to-blue-900/60 text-cyan-400 font-mono text-xs font-bold shadow-[0_0_10px_rgba(6,182,212,0.15)]">
            SIH
          </div>
          <div className="hidden xl:flex flex-col text-left">
            <div className="flex items-center gap-1 text-xs font-semibold text-slate-200">
              <span>AetherVoice</span>
              <ShieldCheckIcon className="h-3 w-3 text-cyan-400" />
            </div>
            <span className="text-[10px] font-mono text-slate-400">SIH26104 Prototype</span>
          </div>
        </div>
      </div>
    </header>
  )
}
