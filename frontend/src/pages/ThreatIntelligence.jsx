import React from 'react'
import GlassPanel from '../components/common/GlassPanel'
import { ShieldAlertIcon, TerminalIcon, CpuIcon, AlertTriangleIcon } from '../components/common/Icons'

export default function ThreatIntelligence() {
  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
            <ShieldAlertIcon className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Threat Intelligence
            </h1>
            <p className="text-xs text-slate-400">
              Global Voice Cloning CVEs, Deepfake Campaign Feeds & Impersonation Signatures
            </p>
          </div>
        </div>
      </div>

      {/* Module Under Development Notice */}
      <div className="rounded-xl border border-rose-500/30 bg-gradient-to-r from-rose-950/40 via-slate-900/60 to-slate-950/80 p-5 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
          </span>
          <div>
            <h2 className="text-sm font-semibold text-rose-300">
              Module Under Development // Threat Intelligence Hub
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live threat intelligence feeds for zero-day speech synthesis models, CEO fraud patterns, and biometric spoofing telemetry.
            </p>
          </div>
        </div>
      </div>

      {/* Intelligence Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassPanel
          title="Known Attack Signatures"
          subtitle="Voice Cloning Vectors"
          icon={AlertTriangleIcon}
        >
          <div className="space-y-2 text-xs font-mono text-slate-400">
            <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80 flex justify-between">
              <span>Zero-Shot TTS (Bark / XTTS)</span>
              <span className="text-rose-400">HIGH RISK</span>
            </div>
            <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80 flex justify-between">
              <span>Diffusion Voice Conversion (RVC)</span>
              <span className="text-rose-400">CRITICAL</span>
            </div>
            <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80 flex justify-between">
              <span>Speech Resynthesis (VALL-E)</span>
              <span className="text-amber-400">MODERATE</span>
            </div>
          </div>
        </GlassPanel>

        <GlassPanel
          title="Attribution Engine"
          subtitle="Acoustic Watermark Correlation"
          icon={CpuIcon}
        >
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs font-mono text-slate-400 space-y-2">
            <div className="text-cyan-400">SIGNATURE MATCH ENGINE</div>
            <p className="text-[11px] leading-relaxed">
              Designed to evaluate synthetic and replayed speech across multiple generators and call conditions; unseen-source testing is tracked separately.
            </p>
          </div>
        </GlassPanel>

        <GlassPanel
          title="SOC Incident Feed"
          subtitle="Real-time Interception Logs"
          icon={TerminalIcon}
        >
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs font-mono text-slate-400 space-y-1.5">
            <div className="text-emerald-400">STATUS: MONITORING FEED</div>
            <div className="text-[11px] text-slate-400">INCIDENT #0849: Intercepted synthetic audio stream (Confidence: 98.4%)</div>
            <div className="text-[11px] text-slate-400">INCIDENT #0848: Acoustic anomaly flagged on executive line</div>
          </div>
        </GlassPanel>
      </div>
    </div>
  )
}
