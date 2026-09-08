import React, { useState, useRef, useEffect } from 'react'
import {
  UploadIcon,
  TrashIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  Volume2Icon,
  WaveformIcon,
  MicIcon,
  ClockIcon,
} from '../common/Icons'

const DEFAULT_EXTENSIONS = ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac', '.webm']
const ALLOWED_MIME_PREFIXES = ['audio/']

export default function AudioUploader({
  onFileSelected,
  onClear,
  onRecordLiveClick = null,
  allowedExtensions = DEFAULT_EXTENSIONS,
  maxSizeMB = 50,
  large = false,
}) {
  const [file, setFile] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const [audioDuration, setAudioDuration] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState(null)

  const fileInputRef = useRef(null)

  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
    }
  }, [audioUrl])

  const formatDuration = (sec) => {
    if (!sec || isNaN(sec)) return '--:--'
    const mins = Math.floor(sec / 60)
    const remainingSec = Math.floor(sec % 60)
    return `${mins.toString().padStart(2, '0')}:${remainingSec.toString().padStart(2, '0')}`
  }

  const validateAndProcessFile = (selectedFile) => {
    setError(null)

    if (!selectedFile) {
      return
    }

    // Check empty file
    if (selectedFile.size === 0) {
      setError('Selected audio file is empty (0 bytes). Please select a valid audio sample.')
      return
    }

    // Check max file size
    const maxBytes = maxSizeMB * 1024 * 1024
    if (selectedFile.size > maxBytes) {
      setError(`File size exceeds the ${maxSizeMB}MB limit (${(selectedFile.size / (1024 * 1024)).toFixed(1)}MB).`)
      return
    }

    // Check extension and mime
    const fileName = selectedFile.name.toLowerCase()
    const isExtensionValid = allowedExtensions.some((ext) => fileName.endsWith(ext.toLowerCase()))
    const isMimeValid = ALLOWED_MIME_PREFIXES.some((prefix) => selectedFile.type?.startsWith(prefix))

    if (!isExtensionValid && !isMimeValid) {
      setError(
        `Unsupported audio format. Supported formats: ${allowedExtensions.map((e) => e.toUpperCase().replace('.', '')).join(', ')}`
      )
      return
    }

    // Revoke previous URL if any
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
    }

    const url = URL.createObjectURL(selectedFile)
    setFile(selectedFile)
    setAudioUrl(url)

    // Probe duration using audio element
    const probe = new Audio()
    probe.src = url
    probe.onloadedmetadata = () => {
      const dur = probe.duration
      setAudioDuration(dur)
      if (onFileSelected) {
        onFileSelected(selectedFile, url, { duration: dur })
      }
    }
    probe.onerror = () => {
      setAudioDuration(null)
      if (onFileSelected) {
        onFileSelected(selectedFile, url, {})
      }
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcessFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcessFile(e.target.files[0])
    }
  }

  const handleRemove = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
    }
    setFile(null)
    setAudioUrl(null)
    setAudioDuration(null)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    if (onClear) {
      onClear()
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  const formatsDisplay = allowedExtensions
    .map((e) => e.toUpperCase().replace('.', ''))
    .join(', ')

  return (
    <div className="space-y-4">
      {/* Error Banner */}
      {error && (
        <div className="flex items-start gap-2.5 rounded-lg border border-rose-500/40 bg-rose-950/40 p-3 text-xs text-rose-300">
          <AlertTriangleIcon className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold block uppercase tracking-wider text-[10px] text-rose-400">
              Ingestion Validation Error
            </span>
            <p className="leading-relaxed text-rose-200">{error}</p>
          </div>
        </div>
      )}

      {/* Upload Zone */}
      {!file ? (
        <div className="space-y-3">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed text-center cursor-pointer transition-all duration-200 bg-slate-950/60 backdrop-blur-md ${
              large ? 'p-8 sm:p-10' : 'p-6'
            } ${
              isDragging
                ? 'border-cyan-400 bg-cyan-950/20 shadow-[0_0_25px_rgba(6,182,212,0.2)]'
                : 'border-slate-800/80 hover:border-cyan-500/50 hover:bg-slate-900/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={allowedExtensions.join(',')}
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 mb-3 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
              <UploadIcon className="h-6 w-6" />
            </div>
            <span className="text-sm font-semibold text-slate-100">
              Upload Audio Sample
            </span>
            <p className="mt-1 text-xs text-slate-400">
              Drag & drop your voice recording here, or{' '}
              <span className="text-cyan-400 font-medium underline underline-offset-2">browse files</span>
            </p>

            <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-[10px] font-mono text-slate-400">
              <span className="rounded bg-slate-900 px-2 py-0.5 border border-slate-800">
                FORMATS: {formatsDisplay}
              </span>
              <span className="rounded bg-slate-900 px-2 py-0.5 border border-slate-800">
                MAX SIZE: {maxSizeMB}MB
              </span>
            </div>
          </div>

          {/* Optional OR RECORD LIVE Switcher */}
          {onRecordLiveClick && (
            <div className="relative flex items-center justify-center pt-1">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-800/80" />
              </div>
              <div className="relative bg-slate-950 px-3 text-[10px] font-mono uppercase text-slate-400">
                OR
              </div>
            </div>
          )}

          {onRecordLiveClick && (
            <button
              type="button"
              onClick={onRecordLiveClick}
              className="w-full flex items-center justify-center gap-2 rounded-xl border border-slate-800/90 bg-slate-900/50 hover:bg-slate-900 hover:border-cyan-500/40 p-3 text-xs font-mono text-slate-300 hover:text-cyan-300 transition-all shadow-[0_0_15px_rgba(0,0,0,0.3)]"
            >
              <MicIcon className="h-4 w-4 text-cyan-400" />
              <span>RECORD LIVE FROM MICROPHONE</span>
            </button>
          )}
        </div>
      ) : (
        /* Selected File Card */
        <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                <WaveformIcon className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white truncate max-w-[200px] sm:max-w-xs">
                  {file.name}
                </h4>
                <div className="flex flex-wrap items-center gap-2 mt-0.5 text-[10px] font-mono text-slate-400">
                  <span>{formatFileSize(file.size)}</span>
                  {audioDuration && (
                    <>
                      <span>•</span>
                      <span className="flex items-center gap-1 text-slate-300">
                        <ClockIcon className="h-3 w-3 text-cyan-400" />
                        <span>{formatDuration(audioDuration)}</span>
                      </span>
                    </>
                  )}
                  <span>•</span>
                  <span className="uppercase text-cyan-400">{file.type || 'audio/raw'}</span>
                  <span>•</span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <CheckCircleIcon className="h-3 w-3" />
                    <span>Loaded</span>
                  </span>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleRemove}
              title="Remove audio file"
              className="flex items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 hover:bg-slate-800 p-2 text-slate-400 hover:text-rose-400 transition-colors"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          </div>

          {/* Audio Playback Controls */}
          {audioUrl && (
            <div className="pt-2 border-t border-slate-800/60 space-y-1.5">
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span className="flex items-center gap-1 text-cyan-400">
                  <Volume2Icon className="h-3 w-3" />
                  <span>Playback Monitor</span>
                </span>
                <span>FORENSIC BUFFER READY</span>
              </div>
              <audio src={audioUrl} controls className="w-full h-8 rounded accent-cyan-500" />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
