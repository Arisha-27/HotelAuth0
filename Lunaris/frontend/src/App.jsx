import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import FloorPlan from './pages/FloorPlan'
import Agents from './pages/Agents'
import Security from './pages/Security'
import Operations from './pages/Operations'
import Analytics from './pages/Analytics'
import Logs from './pages/Logs'
import Settings from './pages/Settings'
import Landing from './pages/Landing'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/dashboard" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="floor-plan" element={<FloorPlan />} />
        <Route path="agents" element={<Agents />} />
        <Route path="security" element={<Security />} />
        <Route path="operations" element={<Operations />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="logs" element={<Logs />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
