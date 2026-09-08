import React from 'react'
import { ClockIcon, ActivityIcon, InfoIcon } from '../common/Icons'

export default function ChunkTimeline({ chunks = [], windowSeconds = 2, hopSeconds = 1 }) {
  return (
    <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-4 backdrop-blur-md space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3 gap-3">
        <div className="flex items-center gap-2">
          <ClockIcon className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Temporal Chunk Ingestion & Verdict Timeline
          </span>
        </div>
        <span className="text-[10px] font-mono text-slate-400 text-right">
          WINDOW: {windowSeconds}s // HOP: {hopSeconds}s
        </span>
      </div>

      {chunks.length === 0 ? (
        <div className="rounded-lg bg-slate-900/40 border border-slate-800/70 p-6 text-center space-y-2">
          <div className="flex justify-center text-slate-500">
            <ActivityIcon className="h-6 w-6 animate-pulse" />
          </div>
          <div className="text-xs font-mono font-medium text-slate-300">
            Awaiting Live Audio Segmentation
          </div>
          <p className="text-[11px] text-slate-400 max-w-md mx-auto">
            Start the microphone or upload audio. Each usable speech window is sent to the backend and its REAL / synthetic verdict appears here.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="sticky top-0 bg-slate-950">
              <tr className="border-b border-slate-800 text-[10px] text-slate-400 uppercase">
                <th className="py-2 px-3">Audio Chunk</th>
                <th className="py-2 px-3">Timestamp</th>
                <th className="py-2 px-3">Verdict</th>
                <th className="py-2 px-3">Confidence</th>
                <th className="py-2 px-3">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {[...chunks].reverse().map((chunk, index) => (
                <tr key={`${chunk.id}-${index}`} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-2 px-3 text-cyan-300 max-w-[240px] truncate">{chunk.id || index + 1}</td>
                  <td className="py-2 px-3 text-slate-400">{chunk.timestamp}</td>
                  <td className="py-2 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        chunk.verdict === 'synthetic'
                          ? 'bg-rose-950/60 text-rose-300 border border-rose-500/40'
                          : chunk.verdict === 'human'
                            ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/40'
                            : 'bg-amber-950/50 text-amber-300 border border-amber-500/30'
                      }`}
                    >
                      {chunk.verdict?.toUpperCase() || 'UNVERIFIED'}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-slate-300">{chunk.confidence || '--'}</td>
                  <td className="py-2 px-3 text-slate-300">{chunk.risk ?? '--'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 pt-1">
        <InfoIcon className="h-3 w-3 shrink-0 text-slate-400" />
        <span>Rolling chunk history helps avoid judging the call from a single brief transition or pause.</span>
      </div>
    </div>
  )
}
