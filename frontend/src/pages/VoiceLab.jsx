import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  WaveformIcon,
  RadioIcon,
  CpuIcon,
  PlayIcon,
  PauseIcon,
  ShieldCheckIcon,
} from '../components/common/Icons'
import StatusPill from '../components/common/StatusPill'
import GlassPanel from '../components/common/GlassPanel'
import NeuralCore from '../components/3d/NeuralCore'

// Audio Components
import AudioUploader from '../components/audio/AudioUploader'
import AudioRecorder from '../components/audio/AudioRecorder'
import Waveform from '../components/audio/Waveform'
import AudioMetadataCard from '../components/audio/AudioMetadataCard'

// Analysis Components
import ForensicPipeline from '../components/analysis/ForensicPipeline'

export default function VoiceLab() {
  // Ingestion Mode: 'upload' | 'record'
  const [ingestMode, setIngestMode] = useState('upload')

  // Audio File & Stream states
  const [audioFile, setAudioFile] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const [rawMetadata, setRawMetadata] = useState(null) // { duration, sampleRate, channels }

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const audioPlayerRef = useRef(null)

  // Forensic Pipeline Execution Simulation
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [activeStage, setActiveStage] = useState(0)
  const [stageProgress, setStageProgress] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const pipelineTimerRef = useRef(null)

  // Clean up audio URL and timers
  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl)
      if (pipelineTimerRef.current) clearInterval(pipelineTimerRef.current)
    }
  }, [audioUrl])

  // Audio Player Event Listeners
  const handleTimeUpdate = () => {
    if (audioPlayerRef.current) {
      setCurrentTime(audioPlayerRef.current.currentTime)
    }
  }

  const handleAudioEnded = () => {
    setIsPlaying(false)
    setCurrentTime(0)
  }

  const togglePlayPause = () => {
    if (!audioPlayerRef.current || !audioUrl) return

    if (isPlaying) {
      audioPlayerRef.current.pause()
      setIsPlaying(false)
    } else {
      audioPlayerRef.current.play()
      setIsPlaying(true)
    }
  }

  const handleSeek = (newTime) => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.currentTime = newTime
      setCurrentTime(newTime)
    }
  }

  // Audio File Handlers
  const handleFileSelected = (file, url, initialMeta = {}) => {
    setAudioFile(file)
    setAudioUrl(url)
    setRawMetadata(initialMeta.duration ? initialMeta : null)
    setIsComplete(false)
    setIsAnalyzing(false)
    setActiveStage(0)
    setStageProgress(0)
  }

  const handleClearAudio = () => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause()
    }
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
    }
    setAudioFile(null)
    setAudioUrl(null)
    setRawMetadata(null)
    setIsPlaying(false)
    setCurrentTime(0)
    setIsComplete(false)
    setIsAnalyzing(false)
    setActiveStage(0)
    setStageProgress(0)
  }

  // Live Recorder Handler
  const handleRecordingComplete = (blob, url, durationSeconds) => {
    // Convert blob to File object for unified handling
    const recordedFile = new File([blob], `recorded_sample_${Date.now()}.webm`, {
      type: blob.type || 'audio/webm',
    })
    setAudioFile(recordedFile)
    setAudioUrl(url)
    setRawMetadata({ duration: durationSeconds })
    setIngestMode('upload') // Switch back to preview view
    setIsComplete(false)
    setIsAnalyzing(false)
    setActiveStage(0)
    setStageProgress(0)
  }

  // Web Audio Decoded Metadata callback from Waveform
  const handleAudioDecoded = (decodedData) => {
    setRawMetadata((prev) => ({
      ...prev,
      duration: decodedData.duration,
      sampleRate: decodedData.sampleRate,
      channels: decodedData.channels,
    }))
  }

  // Pipeline Demonstration Simulation (Strictly labeled as DEMO)
  const startPipelineAnalysis = () => {
    if (!audioFile || isAnalyzing) return

    setIsAnalyzing(true)
    setIsComplete(false)
    setActiveStage(0)
    setStageProgress(0)

    let currentStage = 0
    let progressVal = 0

    pipelineTimerRef.current = setInterval(() => {
      progressVal += 12
      if (progressVal >= 100) {
        progressVal = 0
        currentStage += 1
        if (currentStage >= 5) {
          clearInterval(pipelineTimerRef.current)
          setIsAnalyzing(false)
          setIsComplete(true)
          setActiveStage(5)
          setStageProgress(100)
          return
        }
        setActiveStage(currentStage)
      }
      setStageProgress(progressVal)
    }, 180)
  }

  const resetPipeline = () => {
    if (pipelineTimerRef.current) clearInterval(pipelineTimerRef.current)
    setIsAnalyzing(false)
    setIsComplete(false)
    setActiveStage(0)
    setStageProgress(0)
  }

  // 3D Voice Core State
  const coreState = isAnalyzing || isPlaying ? 'analyzing' : 'idle'

  return (
    <div className="space-y-6 pb-6 select-none">
      {/* Hidden audio element for playback sync */}
      {audioUrl && (
        <audio
          ref={audioPlayerRef}
          src={audioUrl}
          onTimeUpdate={handleTimeUpdate}
          onEnded={handleAudioEnded}
          className="hidden"
        />
      )}

      {/* 1. HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 text-slate-400 hover:border-cyan-500/40 hover:text-cyan-300 transition-all"
            title="Return to Command Center"
          >
            <ArrowLeftIcon className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
                Voice Lab
              </h1>
              <StatusPill status="online" label="SOC NODE READY" size="sm" />
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              FORENSIC AUDIO ANALYSIS WORKSPACE // SIH26104
            </p>
          </div>
        </div>

        {/* System Status Indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg bg-slate-900/60 border border-slate-800/80 px-3 py-1.5 text-xs font-mono text-slate-300">
            <span className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
            <span className="text-slate-400">DSP ENGINE:</span>
            <span className="text-blue-300 font-bold">READY</span>
          </div>
        </div>
      </div>

      {/* 2. MAIN WORKSPACE: 3-PANEL LAYOUT */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-stretch">
        
        {/* LEFT PANEL — AUDIO INGESTION (Col Span 4) */}
        <div className="xl:col-span-4 flex flex-col space-y-4">
          <GlassPanel
            title="Audio Ingestion"
            subtitle="Drag & Drop or Record Live Sample"
            icon={RadioIcon}
            action={
              <div className="flex items-center rounded-lg bg-slate-950/80 p-0.5 border border-slate-800">
                <button
                  type="button"
                  onClick={() => setIngestMode('upload')}
                  className={`px-2.5 py-1 text-[11px] font-mono rounded transition-colors ${
                    ingestMode === 'upload'
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Upload
                </button>
                <button
                  type="button"
                  onClick={() => setIngestMode('record')}
                  className={`px-2.5 py-1 text-[11px] font-mono rounded transition-colors ${
                    ingestMode === 'record'
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Live Mic
                </button>
              </div>
            }
          >
            {ingestMode === 'upload' ? (
              <AudioUploader
                allowedExtensions={['.wav', '.mp3', '.m4a', '.ogg']}
                maxSizeMB={50}
                large={true}
                onFileSelected={handleFileSelected}
                onClear={handleClearAudio}
                onRecordLiveClick={() => setIngestMode('record')}
              />
            ) : (
              <div className="space-y-3">
                <AudioRecorder
                  onRecordingComplete={handleRecordingComplete}
                  onClear={() => setIngestMode('upload')}
                />
                <button
                  type="button"
                  onClick={() => setIngestMode('upload')}
                  className="w-full text-center text-[11px] font-mono text-slate-400 hover:text-cyan-300 transition-colors pt-1"
                >
                  ← Return to File Uploader
                </button>
              </div>
            )}
          </GlassPanel>

          {/* Quick Guidance Box */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/30 p-3.5 text-xs font-mono text-slate-400 space-y-1.5">
            <div className="flex items-center gap-1.5 text-cyan-400 font-semibold text-[11px]">
              <ShieldCheckIcon className="h-3.5 w-3.5" />
              <span>FORENSIC PROTOCOL</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-400 font-sans">
              Upload a browser-decodable audio file. AetherVoice decodes it to PCM and analyzes overlapping 2-second windows with a 1-second hop through the same backend used by live microphone analysis.
            </p>
          </div>
        </div>

        {/* CENTER PANEL — AUDIO FORENSICS (Col Span 4) */}
        <div className="xl:col-span-4 flex flex-col space-y-4">
          <GlassPanel
            title="Audio Forensics"
            subtitle="Envelope Extraction & Waveform Inspection"
            icon={WaveformIcon}
            className="space-y-4"
          >
            {/* Real Web Audio Decoded Waveform */}
            <Waveform
              audioFile={audioFile}
              audioUrl={audioUrl}
              currentTime={currentTime}
              duration={rawMetadata?.duration || 0}
              onSeek={handleSeek}
              onAudioDecoded={handleAudioDecoded}
            />

            {/* Playback Controls & Scrubber */}
            <div className="rounded-xl border border-slate-800/90 bg-slate-950/80 p-3.5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    disabled={!audioUrl}
                    onClick={togglePlayPause}
                    className={`flex h-9 w-9 items-center justify-center rounded-lg border font-bold transition-all ${
                      !audioUrl
                        ? 'bg-slate-900 border-slate-800 text-slate-600 cursor-not-allowed'
                        : isPlaying
                        ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.2)]'
                        : 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/30 shadow-[0_0_12px_rgba(6,182,212,0.2)]'
                    }`}
                  >
                    {isPlaying ? (
                      <PauseIcon className="h-4 w-4" />
                    ) : (
                      <PlayIcon className="h-4 w-4" />
                    )}
                  </button>

                  <div>
                    <div className="text-xs font-mono font-semibold text-slate-200">
                      {isPlaying ? 'PLAYING AUDIO' : audioUrl ? 'PLAYBACK READY' : 'NO AUDIO LOADED'}
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">
                      CLICK WAVEFORM TO SEEK
                    </span>
                  </div>
                </div>

                <div className="text-right font-mono text-xs">
                  <span className="text-cyan-400 font-bold">
                    {(currentTime).toFixed(1)}s
                  </span>
                  <span className="text-slate-500"> / </span>
                  <span className="text-slate-400">
                    {(rawMetadata?.duration || 0).toFixed(1)}s
                  </span>
                </div>
              </div>
            </div>
          </GlassPanel>

          {/* Compact 3D Voice Core Resonance Status (Tactical viewport) */}
          <GlassPanel
            title="Lattice Resonance"
            subtitle="3D Acoustic Core Monitor"
            icon={CpuIcon}
            className="flex-1 flex flex-col justify-between overflow-hidden min-h-[220px]"
          >
            <div className="relative h-44 w-full rounded-lg bg-slate-950/70 border border-slate-800/70 overflow-hidden flex items-center justify-center">
              <NeuralCore state={coreState} />
            </div>
            <div className="mt-2 text-right text-[10px] font-mono text-slate-500">
              STATE: [{coreState.toUpperCase()}] // 3D RENDER ACTIVE
            </div>
          </GlassPanel>
        </div>

        {/* RIGHT PANEL — ANALYSIS PIPELINE (Col Span 4) */}
        <div className="xl:col-span-4 flex flex-col space-y-4">
          <ForensicPipeline
            hasAudio={Boolean(audioFile)}
            isAnalyzing={isAnalyzing}
            activeStage={activeStage}
            progress={stageProgress}
            isComplete={isComplete}
            onAnalyzeClick={startPipelineAnalysis}
            onResetClick={resetPipeline}
          />
        </div>
      </div>

      {/* 3. BOTTOM SECTION — AUDIO INFORMATION */}
      <div className="pt-2">
        <AudioMetadataCard
          file={audioFile}
          metadata={rawMetadata}
        />
      </div>
    </div>
  )
}
