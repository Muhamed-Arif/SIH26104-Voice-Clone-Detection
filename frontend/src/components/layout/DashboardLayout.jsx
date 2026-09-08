import React from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Sidebar from './Sidebar'
import Navbar from './Navbar'

export default function DashboardLayout() {
  const location = useLocation()

  return (
    <div className="relative flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 antialiased selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Background Ambience / Subtle Cybersecurity Glow */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/4 h-96 w-96 rounded-full bg-cyan-600/10 blur-[128px]" />
        <div className="absolute top-1/3 -right-20 h-96 w-96 rounded-full bg-blue-600/10 blur-[140px]" />
        <div className="absolute -bottom-40 left-1/3 h-96 w-96 rounded-full bg-violet-600/10 blur-[150px]" />
        {/* Subtle cyber grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `radial-gradient(#38bdf8 1px, transparent 1px)`,
            backgroundSize: '24px 24px',
          }}
        />
      </div>

      {/* Persistent Left Sidebar */}
      <Sidebar />

      {/* Right Column: Navbar + Dynamic Content Area */}
      <div className="relative z-10 flex flex-1 flex-col overflow-hidden">
        <Navbar />

        {/* Scrollable Main Area (No horizontal scrolling) */}
        <main className="relative flex-1 overflow-y-auto overflow-x-hidden p-5 sm:p-6 lg:p-7">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25, ease: 'easeInOut' }}
              className="mx-auto max-w-[1720px] h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
