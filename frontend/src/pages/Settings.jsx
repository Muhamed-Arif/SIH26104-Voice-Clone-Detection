import React, { useState, useCallback } from "react"
import { motion } from "framer-motion"
import GlassPanel from "../components/common/GlassPanel"
import {
  SettingsIcon,
  CpuIcon,
  ShieldCheckIcon,
  BellIcon,
  ActivityIcon,
  WaveformIcon,
  InfoIcon,
  RefreshCwIcon,
  CheckCircleIcon,
} from "../components/common/Icons"

const DEFAULTS = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "",
  analysisTimeout: 30,
  maxFileSize: 50,
  syntheticThreshold: 75,
  humanThreshold: 85,
  confidenceMinimum: 60,
  sampleRate: 16000,
  chunkDuration: 2,
  overlapDuration: 1,
  enablePreProcessing: true,
  noiseReduction: 50,
  highRiskAlert: true,
  syntheticAlert: true,
  analysisCompleteAlert: true,
  alertSound: false,
  show3DCore: true,
  reduceMotion: false,
  showConfidencePercentages: true,
  showChunkTimeline: true,
}

const STORAGE_KEY = "aethervoice_settings"

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) }
  } catch (_) {}
  return { ...DEFAULTS }
}

function SaveBar({ onSave, saved }) {
  return (
    <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800/60 mt-3">
      {saved && (
        <span className="flex items-center gap-1.5 text-xs text-emerald-400">
          <CheckCircleIcon className="h-3.5 w-3.5" />
          Saved
        </span>
      )}
      <button
        onClick={onSave}
        className="px-4 py-1.5 text-xs font-semibold uppercase tracking-wider rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/25 hover:border-cyan-400/50 transition-all duration-200"
      >
        Save
      </button>
    </div>
  )
}

function SliderField({ label, value, min = 0, max = 100, step = 1, unit = "%", onChange }) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-400">{label}</span>
        <span className="text-xs font-mono font-semibold text-cyan-300">{value}{unit}</span>
      </div>
      <div className="relative h-1.5 rounded-full bg-slate-800 overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full appearance-none bg-transparent cursor-pointer mt-[-10px] [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-cyan-400 [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-slate-900 [&::-webkit-slider-thumb]:cursor-pointer"
      />
    </div>
  )
}

function ToggleField({ label, description, value, onChange }) {
  return (
    <div className="flex items-start justify-between gap-3 py-2.5 border-b border-slate-800/40 last:border-0">
      <div>
        <p className="text-xs font-medium text-slate-300">{label}</p>
        {description && <p className="text-[11px] text-slate-500 mt-0.5">{description}</p>}
      </div>
      <button
        onClick={() => onChange(!value)}
        aria-pressed={value}
        className={[
          "relative shrink-0 inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200",
          value ? "bg-cyan-500" : "bg-slate-700",
        ].join(" ")}
      >
        <span
          className={[
            "inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform duration-200",
            value ? "translate-x-[18px]" : "translate-x-0.5",
          ].join(" ")}
        />
      </button>
    </div>
  )
}

function InputField({ label, value, onChange, type = "text", unit, min, step }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2.5 border-b border-slate-800/40 last:border-0">
      <span className="text-xs text-slate-400 shrink-0">{label}</span>
      <div className="flex items-center gap-1.5">
        <input
          type={type}
          value={value}
          min={min}
          step={step}
          onChange={e => onChange(type === "number" ? Number(e.target.value) : e.target.value)}
          className="w-40 rounded-lg bg-slate-950/60 border border-slate-700/60 text-xs font-mono text-slate-200 px-2.5 py-1.5 focus:outline-none focus:border-cyan-500/50 transition-all"
        />
        {unit && <span className="text-[11px] text-slate-500">{unit}</span>}
      </div>
    </div>
  )
}

function SelectField({ label, value, options, onChange }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2.5 border-b border-slate-800/40 last:border-0">
      <span className="text-xs text-slate-400 shrink-0">{label}</span>
      <select
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="rounded-lg bg-slate-950/60 border border-slate-700/60 text-xs font-mono text-slate-200 px-2.5 py-1.5 focus:outline-none focus:border-cyan-500/50 transition-all"
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}

function useToast() {
  const [toasts, setToasts] = useState({})
  const show = useCallback((key) => {
    setToasts(t => ({ ...t, [key]: true }))
    setTimeout(() => setToasts(t => ({ ...t, [key]: false })), 2000)
  }, [])
  return { toasts, show }
}

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
}

const stagger = { show: { transition: { staggerChildren: 0.06 } } }

export default function Settings() {
  const [settings, setSettings] = useState(loadSettings)
  const { toasts, show } = useToast()

  const set = useCallback((key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }, [])

  const persist = useCallback((keys, toastKey) => {
    setSettings(prev => {
      const partial = {}
      keys.forEach(k => { partial[k] = prev[k] })
      try {
        const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}")
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...existing, ...partial }))
      } catch (_) {}
      return prev
    })
    show(toastKey)
  }, [show])

  const resetAll = useCallback(() => {
    setSettings({ ...DEFAULTS })
    localStorage.removeItem(STORAGE_KEY)
    show("all")
  }, [show])

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-6 pb-8">

      {/* Header */}
      <motion.div variants={fadeUp} className="border-b border-slate-800/80 pb-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-300">
            <SettingsIcon className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">System Settings</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Configure detection thresholds, audio processing, and display preferences
            </p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

        {/* 1. System Configuration */}
        <motion.div variants={fadeUp}>
          <GlassPanel title="System Configuration" subtitle="API & connection settings" icon={CpuIcon}>
            <div>
              <InputField label="API Base URL" value={settings.apiBaseUrl} onChange={v => set("apiBaseUrl", v)} />
              <InputField label="Analysis Timeout" value={settings.analysisTimeout} onChange={v => set("analysisTimeout", v)} type="number" unit="seconds" min={5} step={5} />
              <InputField label="Max File Size" value={settings.maxFileSize} onChange={v => set("maxFileSize", v)} type="number" unit="MB" min={1} step={1} />
            </div>
            <SaveBar onSave={() => persist(["apiBaseUrl", "analysisTimeout", "maxFileSize"], "system")} saved={toasts.system} />
          </GlassPanel>
        </motion.div>

        {/* 2. Detection Thresholds */}
        <motion.div variants={fadeUp}>
          <GlassPanel title="Detection Thresholds" subtitle="EER-tuned sensitivity controls" icon={ShieldCheckIcon}>
            <div className="space-y-4">
              <SliderField label="Synthetic Detection Threshold" value={settings.syntheticThreshold} onChange={v => set("syntheticThreshold", v)} />
              <SliderField label="Human Confirmation Threshold" value={settings.humanThreshold} onChange={v => set("humanThreshold", v)} />
              <SliderField label="Confidence Minimum" value={settings.confidenceMinimum} onChange={v => set("confidenceMinimum", v)} />
            </div>
            <div className="flex items-center justify-between gap-3 pt-3 border-t border-slate-800/60 mt-3">
              <button
                onClick={() => { set("syntheticThreshold", DEFAULTS.syntheticThreshold); set("humanThreshold", DEFAULTS.humanThreshold); set("confidenceMinimum", DEFAULTS.confidenceMinimum) }}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800/60 border border-slate-700/60 text-slate-400 hover:text-slate-200 transition-all"
              >
                Reset to Defaults
              </button>
              <div className="flex items-center gap-3">
                {toasts.thresholds && <span className="flex items-center gap-1.5 text-xs text-emerald-400"><CheckCircleIcon className="h-3.5 w-3.5" />Saved</span>}
                <button onClick={() => persist(["syntheticThreshold", "humanThreshold", "confidenceMinimum"], "thresholds")} className="px-4 py-1.5 text-xs font-semibold uppercase tracking-wider rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/25 transition-all">
                  Save Thresholds
                </button>
              </div>
            </div>
          </GlassPanel>
        </motion.div>

        {/* 3. Audio Processing */}
        <motion.div variants={fadeUp}>
          <GlassPanel title="Audio Processing" subtitle="Sample rate, chunking & pre-processing" icon={WaveformIcon}>
            <div>
              <SelectField
                label="Sample Rate"
                value={settings.sampleRate}
                options={[
                  { value: 8000, label: "8,000 Hz" },
                  { value: 16000, label: "16,000 Hz (default)" },
                  { value: 22050, label: "22,050 Hz" },
                  { value: 44100, label: "44,100 Hz" },
                ]}
                onChange={v => set("sampleRate", v)}
              />
              <InputField label="Chunk Duration" value={settings.chunkDuration} onChange={v => set("chunkDuration", v)} type="number" unit="seconds" min={1} step={0.5} />
              <InputField label="Overlap Duration" value={settings.overlapDuration} onChange={v => set("overlapDuration", v)} type="number" unit="seconds" min={0} step={0.1} />
            </div>
            <div className="mt-3 border-t border-slate-800/60 pt-3">
              <ToggleField label="Enable Pre-Processing" description="Apply bandpass filter and normalization before inference" value={settings.enablePreProcessing} onChange={v => set("enablePreProcessing", v)} />
            </div>
            <div className="mt-3 pt-1">
              <SliderField label="Noise Reduction Level" value={settings.noiseReduction} onChange={v => set("noiseReduction", v)} />
            </div>
            <SaveBar onSave={() => persist(["sampleRate", "chunkDuration", "overlapDuration", "enablePreProcessing", "noiseReduction"], "audio")} saved={toasts.audio} />
          </GlassPanel>
        </motion.div>

        {/* 4. Notifications & Alerts */}
        <motion.div variants={fadeUp}>
          <GlassPanel title="Notifications & Alerts" subtitle="In-app alert configuration" icon={BellIcon}>
            <div>
              <ToggleField label="High Risk Alert" description="Alert when risk level is CRITICAL or HIGH" value={settings.highRiskAlert} onChange={v => set("highRiskAlert", v)} />
              <ToggleField label="Synthetic Detection Alert" description="Alert when a SYNTHETIC verdict is returned" value={settings.syntheticAlert} onChange={v => set("syntheticAlert", v)} />
              <ToggleField label="Analysis Complete Alert" description="Notify when background analysis finishes" value={settings.analysisCompleteAlert} onChange={v => set("analysisCompleteAlert", v)} />
              <ToggleField label="Alert Sound" description="Play audio tone on high-severity events" value={settings.alertSound} onChange={v => set("alertSound", v)} />
            </div>
            <SaveBar onSave={() => persist(["highRiskAlert", "syntheticAlert", "analysisCompleteAlert", "alertSound"], "notif")} saved={toasts.notif} />
          </GlassPanel>
        </motion.div>

        {/* 5. Display Preferences */}
        <motion.div variants={fadeUp}>
          <GlassPanel title="Display Preferences" subtitle="UI component visibility & motion" icon={ActivityIcon}>
            <div>
              <ToggleField label="Show 3D Neural Core" description="Render the Three.js voice visualisation sphere" value={settings.show3DCore} onChange={v => set("show3DCore", v)} />
              <ToggleField label="Reduce Motion" description="Disable Framer Motion transitions and pulsing effects" value={settings.reduceMotion} onChange={v => set("reduceMotion", v)} />
              <ToggleField label="Show Confidence Percentages" description="Display numeric confidence values alongside meters" value={settings.showConfidencePercentages} onChange={v => set("showConfidencePercentages", v)} />
              <ToggleField label="Show Chunk Timeline" description="Display per-chunk analysis table in Live Analysis" value={settings.showChunkTimeline} onChange={v => set("showChunkTimeline", v)} />
            </div>
            <SaveBar onSave={() => persist(["show3DCore", "reduceMotion", "showConfidencePercentages", "showChunkTimeline"], "display")} saved={toasts.display} />
          </GlassPanel>
        </motion.div>

        {/* 6. About / System Info */}
        <motion.div variants={fadeUp}>
          <GlassPanel title="About / System Info" subtitle="Build and dependency information" icon={InfoIcon}>
            <div className="space-y-0">
              {[
                ["Project", "AetherVoice"],
                ["SIH Problem Statement", "SIH26104"],
                ["Version", "1.0.0-alpha"],
                ["Frontend", "React 19 + Vite 6"],
                ["3D Engine", "Three.js + React Three Fiber"],
                ["Animation", "Framer Motion 13"],
                ["Charts", "Recharts 3"],
                ["ML Backend", "FastAPI (not connected)"],
                ["CSS Framework", "Tailwind CSS v4"],
                ["HTTP Client", "Axios"],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between text-xs font-mono py-1.5 border-b border-slate-800/40 last:border-0">
                  <span className="text-slate-500">{label}</span>
                  <span className="text-slate-300">{value}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-lg bg-slate-950/50 border border-slate-800/80 px-3 py-2.5 text-[11px] font-mono text-slate-500">
              <span className="text-slate-600">BUILD //</span>{" "}
              <span className="text-cyan-500/70">AetherVoice-Frontend</span>{" "}
              <span className="text-slate-600">@ SIH2026</span>
            </div>
          </GlassPanel>
        </motion.div>

      </div>

      {/* Reset All */}
      <motion.div variants={fadeUp}>
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 backdrop-blur-xl p-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-rose-300">Reset All Settings</h3>
              <p className="text-xs text-slate-500 mt-0.5">Restore all configuration to factory defaults and clear localStorage.</p>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              {toasts.all && <span className="flex items-center gap-1.5 text-xs text-emerald-400"><CheckCircleIcon className="h-3.5 w-3.5" />Reset</span>}
              <button onClick={resetAll} className="flex items-center gap-2 px-4 py-2 text-xs font-semibold uppercase tracking-wider rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300 hover:bg-rose-500/25 transition-all">
                <RefreshCwIcon className="h-3.5 w-3.5" />
                Reset All
              </button>
            </div>
          </div>
        </div>
      </motion.div>

    </motion.div>
  )
}
