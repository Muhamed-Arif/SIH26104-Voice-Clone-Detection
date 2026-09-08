import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import NeuralCore from '../components/3d/NeuralCore'
import GlassPanel from '../components/common/GlassPanel'
import StatusPill from '../components/common/StatusPill'
import {
  ActivityIcon,
  RadioIcon,
  WaveformIcon,
  ShieldCheckIcon,
  ShieldAlertIcon,
  CpuIcon,
  BarChartIcon,
  FingerprintIcon,
  ChevronRightIcon,
} from '../components/common/Icons'

const STATE_DETAILS = {
  idle: {
    label: 'STANDBY / IDLE',
    pillStatus: 'idle',
    modelStatus: 'READY // AWAITING STREAM',
    audioInput: 'NO ACTIVE INGESTION',
    confidence: '---',
    confidenceVal: 0,
    riskLevel: 'NOMINAL',
    riskScore: '0.0 / 10',
    riskColor: 'text-slate-400',
    detectionState: 'System idle. Ingestion buffers clear.',
  },
  analyzing: {
    label: 'ANALYZING STREAM',
    pillStatus: 'analyzing',
    modelStatus: 'PROCESSING LIVE ACOUSTIC FEATURES',
    audioInput: 'LIVE MICROPHONE STREAM',
    confidence: 'EVALUATING...',
    confidenceVal: 65,
    riskLevel: 'ASSESSING',
    riskScore: 'CALCULATING',
    riskColor: 'text-amber-400',
    detectionState: 'Extracting acoustic statistics and evaluating synthetic-voice probability...',
  },
  human: {
    label: 'VERIFIED AUTHENTIC HUMAN',
    pillStatus: 'human',
    modelStatus: 'INFERENCE COMPLETE // LOW RISK',
    audioInput: 'LIVE MICROPHONE STREAM',
    confidence: '99.2%',
    confidenceVal: 99,
    riskLevel: 'LOW',
    riskScore: '0.4 / 10',
    riskColor: 'text-emerald-400',
    detectionState: 'Low synthetic probability and low backend risk score in this demo state.',
  },
  synthetic: {
    label: 'SYNTHETIC CLONE DETECTED',
    pillStatus: 'synthetic',
    modelStatus: 'THREAT DETECTED // HIGH CERTAINTY',
    audioInput: 'LIVE MICROPHONE STREAM',
    confidence: '98.8%',
    confidenceVal: 98,
    riskLevel: 'CRITICAL',
    riskScore: '9.7 / 10',
    riskColor: 'text-rose-400',
    detectionState: 'High synthetic probability and high backend risk score in this demo state.',
  },
  unknown: {
    label: 'UNKNOWN SIGNATURE',
    pillStatus: 'unknown',
    modelStatus: 'IRREGULAR SPECTRAL ANOMALY',
    audioInput: 'LIVE MICROPHONE STREAM',
    confidence: '54.1%',
    confidenceVal: 54,
    riskLevel: 'MODERATE',
    riskScore: '5.8 / 10',
    riskColor: 'text-orange-400',
    detectionState: 'Uncertain acoustic profile. Secondary verification is recommended.',
  },
  inconclusive: {
    label: 'INCONCLUSIVE TELEMETRY',
    pillStatus: 'inconclusive',
    modelStatus: 'LOW SIGNAL-TO-NOISE RATIO',
    audioInput: 'STREAM #01 (High Ambient Noise)',
    confidence: '38.0%',
    confidenceVal: 38,
    riskLevel: 'UNVERIFIED',
    riskScore: '3.2 / 10',
    riskColor: 'text-violet-400',
    detectionState: 'Excessive environmental noise masking vocal tract frequencies.',
  },
}

export default function Home() {
  const [analysisState, setAnalysisState] = useState('idle')
  const details = STATE_DETAILS[analysisState] || STATE_DETAILS.idle

  const statesList = [
    { id: 'idle', label: 'Idle' },
    { id: 'analyzing', label: 'Analyzing' },
    { id: 'human', label: 'Human' },
    { id: 'synthetic', label: 'Synthetic' },
    { id: 'unknown', label: 'Unknown' },
    { id: 'inconclusive', label: 'Inconclusive' },
  ]

  return (
    <div className="space-y-6 pb-6">
      {/* Top Banner: SOC Overview & Interactive State Simulator */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Command Center
            </h1>
            <StatusPill status={analysisState} size="sm" />
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Real-Time Acoustic Impersonation Vector Defense // SIH26104 SOC Telemetry
          </p>
        </div>

        {/* State Simulation Bar for Judges / Presentation */}
        <div className="flex flex-wrap items-center gap-1.5 rounded-xl border border-slate-800/80 bg-slate-900/50 p-1.5 backdrop-blur-md">
          <span className="px-2 text-[10px] font-mono font-medium text-slate-400 uppercase tracking-wider">
            Simulate State:
          </span>
          {statesList.map((s) => {
            const isActive = analysisState === s.id
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => setAnalysisState(s.id)}
                className={`rounded-lg px-2.5 py-1 text-xs font-mono font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_12px_rgba(6,182,212,0.25)]'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'
                }`}
              >
                {s.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Main Grid: 3D Voice Core (Left/Center) + System Intelligence (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Left/Center: Interactive 3D Voice Core */}
        <div className="lg:col-span-7 xl:col-span-8 flex flex-col">
          <GlassPanel
            title="3D Voice Authenticity Core"
            subtitle="Live detection-state visualization"
            icon={CpuIcon}
            glowing={analysisState === 'synthetic'}
            highlightColor={analysisState === 'synthetic' ? 'rose' : 'cyan'}
            action={
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-slate-400 hidden sm:inline">
                  ORBIT: DRAG TO ROTATE
                </span>
                <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse"></span>
              </div>
            }
            className="flex-1 flex flex-col overflow-hidden min-h-[440px] xl:min-h-[520px]"
          >
            <div className="relative flex-1 w-full rounded-lg bg-slate-950/60 border border-slate-800/60 overflow-hidden flex items-center justify-center">
              {/* Radial gradient background behind core */}
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(6,182,212,0.08)_0%,transparent_70%)] pointer-events-none" />
              
              {/* 3D Scene */}
              <NeuralCore state={analysisState} />
            </div>

            {/* Core Telemetry Sub-strip */}
            <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
              <div className="rounded bg-slate-950/50 border border-slate-800/60 p-2">
                <span className="text-slate-400 block text-[10px]">RESONATOR MODE</span>
                <span className="text-cyan-300 font-semibold uppercase">{analysisState}</span>
              </div>
              <div className="rounded bg-slate-950/50 border border-slate-800/60 p-2">
                <span className="text-slate-400 block text-[10px]">ACOUSTIC BANDS</span>
                <span className="text-slate-200 font-semibold">30 Acoustic Features</span>
              </div>
              <div className="rounded bg-slate-950/50 border border-slate-800/60 p-2">
                <span className="text-slate-400 block text-[10px]">LATENT NODES</span>
                <span className="text-slate-200 font-semibold">Backend Risk Engine</span>
              </div>
              <div className="rounded bg-slate-950/50 border border-slate-800/60 p-2">
                <span className="text-slate-400 block text-[10px]">DSP SAMPLING</span>
                <span className="text-emerald-400 font-semibold">Native → 16 kHz</span>
              </div>
            </div>
          </GlassPanel>
        </div>

        {/* Right: System Intelligence Panel */}
        <div className="lg:col-span-5 xl:col-span-4 flex flex-col space-y-4">
          <GlassPanel
            title="System Intelligence"
            subtitle="Deepfake & Voice Clone Telemetry"
            icon={ShieldAlertIcon}
            className="flex-1 flex flex-col justify-between"
          >
            <div className="space-y-4">
              {/* Analysis Status & Detection State */}
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                  Current Detection State
                </span>
                <div className="mt-1.5 flex items-center justify-between rounded-lg bg-slate-950/80 border border-slate-800/90 p-3">
                  <div className="space-y-1">
                    <StatusPill status={details.pillStatus} size="sm" />
                    <p className="text-xs text-slate-300 leading-relaxed pt-1">
                      {details.detectionState}
                    </p>
                  </div>
                </div>
              </div>

              {/* Confidence Meter */}
              <div className="rounded-lg bg-slate-950/60 border border-slate-800/80 p-3 space-y-2">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">MODEL CONFIDENCE</span>
                  <span className="text-cyan-400 font-bold">{details.confidence}</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full ${
                      analysisState === 'synthetic'
                        ? 'bg-gradient-to-r from-rose-500 to-red-600'
                        : analysisState === 'human'
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                        : 'bg-gradient-to-r from-cyan-500 to-blue-500'
                    }`}
                    initial={{ width: '0%' }}
                    animate={{ width: `${details.confidenceVal}%` }}
                    transition={{ duration: 0.6, ease: 'easeOut' }}
                  />
                </div>
              </div>

              {/* Risk Level Gauge */}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-slate-950/60 border border-slate-800/80 p-3">
                  <span className="text-[10px] font-mono uppercase text-slate-400">Risk Assessment</span>
                  <div className={`mt-1 text-lg font-bold font-mono ${details.riskColor}`}>
                    {details.riskLevel}
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">{details.riskScore}</span>
                </div>

                <div className="rounded-lg bg-slate-950/60 border border-slate-800/80 p-3">
                  <span className="text-[10px] font-mono uppercase text-slate-400">Engine State</span>
                  <div className="mt-1 text-sm font-bold font-mono text-cyan-300">
                    INSPECTING
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">Dual Neural Stream</span>
                </div>
              </div>

              {/* Model & Stream Diagnostics */}
              <div className="space-y-2 text-xs font-mono pt-1">
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-400">ANALYSIS STATUS</span>
                  <span className="text-slate-200">{details.label}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-400">MODEL INFERENCE</span>
                  <span className="text-slate-200 text-right">{details.modelStatus}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-400">AUDIO INPUT</span>
                  <span className="text-cyan-400 text-right">{details.audioInput}</span>
                </div>
              </div>
            </div>

            {/* Note confirming demo telemetry */}
            <div className="mt-4 rounded-md bg-cyan-950/20 border border-cyan-500/20 p-2.5 text-[10px] font-mono text-cyan-400/80 flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 shrink-0"></span>
              <span>TELEMETRY: DEMO / SIMULATION MODE (SIH PROTOTYPE)</span>
            </div>
          </GlassPanel>
        </div>
      </div>

      {/* Bottom Section: Quick Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/live-analysis"
          className="group relative block rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 backdrop-blur-xl transition-all hover:border-cyan-500/40 hover:bg-slate-900/70 hover:shadow-[0_0_20px_rgba(6,182,212,0.12)]"
        >
          <div className="flex items-start justify-between">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 group-hover:scale-105 transition-transform">
              <RadioIcon className="h-5 w-5" />
            </div>
            <ChevronRightIcon className="h-4 w-4 text-slate-400 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="mt-3 text-sm font-semibold text-white group-hover:text-cyan-300 transition-colors">
            Start Live Analysis
          </h3>
          <p className="mt-1 text-xs text-slate-400 leading-relaxed">
            Attach real-time microphone or RTMP audio feed for instantaneous clone detection.
          </p>
        </Link>

        <Link
          to="/voice-lab"
          className="group relative block rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 backdrop-blur-xl transition-all hover:border-blue-500/40 hover:bg-slate-900/70 hover:shadow-[0_0_20px_rgba(59,130,246,0.12)]"
        >
          <div className="flex items-start justify-between">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 group-hover:scale-105 transition-transform">
              <WaveformIcon className="h-5 w-5" />
            </div>
            <ChevronRightIcon className="h-4 w-4 text-slate-400 group-hover:text-blue-400 group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="mt-3 text-sm font-semibold text-white group-hover:text-blue-300 transition-colors">
            Open Voice Lab
          </h3>
          <p className="mt-1 text-xs text-slate-400 leading-relaxed">
            Deep-dive forensic spectrogram analysis, harmonic distortion, and vocoder artifact inspection.
          </p>
        </Link>

        <button
          type="button"
          onClick={() => setAnalysisState(analysisState === 'synthetic' ? 'human' : 'synthetic')}
          className="group relative text-left w-full rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 backdrop-blur-xl transition-all hover:border-violet-500/40 hover:bg-slate-900/70 hover:shadow-[0_0_20px_rgba(139,92,246,0.12)]"
        >
          <div className="flex items-start justify-between">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-500/10 border border-violet-500/30 text-violet-400 group-hover:scale-105 transition-transform">
              <FingerprintIcon className="h-5 w-5" />
            </div>
            <ChevronRightIcon className="h-4 w-4 text-slate-400 group-hover:text-violet-400 group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="mt-3 text-sm font-semibold text-white group-hover:text-violet-300 transition-colors">
            Verify Voice Sample
          </h3>
          <p className="mt-1 text-xs text-slate-400 leading-relaxed">
            Toggle simulated attack vs genuine voice sample verification test in the 3D core.
          </p>
        </button>
      </div>

      {/* Small System Metrics (Clearly Marked Demo / UI Values) */}
      <div className="border-t border-slate-800/80 pt-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            System Telemetry Metrics
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            [DEMO / BENCHMARK VALUES]
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/30 p-3.5 backdrop-blur-md">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Audio Streams</span>
              <ActivityIcon className="h-4 w-4 text-cyan-400" />
            </div>
            <div className="mt-2 text-xl font-bold font-mono text-white">4 Active</div>
            <span className="text-[10px] font-mono text-emerald-400">100% Ingestion Uptime</span>
          </div>

          <div className="rounded-xl border border-slate-800/80 bg-slate-900/30 p-3.5 backdrop-blur-md">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Analyses Today</span>
              <BarChartIcon className="h-4 w-4 text-blue-400" />
            </div>
            <div className="mt-2 text-xl font-bold font-mono text-white">1,428</div>
            <span className="text-[10px] font-mono text-cyan-400">Avg 42ms Latency</span>
          </div>

          <div className="rounded-xl border border-slate-800/80 bg-slate-900/30 p-3.5 backdrop-blur-md">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Threats Detected</span>
              <ShieldAlertIcon className="h-4 w-4 text-rose-400" />
            </div>
            <div className="mt-2 text-xl font-bold font-mono text-rose-300">19</div>
            <span className="text-[10px] font-mono text-rose-400">14 Impersonations Intercepted</span>
          </div>

          <div className="rounded-xl border border-slate-800/80 bg-slate-900/30 p-3.5 backdrop-blur-md">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Model Accuracy</span>
              <ShieldCheckIcon className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-2 text-xl font-bold font-mono text-emerald-300">99.4%</div>
            <span className="text-[10px] font-mono text-slate-400">ASVspoof 5 Evaluation</span>
          </div>
        </div>
      </div>
    </div>
  )
}
