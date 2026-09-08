import React, { useRef, useEffect, useState, useMemo } from 'react'
import { ActivityIcon, RadioIcon, Volume2Icon, AlertTriangleIcon, ClockIcon } from '../common/Icons'

export default function Waveform({
  stream = null,
  audioUrl = null,
  audioFile = null,
  isRecording = false,
  currentTime = 0,
  duration = 0,
  onSeek = null,
  onAudioDecoded = null,
  className = '',
}) {
  const [liveAudioLevels, setLiveAudioLevels] = useState(() => Array(48).fill(8))
  const [liveVuLevel, setLiveVuLevel] = useState(-48)
  const [decodedData, setDecodedData] = useState({ file: null, peaks: null, error: null })

  const animationFrameRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const sourceRef = useRef(null)

  // Real-time microphone audio visualizer via Web Audio API AnalyserNode
  useEffect(() => {
    if (isRecording && stream) {
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext
        if (!AudioCtx) return

        const audioCtx = new AudioCtx()
        audioContextRef.current = audioCtx
        const analyser = audioCtx.createAnalyser()
        analyser.fftSize = 128
        analyser.smoothingTimeConstant = 0.8
        analyserRef.current = analyser

        const source = audioCtx.createMediaStreamSource(stream)
        source.connect(analyser)
        sourceRef.current = source

        const bufferLength = analyser.frequencyBinCount
        const dataArray = new Uint8Array(bufferLength)

        const updateLiveMeter = () => {
          analyser.getByteFrequencyData(dataArray)

          // Sample 48 bars
          const barsCount = 48
          const newLevels = []
          let sum = 0

          for (let i = 0; i < barsCount; i++) {
            const index = Math.floor((i / barsCount) * (bufferLength / 1.5))
            const val = dataArray[index] || 0
            const height = Math.max(6, Math.min(96, (val / 255) * 96))
            newLevels.push(height)
            sum += val
          }

          const avg = sum / barsCount
          const db = Math.round(Math.max(-60, (avg / 255) * 60 - 60))
          setLiveVuLevel(db)
          setLiveAudioLevels(newLevels)

          animationFrameRef.current = requestAnimationFrame(updateLiveMeter)
        }

        updateLiveMeter()
      } catch (e) {
        console.error('AudioContext live visualizer error:', e)
      }
    } else {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close().catch(() => {})
      }
      audioContextRef.current = null
      analyserRef.current = null
      sourceRef.current = null
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close().catch(() => {})
      }
    }
  }, [isRecording, stream])

  // Decode real audio file asynchronously using Web Audio API AudioContext.decodeAudioData
  useEffect(() => {
    if (audioFile && !isRecording) {
      let isCancelled = false

      const AudioCtx = window.AudioContext || window.webkitAudioContext
      if (!AudioCtx) {
        return
      }

      const audioCtx = new AudioCtx()

      audioFile
        .arrayBuffer()
        .then((arrayBuffer) => {
          if (isCancelled) return null
          return audioCtx.decodeAudioData(arrayBuffer)
        })
        .then((audioBuffer) => {
          if (!audioBuffer || isCancelled) return

          // Extract real channel peaks from channel 0
          const rawData = audioBuffer.getChannelData(0)
          const barCount = 48
          const blockSize = Math.max(1, Math.floor(rawData.length / barCount))
          const extractedPeaks = []

          for (let i = 0; i < barCount; i++) {
            const start = i * blockSize
            let sum = 0
            for (let j = 0; j < blockSize; j++) {
              sum += Math.abs(rawData[start + j] || 0)
            }
            const avg = sum / blockSize
            const height = Math.max(8, Math.min(96, Math.round(avg * 250)))
            extractedPeaks.push(height)
          }

          setDecodedData({ file: audioFile, peaks: extractedPeaks, error: null })

          if (onAudioDecoded) {
            onAudioDecoded({
              duration: audioBuffer.duration,
              sampleRate: audioBuffer.sampleRate,
              channels: audioBuffer.numberOfChannels,
            })
          }

          audioCtx.close().catch(() => {})
        })
        .catch((err) => {
          if (isCancelled) return
          console.warn('Audio decoding failed:', err)
          setDecodedData({
            file: audioFile,
            peaks: null,
            error: 'Could not decode audio data. Format may be compressed or corrupted.',
          })
          audioCtx.close().catch(() => {})
        })

      return () => {
        isCancelled = true
        if (audioCtx.state !== 'closed') {
          audioCtx.close().catch(() => {})
        }
      }
    }
  }, [audioFile, isRecording, onAudioDecoded])

  // Derived state
  const isDecoding = Boolean(audioFile && decodedData.file !== audioFile && !isRecording)
  const decodedPeaks = decodedData.file === audioFile ? decodedData.peaks : null
  const decodeError = decodedData.file === audioFile ? decodedData.error : null

  // Fallback synthetic envelope if no real decoded peaks
  const staticEnvelope = useMemo(() => {
    const barsCount = 48
    if (audioUrl) {
      const envelope = []
      for (let i = 0; i < barsCount; i++) {
        const harmonic =
          Math.sin(i * 0.2) * 20 +
          Math.cos(i * 0.45) * 15 +
          Math.sin(i * 0.1) * 25 +
          35
        envelope.push(Math.max(10, Math.min(88, harmonic)))
      }
      return envelope
    }
    return Array(barsCount)
      .fill(0)
      .map((_, i) => 8 + Math.sin(i * 0.4) * 4)
  }, [audioUrl])

  // Active bar heights
  const audioLevels = isRecording
    ? liveAudioLevels
    : decodedPeaks || staticEnvelope

  const vuLevel = isRecording ? liveVuLevel : (audioUrl || audioFile) ? -18 : -60

  // Playback progress calculation (0 to 100%)
  const progressPercent = duration > 0 ? Math.min(100, (currentTime / duration) * 100) : 0

  const handleWaveformClick = (e) => {
    if (!onSeek || !duration) return
    const rect = e.currentTarget.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const newPercent = Math.max(0, Math.min(1, clickX / rect.width))
    onSeek(newPercent * duration)
  }

  const formatTime = (sec) => {
    if (!sec || isNaN(sec)) return '00:00.0'
    const mins = Math.floor(sec / 60)
    const s = (sec % 60).toFixed(1)
    return `${mins.toString().padStart(2, '0')}:${s.padStart(4, '0')}`
  }

  return (
    <div
      className={`rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-3 ${className}`}
    >
      {/* Header telemetry */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isRecording ? (
            <RadioIcon className="h-4 w-4 text-rose-400 animate-pulse" />
          ) : audioFile || audioUrl ? (
            <Volume2Icon className="h-4 w-4 text-cyan-400" />
          ) : (
            <ActivityIcon className="h-4 w-4 text-slate-400" />
          )}
          <span className="text-xs font-mono uppercase tracking-wider text-slate-200">
            {isRecording
              ? 'LIVE MICROPHONE SPECTRAL BANDS'
              : isDecoding
              ? 'DECODING AUDIO BUFFER...'
              : decodedPeaks
              ? 'ACOUSTIC ENVELOPE (WEB AUDIO DECODED)'
              : audioUrl
              ? 'AUDIO ENVELOPE PREVIEW'
              : 'ACOUSTIC MONITOR STANDBY'}
          </span>
        </div>

        <div className="flex items-center gap-3 text-[10px] font-mono">
          {duration > 0 && (
            <span className="flex items-center gap-1 text-slate-300">
              <ClockIcon className="h-3 w-3 text-cyan-400" />
              <span>{formatTime(currentTime)} / {formatTime(duration)}</span>
            </span>
          )}
          <span className="text-slate-400">VU:</span>
          <span
            className={`font-bold ${
              vuLevel > -12 ? 'text-rose-400' : vuLevel > -24 ? 'text-amber-400' : 'text-cyan-400'
            }`}
          >
            {vuLevel > -60 ? `${vuLevel} dB` : '-INF'}
          </span>
        </div>
      </div>

      {/* Decoding Error Alert */}
      {decodeError && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/40 bg-amber-950/30 p-2.5 text-xs text-amber-300">
          <AlertTriangleIcon className="h-4 w-4 shrink-0 text-amber-400" />
          <span className="text-[11px] font-mono">{decodeError}</span>
        </div>
      )}

      {/* Waveform Bar Container with interactive scrubbing */}
      <div
        onClick={handleWaveformClick}
        className={`relative h-28 w-full rounded-lg bg-slate-950/90 border border-slate-800/70 p-2 flex items-center justify-center overflow-hidden ${
          onSeek && duration > 0 ? 'cursor-pointer' : ''
        }`}
      >
        {/* Subtle grid lines */}
        <div className="pointer-events-none absolute inset-0 flex flex-col justify-between p-2 opacity-15">
          <div className="w-full border-b border-dashed border-cyan-400" />
          <div className="w-full border-b border-cyan-400" />
          <div className="w-full border-b border-dashed border-cyan-400" />
        </div>

        {/* Dynamic Bars */}
        <div className="relative z-10 flex h-full w-full items-center justify-between gap-[3px] px-1">
          {audioLevels.map((height, idx) => {
            const barProgress = (idx / audioLevels.length) * 100
            const isPlayed = duration > 0 && barProgress <= progressPercent

            let barColor = 'bg-slate-800'
            if (isRecording) {
              barColor = 'bg-gradient-to-t from-rose-600 via-amber-400 to-cyan-300'
            } else if (audioFile || audioUrl) {
              if (isPlayed) {
                barColor = 'bg-gradient-to-t from-cyan-400 to-white shadow-[0_0_8px_rgba(6,182,212,0.6)]'
              } else {
                barColor = 'bg-gradient-to-t from-cyan-900 to-cyan-600 opacity-70'
              }
            }

            return (
              <div
                key={idx}
                className="flex-1 flex flex-col items-center justify-center h-full"
              >
                <div
                  style={{ height: `${height}%` }}
                  className={`w-full rounded-full transition-all duration-75 ${barColor}`}
                />
              </div>
            )
          })}
        </div>

        {/* Playback Playhead Scrubber */}
        {duration > 0 && !isRecording && (
          <div
            style={{ left: `${progressPercent}%` }}
            className="pointer-events-none absolute inset-y-0 w-0.5 bg-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.9)] z-20 transition-all duration-75"
          >
            <div className="h-2 w-2 rounded-full bg-cyan-400 -ml-[3px] -mt-1 shadow-[0_0_8px_rgba(6,182,212,1)]" />
          </div>
        )}

        {/* Scanning laser line in recording mode */}
        {isRecording && (
          <div className="pointer-events-none absolute inset-y-0 w-1 bg-rose-400/80 blur-[1px] animate-pulse left-1/2 -translate-x-1/2" />
        )}
      </div>

      {/* Footer Diagnostic strip */}
      <div className="flex flex-wrap items-center justify-between text-[10px] font-mono text-slate-400 pt-1 border-t border-slate-800/50">
        <div>
          <span>REPRESENTATION: </span>
          <span className="text-slate-300">
            {decodedPeaks ? 'Actual Peak Amplitudes' : 'Signal Envelope'}
          </span>
        </div>
        <div className="text-slate-400">
          [NOT PREDICTIVE AI EVIDENCE]
        </div>
        <div className="text-cyan-400/80">
          {isDecoding
            ? 'DECODING...'
            : audioFile || audioUrl
            ? 'DSP READY'
            : isRecording
            ? 'INGESTING'
            : 'AWAITING INPUT'}
        </div>
      </div>
    </div>
  )
}
