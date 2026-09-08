import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './components/layout/DashboardLayout'
import Home from './pages/Home'
import LiveAnalysis from './pages/LiveAnalysis'
import VoiceLab from './pages/VoiceLab'
import ThreatIntelligence from './pages/ThreatIntelligence'
import Reports from './pages/Reports'
import Settings from './pages/Settings'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route index element={<Home />} />
          <Route path="live-analysis" element={<LiveAnalysis />} />
          <Route path="voice-lab" element={<VoiceLab />} />
          <Route path="threat-intelligence" element={<ThreatIntelligence />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
