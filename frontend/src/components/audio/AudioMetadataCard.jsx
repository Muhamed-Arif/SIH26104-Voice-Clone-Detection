import React from 'react'
import { FileTextIcon, ClockIcon, RadioIcon, ActivityIcon, CpuIcon } from '../common/Icons'

export default function AudioMetadataCard({
  file = null,
  metadata = null, // { duration, sampleRate, channels }
  className = '',
}) {
  const formatFileSize = (bytes) => {
    if (!bytes && bytes !== 0) return '---'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  const formatDuration = (sec) => {
    if (!sec && sec !== 0) return '---'
    const mins = Math.floor(sec / 60)
    const remainingSec = (sec % 60).toFixed(2)
    return `${mins.toString().padStart(2, '0')}:${remainingSec.padStart(5, '0')}s`
  }

  const formatChannels = (ch) => {
    if (!ch) return '---'
    if (ch === 1) return '1 (Mono)'
    if (ch === 2) return '2 (Stereo)'
    return `${ch} Channels`
  }

  const formatSampleRate = (sr) => {
    if (!sr) return '---'
    return `${sr.toLocaleString()} Hz`
  }

  const fileType = file?.type || (file?.name ? file.name.split('.').pop()?.toUpperCase() : '---')

  return (
    <div className={`rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-3 font-mono ${className}`}>
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <FileTextIcon className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Acoustic Signal Telemetry & Metadata
          </span>
        </div>
        <span className="text-[10px] text-slate-400">
          [EXTRACTED FROM INGESTED AUDIO HEADER]
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-2.5 space-y-1">
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <RadioIcon className="h-3 w-3 text-cyan-400" />
            <span>FILE FORMAT</span>
          </span>
          <span className="text-xs font-bold text-slate-200 block truncate">
            {file ? fileType : '---'}
          </span>
        </div>

        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-2.5 space-y-1">
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <ActivityIcon className="h-3 w-3 text-cyan-400" />
            <span>SAMPLE RATE</span>
          </span>
          <span className="text-xs font-bold text-cyan-400 block truncate">
            {formatSampleRate(metadata?.sampleRate)}
          </span>
        </div>

        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-2.5 space-y-1">
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <CpuIcon className="h-3 w-3 text-cyan-400" />
            <span>CHANNELS</span>
          </span>
          <span className="text-xs font-bold text-slate-200 block truncate">
            {formatChannels(metadata?.channels)}
          </span>
        </div>

        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-2.5 space-y-1">
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <ClockIcon className="h-3 w-3 text-cyan-400" />
            <span>DURATION</span>
          </span>
          <span className="text-xs font-bold text-slate-200 block truncate">
            {formatDuration(metadata?.duration)}
          </span>
        </div>

        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-2.5 space-y-1 col-span-2 sm:col-span-1">
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <FileTextIcon className="h-3 w-3 text-cyan-400" />
            <span>FILE SIZE</span>
          </span>
          <span className="text-xs font-bold text-slate-200 block truncate">
            {formatFileSize(file?.size)}
          </span>
        </div>
      </div>
    </div>
  )
}
