import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  ActivityIcon,
  RadioIcon,
  WaveformIcon,
  ShieldAlertIcon,
  FileTextIcon,
  SettingsIcon,
  CpuIcon,
  ShieldCheckIcon,
} from '../common/Icons'

const navItems = [
  { name: 'Command Center', path: '/', icon: ActivityIcon },
  { name: 'Live Analysis', path: '/live-analysis', icon: RadioIcon },
  { name: 'Voice Lab', path: '/voice-lab', icon: WaveformIcon },
  { name: 'Threat Intelligence', path: '/threat-intelligence', icon: ShieldAlertIcon },
  { name: 'Reports', path: '/reports', icon: FileTextIcon },
  { name: 'Settings', path: '/settings', icon: SettingsIcon },
]

export default function Sidebar() {
  return (
    <aside className="relative flex flex-col w-64 shrink-0 border-r border-slate-800/80 bg-slate-950/80 backdrop-blur-2xl h-screen select-none z-30">
      {/* Brand Header */}
      <div className="flex flex-col gap-2 p-5 border-b border-slate-800/60">
        <div className="flex items-center gap-3">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/40 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.25)]">
            <ShieldCheckIcon className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
            </span>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-base font-bold tracking-wider text-white">AETHER</span>
              <span className="text-base font-light tracking-wider text-cyan-400">VOICE</span>
            </div>
            <p className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
              Impersonation Defense
            </p>
          </div>
        </div>

        <div className="mt-1 flex items-center justify-between rounded-md bg-slate-900/60 px-2.5 py-1 text-[10px] font-mono border border-slate-800/80">
          <span className="text-slate-400">PROBLEM STATEMENT</span>
          <span className="text-cyan-400 font-semibold">SIH26104</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1.5 px-3 py-4 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
          Operations
        </div>
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-xs font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.1)]'
                    : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200 border border-transparent'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 rounded-r bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
                  )}
                  <Icon
                    className={`h-4 w-4 transition-colors ${
                      isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-slate-300'
                    }`}
                  />
                  <span className="tracking-wide">{item.name}</span>
                </>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* SOC Telemetry Footer */}
      <div className="p-3 border-t border-slate-800/60 bg-slate-950/60">
        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-3 space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="flex items-center gap-1.5 text-slate-400">
              <CpuIcon className="h-3.5 w-3.5 text-cyan-400" />
              <span>Neural Engine</span>
            </span>
            <span className="font-mono text-emerald-400 text-[10px]">READY</span>
          </div>
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1 border-t border-slate-800/50">
            <span>SOC Node: IND-CENTRAL</span>
            <span className="text-slate-400">v1.0.4-rc</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
