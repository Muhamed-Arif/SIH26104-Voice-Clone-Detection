import React from 'react'
import GlassPanel from '../components/common/GlassPanel'
import {
  FileTextIcon,
  BarChartIcon,
  ShieldCheckIcon,
} from '../components/common/Icons'

const reports = [
  {
    id: 'AV-2026-0906-A',
    title: 'Daily Executive Threat Summary',
    description: 'Acoustic threat interceptions',
    threats: 14,
    format: 'PDF / JSON',
    date: '06 Sep 2026',
  },
  {
    id: 'AV-2026-0906-B',
    title: 'Weekly Telemetry Overview',
    description: 'Voice impersonation detection telemetry',
    threats: 19,
    format: 'PDF / CSV',
    date: '06 Sep 2026',
  },
]

function downloadJSON(report) {
  const data = {
    reportId: report.id,
    title: report.title,
    date: report.date,
    threatsDetected: report.threats,
    system: 'AetherVoice',
    problemStatement: 'SIH26104',
    verification: 'SHA-256',
    mode: 'DEMO',
  }

  const blob = new Blob(
    [JSON.stringify(data, null, 2)],
    { type: 'application/json' }
  )

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = `${report.id}.json`
  link.click()

  URL.revokeObjectURL(url)
}

function downloadCSV(report) {
  const csv = [
    'Report ID,Title,Date,Threats Detected,Status',
    `"${report.id}","${report.title}","${report.date}",${report.threats},"VERIFIED"`,
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv' })

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = `${report.id}.csv`
  link.click()

  URL.revokeObjectURL(url)
}

function generateReport() {
  window.print()
}

export default function Reports() {
  return (
    <div className="space-y-6 pb-8">

      {/* HEADER */}
      <div className="border-b border-slate-800/80 pb-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-violet-500/30 bg-violet-500/10 text-violet-400">
              <FileTextIcon className="h-5 w-5" />
            </div>

            <div>
              <h1 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
                Incident & Compliance Reports
              </h1>

              <p className="text-xs text-slate-400">
                Forensic evidence, detection telemetry & audit reports
              </p>
            </div>

          </div>

          <button
            onClick={generateReport}
            className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-4 py-2 text-xs font-semibold text-cyan-300 transition hover:bg-cyan-500/20"
          >
            Generate Report
          </button>

        </div>
      </div>

      {/* SYSTEM STATUS */}
      <div className="rounded-xl border border-violet-500/30 bg-gradient-to-r from-violet-950/40 via-slate-900/60 to-slate-950/80 p-5 backdrop-blur-xl">

        <div className="flex items-start gap-3">

          <span className="relative mt-1 flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-violet-400 opacity-60" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-violet-500" />
          </span>

          <div>
            <h2 className="text-sm font-semibold text-violet-300">
              FORENSIC AUDIT SYSTEM // ONLINE
            </h2>

            <p className="mt-1 text-xs leading-relaxed text-slate-400">
              AetherVoice audit pipeline is ready for detection summaries,
              forensic evidence packaging and compliance exports.
            </p>
          </div>

        </div>

      </div>

      {/* STATISTICS */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">

        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-[10px] font-semibold tracking-wider text-slate-500">
            REPORTS GENERATED
          </p>

          <p className="mt-2 text-2xl font-bold text-white">
            24
          </p>

          <p className="mt-1 text-[10px] text-cyan-400">
            Audit trail active
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-[10px] font-semibold tracking-wider text-slate-500">
            THREATS DOCUMENTED
          </p>

          <p className="mt-2 text-2xl font-bold text-rose-400">
            19
          </p>

          <p className="mt-1 text-[10px] text-slate-500">
            Voice impersonation vectors
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-[10px] font-semibold tracking-wider text-slate-500">
            EVIDENCE INTEGRITY
          </p>

          <p className="mt-2 text-2xl font-bold text-emerald-400">
            VERIFIED
          </p>

          <p className="mt-1 text-[10px] text-emerald-400">
            SHA-256 enabled
          </p>
        </div>

      </div>

      {/* MAIN REPORT GRID */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">

        {/* DETECTION REPORTS */}
        <GlassPanel
          title="Detection Reports"
          subtitle="Executive & telemetry summaries"
          icon={BarChartIcon}
        >

          <div className="space-y-3">

            {reports.map((report) => (
              <div
                key={report.id}
                className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 transition hover:border-cyan-500/30"
              >

                <div className="flex items-start justify-between gap-3">

                  <div className="min-w-0">

                    <p className="text-sm font-semibold text-slate-200">
                      {report.title}
                    </p>

                    <p className="mt-1 text-[11px] text-slate-500">
                      {report.description}
                    </p>

                    <p className="mt-2 font-mono text-[10px] text-slate-600">
                      {report.id}
                    </p>

                  </div>

                  <span className="shrink-0 rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-[9px] font-semibold text-emerald-400">
                    VERIFIED
                  </span>

                </div>

                <div className="mt-3 flex items-center justify-between border-t border-slate-800 pt-3">

                  <span className="text-[10px] text-slate-500">
                    {report.threats} threats • {report.date}
                  </span>

                  <span className="text-[10px] text-cyan-400">
                    {report.format}
                  </span>

                </div>

                <div className="mt-3 flex gap-2">

                  <button
                    onClick={() => downloadJSON(report)}
                    className="rounded-md border border-cyan-500/20 bg-cyan-500/10 px-3 py-1.5 text-[10px] font-semibold text-cyan-300 transition hover:bg-cyan-500/20"
                  >
                    Export JSON
                  </button>

                  <button
                    onClick={() => downloadCSV(report)}
                    className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-[10px] font-semibold text-slate-300 transition hover:bg-slate-800"
                  >
                    Export CSV
                  </button>

                </div>

              </div>
            ))}

          </div>

        </GlassPanel>

        {/* FORENSIC EVIDENCE */}
        <GlassPanel
          title="Forensic Evidence Packages"
          subtitle="Cryptographically verified audio evidence"
          icon={ShieldCheckIcon}
        >

          <div className="space-y-4">

            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">

              <div className="flex items-center gap-2">

                <ShieldCheckIcon className="h-4 w-4 text-emerald-400" />

                <span className="text-xs font-semibold text-emerald-400">
                  SHA-256 HASH VERIFIED
                </span>

              </div>

              <p className="mt-3 break-all font-mono text-[10px] leading-relaxed text-slate-500">
                7f3c91a2b8e4d61c9a12f4e8b71d0c32...
              </p>

            </div>

            {/* EVIDENCE DETAILS */}
            <div className="grid grid-cols-2 gap-3">

              <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
                <p className="text-[9px] text-slate-500">
                  SAMPLE ID
                </p>

                <p className="mt-1 font-mono text-xs text-slate-200">
                  AV-01924
                </p>
              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
                <p className="text-[9px] text-slate-500">
                  MODEL VERSION
                </p>

                <p className="mt-1 font-mono text-xs text-cyan-400">
                  AV-DET-1.0
                </p>
              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
                <p className="text-[9px] text-slate-500">
                  AUDIO DURATION
                </p>

                <p className="mt-1 text-xs text-slate-200">
                  12.48 sec
                </p>
              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
                <p className="text-[9px] text-slate-500">
                  SAMPLE RATE
                </p>

                <p className="mt-1 text-xs text-slate-200">
                  48 kHz
                </p>
              </div>

            </div>

            {/* EVIDENCE CHAIN */}
            <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-4">

              <p className="text-[10px] font-semibold tracking-wider text-cyan-400">
                EVIDENCE CHAIN
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-2 font-mono text-[9px]">

                <span className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-300">
                  AUDIO
                </span>

                <span className="text-slate-600">
                  →
                </span>

                <span className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-300">
                  ANALYSIS
                </span>

                <span className="text-slate-600">
                  →
                </span>

                <span className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-300">
                  HASH
                </span>

                <span className="text-slate-600">
                  →
                </span>

                <span className="rounded border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-emerald-400">
                  VERIFIED
                </span>

              </div>

            </div>

          </div>

        </GlassPanel>

      </div>

      {/* DEMO NOTICE */}
      <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">

        <p className="text-[10px] leading-relaxed text-amber-300/80">
          DEMONSTRATION MODE — Report values and forensic metadata shown here
          are simulated frontend data. Real detection results will be supplied
          by the AetherVoice analysis backend.
        </p>

      </div>

    </div>
  )
}