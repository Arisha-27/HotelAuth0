import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import FloorPlan from './pages/FloorPlan'
import Agents from './pages/Agents'
import Security from './pages/Security'
import Operations from './pages/Operations'
import Analytics from './pages/Analytics'
import Logs from './pages/Logs'
import Settings from './pages/Settings'
import HITL from './pages/HITL'
import Advanced from './pages/Advanced'

function App() {
  return (
    <Routes>
      {/* Public landing page */}
      <Route path="/landing" element={<Landing />} />

      {/* Dashboard routes — no auth required */}
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="floor-plan" element={<FloorPlan />} />
        <Route path="agents" element={<Agents />} />
        <Route path="security" element={<Security />} />
        <Route path="operations" element={<Operations />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="logs" element={<Logs />} />
        <Route path="hitl" element={<HITL />} />
        <Route path="advanced" element={<Advanced />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
