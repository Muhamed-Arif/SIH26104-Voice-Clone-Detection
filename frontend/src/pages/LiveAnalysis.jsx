import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { analyzeAudioFile, analyzeWaveform, getRmsDb } from '../services/api'
import {
  ArrowLeftIcon,
  RadioIcon,
  MicIcon,
  UploadIcon,
  CpuIcon,
} from '../components/common/Icons'
import StatusPill from '../components/common/StatusPill'
import GlassPanel from '../components/common/GlassPanel'
import NeuralCore from '../components/3d/NeuralCore'

import AudioRecorder from '../components/audio/AudioRecorder'
import AudioUploader from '../components/audio/AudioUploader'
import Waveform from '../components/audio/Waveform'

import AnalysisPanel from '../components/analysis/AnalysisPanel'
import ConfidenceMeter from '../components/analysis/ConfidenceMeter'
import ChunkTimeline from '../components/analysis/ChunkTimeline'
import ModelStatus from '../components/analysis/ModelStatus'

import RiskGauge from '../components/risk/RiskGauge'
import RiskBadge from '../components/risk/RiskBadge'
import ReasonCodes from '../components/risk/ReasonCodes'
import PreventionStatus from '../components/risk/PreventionStatus'

const WINDOW_SECONDS = 2
const HOP_SECONDS = 1
const SILENCE_DB = -45

function clamp01(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return 0
  return Math.max(0, Math.min(1, n))
}

function mapBackendResult(data, latencyMs = null) {
  const syntheticProbability = clamp01(data.synthetic_probability)
  const confidenceValue = clamp01(
    data.confidence ?? Math.max(syntheticProbability, 1 - syntheticProbability)
  )
  const riskLevel = String(data.risk_level || 'LOW').toLowerCase()
  const action = String(data.action || 'ALLOW').toUpperCase()

  let verdict = 'human'
  if (action === 'BLOCK' || riskLevel === 'high' || riskLevel === 'critical') {
    verdict = 'synthetic'
  } else if (riskLevel === 'medium' || riskLevel === 'moderate') {
    verdict = 'unknown'
  }

  return {
    verdict,
    synthetic_probability: syntheticProbability,
    human_probability: 1 - syntheticProbability,
    confidence: `${(confidenceValue * 100).toFixed(1)}%`,
    confidence_value: confidenceValue,
    risk_level: riskLevel === 'medium' ? 'moderate' : riskLevel,
    risk_score: Number(data.risk_score || 0),
    audio_quality: String(data.audio_quality || 'UNKNOWN'),
    action,
    latency_ms: Number(latencyMs ?? data.latency_ms ?? 0),
    model_version: data.model_version || 'unknown',
    reason_codes: Array.isArray(data.reason_codes) ? data.reason_codes : [],
    risk_factors: Array.isArray(data.risk_factors) ? data.risk_factors : [],
    chunk_id: data.chunk_id,
    created_at: data.created_at || new Date().toISOString(),
    evidence: {
      syntheticProbability,
      confidence: confidenceValue,
      riskScore: Math.max(0, Math.min(1, Number(data.risk_score || 0) / 100)),
      reasonCodes: Array.isArray(data.reason_codes) ? data.reason_codes : [],
    },
  }
}

export default function LiveAnalysis() {
  const [inputMode, setInputMode] = useState('mic')
  const [isRecording, setIsRecording] = useState(false)
  const [audioStream, setAudioStream] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const [audioDuration, setAudioDuration] = useState(0)

  const [analysisStatus, setAnalysisStatus] = useState('WAITING')
  const [audioQuality, setAudioQuality] = useState('AWAITING INPUT')
  const [processingStage, setProcessingStage] = useState('INGESTION STANDBY')
  const [inferenceResult, setInferenceResult] = useState(null)
  const [chunks, setChunks] = useState([])
  const [modelStatus, setModelStatus] = useState('CHECKING BACKEND')

  const sessionIdRef = useRef(crypto.randomUUID())
  const liveAudioContextRef = useRef(null)
  const liveSourceRef = useRef(null)
  const liveProcessorRef = useRef(null)
  const liveBufferRef = useRef([])
  const liveSequenceRef = useRef(0)
  const liveSendingRef = useRef(false)

  const coreState = isRecording
    ? 'analyzing'
    : inferenceResult?.verdict === 'synthetic'
      ? 'synthetic'
      : inferenceResult?.verdict === 'human'
        ? 'human'
        : inferenceResult?.verdict === 'unknown'
          ? 'unknown'
          : 'idle'

  const applyResult = useCallback((rawData, clientLatency = null) => {
    const result = mapBackendResult(rawData, clientLatency)
    setInferenceResult(result)
    setAnalysisStatus('COMPLETE')
    setAudioQuality(result.audio_quality)
    setProcessingStage(
      result.action === 'BLOCK'
        ? 'THREAT DETECTED // SENSITIVE ACTION BLOCKED'
        : 'AUTHENTICITY CHECK COMPLETE // ACTION ALLOWED'
    )
    setModelStatus(`ONLINE // ${result.model_version}`)

    setChunks((previous) => {
      const next = [
        ...previous,
        {
          id: result.chunk_id || previous.length + 1,
          timestamp: new Date(result.created_at).toLocaleTimeString(),
          verdict: result.verdict,
          confidence: result.confidence,
          risk: result.risk_score,
        },
      ]
      return next.slice(-24)
    })

    return result
  }, [])

  const stopLiveProcessor = useCallback(async () => {
    const processor = liveProcessorRef.current
    const source = liveSourceRef.current
    const context = liveAudioContextRef.current

    if (processor) {
      processor.onaudioprocess = null
      try { processor.disconnect() } catch (_) {}
    }
    if (source) {
      try { source.disconnect() } catch (_) {}
    }
    if (context && context.state !== 'closed') {
      try { await context.close() } catch (_) {}
    }

    liveProcessorRef.current = null
    liveSourceRef.current = null
    liveAudioContextRef.current = null
    liveBufferRef.current = []
    liveSendingRef.current = false
  }, [])

  const sendLiveWindow = useCallback(async (windowSamples, sampleRate) => {
    if (liveSendingRef.current) return

    const db = getRmsDb(windowSamples)
    if (db < SILENCE_DB) {
      setAudioQuality(`SILENCE SKIPPED (${db.toFixed(1)} dBFS)`)
      return
    }

    liveSendingRef.current = true
    liveSequenceRef.current += 1
    const chunkId = `web-${sessionIdRef.current}-${String(liveSequenceRef.current).padStart(6, '0')}`

    try {
      setAnalysisStatus('PROCESSING')
      setProcessingStage('LIVE CHUNK → M2 DSP → M1 ML → RISK ENGINE')
      const quality = db < -32 ? 'DEGRADED' : 'HIGH'
      const started = performance.now()
      const response = await analyzeWaveform({
        waveform: windowSamples,
        sampleRate,
        chunkId,
        sessionId: sessionIdRef.current,
        quality,
      })
      applyResult(response.data, performance.now() - started)
    } catch (error) {
      console.error('Live backend analysis failed:', error)
      setAnalysisStatus('WAITING FOR MODEL')
      setProcessingStage('BACKEND / MODEL CONNECTION FAILED')
      setModelStatus('OFFLINE / UNREACHABLE')
    } finally {
      liveSendingRef.current = false
    }
  }, [applyResult])

  const startLiveProcessor = useCallback((stream) => {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext
    if (!AudioContextClass) {
      setProcessingStage('WEB AUDIO API NOT SUPPORTED')
      return
    }

    const context = new AudioContextClass()
    const source = context.createMediaStreamSource(stream)
    const processor = context.createScriptProcessor(4096, 1, 1)

    liveAudioContextRef.current = context
    liveSourceRef.current = source
    liveProcessorRef.current = processor
    liveBufferRef.current = []
    liveSequenceRef.current = 0

    processor.onaudioprocess = (event) => {
      const input = event.inputBuffer.getChannelData(0)
      const buffer = liveBufferRef.current
      for (let i = 0; i < input.length; i += 1) buffer.push(input[i])

      const windowSize = Math.round(context.sampleRate * WINDOW_SECONDS)
      const hopSize = Math.round(context.sampleRate * HOP_SECONDS)

      if (buffer.length >= windowSize) {
        const block = Float32Array.from(buffer.slice(0, windowSize))
        liveBufferRef.current = buffer.slice(hopSize)
        sendLiveWindow(block, context.sampleRate)
      }
    }

    source.connect(processor)
    processor.connect(context.destination)
    setModelStatus('ONLINE // LIVE STREAM ACTIVE')
  }, [sendLiveWindow])

  useEffect(() => () => {
    stopLiveProcessor()
  }, [stopLiveProcessor])

  const handleRecordingStart = (stream) => {
    setIsRecording(true)
    setAudioStream(stream)
    setAnalysisStatus('RECORDING')
    setAudioQuality('LIVE PCM CAPTURE')
    setProcessingStage('LIVE HARDWARE CAPTURE // 2s WINDOW / 1s HOP')
    setInferenceResult(null)
    setChunks([])
    startLiveProcessor(stream)
  }

  const handleRecordingStop = () => {
    setIsRecording(false)
    setAudioStream(null)
    setAnalysisStatus(inferenceResult ? 'COMPLETE' : 'WAITING FOR MODEL')
    setProcessingStage(inferenceResult ? 'LIVE ANALYSIS STOPPED' : 'NO SPEECH RESULT YET')
    stopLiveProcessor()
  }

  const handleRecordingComplete = (blob, url, duration) => {
    setAudioUrl(url)
    setAudioDuration(duration)
    setIsRecording(false)
    if (inferenceResult) {
      setAnalysisStatus('COMPLETE')
    }
  }

  const handleRecordingClear = () => {
    stopLiveProcessor()
    setIsRecording(false)
    setAudioStream(null)
    setAudioUrl(null)
    setAudioDuration(0)
    setAnalysisStatus('WAITING')
    setAudioQuality('AWAITING INPUT')
    setProcessingStage('INGESTION STANDBY')
    setInferenceResult(null)
    setChunks([])
  }

  const handleFileSelected = async (file, url) => {
    setAudioUrl(url)
    setAudioDuration(0)
    setAnalysisStatus('PROCESSING')
    setAudioQuality('DECODING AUDIO')
    setProcessingStage('FILE → PCM → CHUNKED BACKEND INFERENCE')
    setInferenceResult(null)
    setChunks([])

    try {
      const result = await analyzeAudioFile(file, {
        sessionId: sessionIdRef.current,
        windowSeconds: WINDOW_SECONDS,
        hopSeconds: HOP_SECONDS,
        onChunk: (data) => applyResult(data, data.client_latency_ms),
      })
      setAudioDuration(Math.round(result.duration))
      applyResult(result.data, result.data.client_latency_ms)
      setAnalysisStatus('COMPLETE')
    } catch (error) {
      console.error('Uploaded audio analysis failed:', error)
      setAnalysisStatus('WAITING')
      setProcessingStage('BACKEND CONNECTION / AUDIO DECODE FAILED')
      setAudioQuality('ANALYSIS ERROR')
      setInferenceResult(null)
    }
  }

  const handleFileClear = () => {
    setAudioUrl(null)
    setAudioDuration(0)
    setAnalysisStatus('WAITING')
    setAudioQuality('AWAITING INPUT')
    setProcessingStage('INGESTION STANDBY')
    setInferenceResult(null)
    setChunks([])
  }

  return (
    <div className="space-y-6 pb-6 select-none">
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
                Live Voice Analysis
              </h1>
              <StatusPill status="online" label="READY" size="sm" />
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              REAL-TIME AUDIO INGESTION & ACOUSTIC IMPERSONATION INFERENCE // SIH26104
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 rounded-lg bg-slate-900/60 border border-slate-800/80 px-3 py-1.5 text-xs font-mono text-slate-300">
            <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-slate-400">SESSION:</span>
            <span className="text-cyan-300 font-bold">{sessionIdRef.current.slice(0, 8)}</span>
          </div>

          <RiskBadge risk_level={inferenceResult?.risk_level || null} size="md" />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-stretch">
        <div className="xl:col-span-4 flex flex-col space-y-4">
          <GlassPanel
            title="Audio Feed Ingestion"
            subtitle="Live Microphone & Audio File Analysis"
            icon={RadioIcon}
            action={
              <div className="flex items-center rounded-lg bg-slate-950/80 p-0.5 border border-slate-800">
                <button
                  type="button"
                  onClick={() => setInputMode('mic')}
                  className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-mono transition-colors ${
                    inputMode === 'mic'
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <MicIcon className="h-3 w-3" />
                  <span>Mic</span>
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode('upload')}
                  className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-mono transition-colors ${
                    inputMode === 'upload'
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <UploadIcon className="h-3 w-3" />
                  <span>Upload</span>
                </button>
              </div>
            }
          >
            {inputMode === 'mic' ? (
              <AudioRecorder
                onRecordingStart={handleRecordingStart}
                onRecordingStop={handleRecordingStop}
                onRecordingComplete={handleRecordingComplete}
                onClear={handleRecordingClear}
              />
            ) : (
              <AudioUploader onFileSelected={handleFileSelected} onClear={handleFileClear} />
            )}
          </GlassPanel>

          <Waveform stream={audioStream} audioUrl={audioUrl} isRecording={isRecording} />

          <ModelStatus
            modelVersion={inferenceResult?.model_version || null}
            latency={inferenceResult?.latency_ms || null}
          />
        </div>

        <div className="xl:col-span-4 flex flex-col">
          <GlassPanel
            title="Resonance Sphere"
            subtitle="Live Acoustic Authenticity State"
            icon={CpuIcon}
            glowing={coreState === 'analyzing' || coreState === 'synthetic'}
            highlightColor={coreState === 'synthetic' ? 'rose' : 'cyan'}
            action={
              <span className="text-[10px] font-mono text-cyan-400 uppercase">
                STATE: [{coreState.toUpperCase()}]
              </span>
            }
            className="flex-1 flex flex-col justify-between overflow-hidden min-h-[420px]"
          >
            <div className="relative flex-1 w-full rounded-lg bg-slate-950/70 border border-slate-800/70 overflow-hidden flex items-center justify-center">
              <NeuralCore state={coreState} />
            </div>

            <div className="mt-3 p-3 rounded-lg bg-slate-950/50 border border-slate-800/60 flex items-center justify-between text-[11px] font-mono">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="text-slate-400">PIPELINE:</span>
                <span className="text-cyan-300 font-bold">
                  {isRecording ? 'LIVE 2s WINDOWS / 1s HOP' : 'STANDBY'}
                </span>
              </div>
              <span className="text-slate-400">THREE-WebGL</span>
            </div>
          </GlassPanel>
        </div>

        <div className="xl:col-span-4 flex flex-col space-y-4">
          <AnalysisPanel
            status={analysisStatus}
            audioQuality={audioQuality}
            processingStage={processingStage}
            modelStatus={modelStatus}
            duration={audioDuration}
          />

          <ConfidenceMeter
            confidence={inferenceResult?.confidence || null}
            human_probability={inferenceResult?.human_probability ?? null}
            synthetic_probability={inferenceResult?.synthetic_probability ?? null}
          />

          <RiskGauge
            risk_level={inferenceResult?.risk_level || null}
            score={inferenceResult ? inferenceResult.risk_score / 10 : null}
          />

          <PreventionStatus
            verdict={inferenceResult?.verdict?.toUpperCase() || 'WAITING'}
            preventionStatus={inferenceResult?.action || 'STANDBY'}
            autoIntercept={true}
          />

          <ReasonCodes evidence={inferenceResult?.evidence || null} />
        </div>
      </div>

      <div className="pt-2">
        <ChunkTimeline chunks={chunks} windowSeconds={WINDOW_SECONDS} hopSeconds={HOP_SECONDS} />
      </div>
    </div>
  )
}
