import axios from 'axios'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

function createAudioContext() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext
  if (!AudioContextClass) {
    throw new Error('Web Audio API is not supported by this browser')
  }
  return new AudioContextClass()
}

export function getRmsDb(waveform) {
  if (!waveform || waveform.length === 0) return -120
  let sum = 0
  for (let i = 0; i < waveform.length; i += 1) {
    const value = waveform[i]
    sum += value * value
  }
  const rms = Math.sqrt(sum / waveform.length)
  return 20 * Math.log10(Math.max(rms, 1e-12))
}

export async function analyzeWaveform({
  waveform,
  sampleRate,
  chunkId,
  sessionId,
  quality = 'HIGH',
  timestamp = new Date().toISOString(),
}) {
  if (!sessionId) throw new Error('sessionId is required')
  if (!chunkId) throw new Error('chunkId is required')
  if (!waveform || waveform.length === 0) throw new Error('waveform is empty')

  const payload = {
    waveform: Array.from(waveform),
    sample_rate: Math.round(sampleRate),
    chunk_id: chunkId,
    quality,
    timestamp,
    session_id: sessionId,
  }

  return apiClient.post('/api/v1/analyze', payload, {
    headers: {
      'Content-Type': 'application/json',
      'x-session-id': sessionId,
    },
  })
}

export async function decodeAudioFile(audioFile) {
  const context = createAudioContext()
  try {
    const bytes = await audioFile.arrayBuffer()
    const decoded = await context.decodeAudioData(bytes.slice(0))
    const channels = decoded.numberOfChannels
    const length = decoded.length
    const mono = new Float32Array(length)

    for (let channel = 0; channel < channels; channel += 1) {
      const data = decoded.getChannelData(channel)
      for (let i = 0; i < length; i += 1) {
        mono[i] += data[i] / channels
      }
    }

    return {
      waveform: mono,
      sampleRate: decoded.sampleRate,
      duration: decoded.duration,
    }
  } finally {
    await context.close()
  }
}

export async function analyzeAudioFile(audioFile, options = {}) {
  const {
    sessionId,
    windowSeconds = 2,
    hopSeconds = 1,
    silenceDb = -45,
    onChunk,
  } = options

  if (!sessionId) throw new Error('sessionId is required')

  const decoded = await decodeAudioFile(audioFile)
  const windowSize = Math.max(1, Math.round(decoded.sampleRate * windowSeconds))
  const hopSize = Math.max(1, Math.round(decoded.sampleRate * hopSeconds))
  const results = []
  let sequence = 0

  for (let start = 0; start < decoded.waveform.length; start += hopSize) {
    const end = Math.min(start + windowSize, decoded.waveform.length)
    const chunk = decoded.waveform.slice(start, end)

    if (chunk.length < decoded.sampleRate * 0.5) break

    const db = getRmsDb(chunk)
    if (db < silenceDb) continue

    sequence += 1
    const quality = db < -32 ? 'DEGRADED' : 'HIGH'
    const t0 = performance.now()

    const response = await analyzeWaveform({
      waveform: chunk,
      sampleRate: decoded.sampleRate,
      chunkId: `upload-${sessionId}-${String(sequence).padStart(6, '0')}`,
      sessionId,
      quality,
    })

    const latencyMs = performance.now() - t0
    const item = { ...response.data, client_latency_ms: latencyMs }
    results.push(item)
    if (onChunk) onChunk(item)
  }

  if (results.length === 0) {
    throw new Error('No usable speech windows were found in the selected audio file')
  }

  const worst = results.reduce((selected, item) => {
    if (!selected) return item
    const currentRisk = Number(item.risk_score || 0)
    const selectedRisk = Number(selected.risk_score || 0)
    if (currentRisk !== selectedRisk) return currentRisk > selectedRisk ? item : selected
    return Number(item.synthetic_probability || 0) > Number(selected.synthetic_probability || 0)
      ? item
      : selected
  }, null)

  return {
    data: worst,
    results,
    duration: decoded.duration,
  }
}

export async function checkBackendHealth() {
  return apiClient.get('/integration-health')
}

export default {
  analyzeWaveform,
  analyzeAudioFile,
  checkBackendHealth,
  apiClient,
}
