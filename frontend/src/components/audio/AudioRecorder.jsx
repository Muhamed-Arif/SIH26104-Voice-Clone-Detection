import React, { useState, useRef, useEffect } from 'react'
import {
  MicIcon,
  StopIcon,
  TrashIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  Volume2Icon,
  RadioIcon,
} from '../common/Icons'

export default function AudioRecorder({
  onRecordingStart,
  onRecordingStop,
  onRecordingComplete,
  onClear,
}) {
  const [status, setStatus] = useState('idle') // 'idle' | 'recording' | 'stopped'
  const [seconds, setSeconds] = useState(0)
  const [audioUrl, setAudioUrl] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)

  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const timerRef = useRef(null)
  const streamRef = useRef(null)
  const audioElemRef = useRef(null)
  const secondsRef = useRef(0)

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
    }
  }, [audioUrl])

  const formatTimer = (sec) => {
    const mins = Math.floor(sec / 60)
    const remainingSec = sec % 60
    return `${mins.toString().padStart(2, '0')}:${remainingSec.toString().padStart(2, '0')}`
  }

  const startRecording = async () => {
    setErrorMessage(null)

    // Check browser support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setErrorMessage('Browser does not support MediaRecorder or getUserMedia audio capture.')
      return
    }

    try {
      // Request microphone permission ONLY after user clicks
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
          sampleRate: 48000,
        },
      })

      streamRef.current = stream

      // Inform parent about stream (e.g. for live waveform analyser)
      if (onRecordingStart) {
        onRecordingStart(stream)
      }

      // Determine supported mime type
      let mimeType = 'audio/webm'
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus'
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        mimeType = 'audio/ogg;codecs=opus'
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4'
      }

      const mediaRecorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
        const url = URL.createObjectURL(audioBlob)
        setAudioUrl(url)
        setStatus('stopped')

        if (onRecordingComplete) {
          onRecordingComplete(audioBlob, url, secondsRef.current)
        }

        // Release hardware mic track
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop())
          streamRef.current = null
        }
      }

      mediaRecorder.onerror = (err) => {
        setErrorMessage(`Recording error: ${err.error?.message || 'Media capture failure'}`)
        stopRecording()
      }

      mediaRecorder.start(100) // Collect chunks every 100ms
      setStatus('recording')
      setSeconds(0)
      secondsRef.current = 0

      timerRef.current = setInterval(() => {
        secondsRef.current += 1
        setSeconds(secondsRef.current)
      }, 1000)
    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMessage(
          'Microphone permission denied. Please grant microphone access in your browser settings to capture audio.'
        )
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setErrorMessage('No microphone device detected on this system.')
      } else {
        setErrorMessage(`Unable to access audio input: ${err.message || 'Unknown error'}`)
      }
      setStatus('idle')
    }
  }

  const stopRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }

    if (onRecordingStop) {
      onRecordingStop()
    }
  }

  const clearRecording = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
    }
    setAudioUrl(null)
    setStatus('idle')
    setSeconds(0)
    secondsRef.current = 0
    setErrorMessage(null)
    audioChunksRef.current = []

    if (onClear) {
      onClear()
    }
  }

  return (
    <div className="space-y-4">
      {/* Error Banner */}
      {errorMessage && (
        <div className="flex items-start gap-2.5 rounded-lg border border-rose-500/40 bg-rose-950/40 p-3 text-xs text-rose-300">
          <AlertTriangleIcon className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold block uppercase tracking-wider text-[10px] text-rose-400">
              Hardware Ingestion Alert
            </span>
            <p className="leading-relaxed text-rose-200">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Recording Control Cockpit */}
      <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${
                status === 'recording'
                  ? 'bg-rose-500 animate-ping'
                  : status === 'stopped'
                  ? 'bg-emerald-400'
                  : 'bg-cyan-400'
              }`}
            />
            <span className="text-xs font-mono uppercase tracking-wider text-slate-300">
              {status === 'recording'
                ? 'RECORDING LIVE STREAM'
                : status === 'stopped'
                ? 'SAMPLE CAPTURED'
                : 'MICROPHONE STANDBY'}
            </span>
          </div>

          <div className="flex items-center gap-1.5 font-mono text-sm font-bold text-cyan-300">
            <RadioIcon className="h-3.5 w-3.5 text-cyan-400" />
            <span>{formatTimer(seconds)}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          {status !== 'recording' ? (
            <button
              type="button"
              onClick={startRecording}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-xs py-2.5 px-4 transition-all duration-200 shadow-[0_0_15px_rgba(6,182,212,0.25)] border border-cyan-400/30"
            >
              <MicIcon className="h-4 w-4" />
              <span>{status === 'stopped' ? 'Re-record Sample' : 'Start Recording'}</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={stopRecording}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs py-2.5 px-4 transition-all duration-200 shadow-[0_0_15px_rgba(244,63,94,0.3)] border border-rose-400/40"
            >
              <StopIcon className="h-4 w-4" />
              <span>Stop Recording</span>
            </button>
          )}

          {status === 'stopped' && (
            <button
              type="button"
              onClick={clearRecording}
              title="Clear recording"
              className="flex items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 hover:bg-slate-800 p-2.5 text-slate-400 hover:text-rose-400 transition-colors"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Playback Preview after Recording */}
        {status === 'stopped' && audioUrl && (
          <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-3 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span className="flex items-center gap-1 text-emerald-400">
                <CheckCircleIcon className="h-3.5 w-3.5" />
                <span>Audio Ingest Complete ({seconds}s)</span>
              </span>
              <span className="flex items-center gap-1 text-slate-400">
                <Volume2Icon className="h-3 w-3 text-cyan-400" />
                <span>Audio Preview</span>
              </span>
            </div>
            <audio
              ref={audioElemRef}
              src={audioUrl}
              controls
              className="w-full h-8 rounded accent-cyan-500"
            />
          </div>
        )}
      </div>
    </div>
  )
}
