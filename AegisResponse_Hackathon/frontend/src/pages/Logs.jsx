import { useState, useEffect, useRef } from 'react'
import { ScrollText, Filter, Download, Pause, Play, Search, X } from 'lucide-react'
import { LOG_ENTRIES } from '../data/mockData'
import './Logs.css'

const FULL_LOG = [
  ...LOG_ENTRIES,
  { time: '22:43:22', agent: 'EXECUTIVE', message: 'Scheduled maintenance window — Floor 2 IoT devices', level: 'info' },
  { time: '22:43:05', agent: 'CLEAN', message: 'Room 408: Deep clean completed — quality score 97/100', level: 'info' },
  { time: '22:42:50', agent: 'RESERVE', message: 'Cancellation processed: Conf #GV-20231028-B', level: 'info' },
  { time: '22:42:35', agent: 'SECURITY', message: 'Staff shift change logged — Night crew Alpha on duty', level: 'info' },
  { time: '22:42:18', agent: 'IOT_GATEWAY', message: 'Room 305: Mini-bar sensor triggered — restock required', level: 'action' },
  { time: '22:42:00', agent: 'EXECUTIVE', message: 'Revenue optimization cycle complete — yield adjusted for Nov bookings', level: 'info' },
  { time: '22:41:45', agent: 'OPERATIONS', message: 'Laundry batch #LB-445 processed — 120 items', level: 'info' },
  { time: '22:41:30', agent: 'SURVEILLANCE', message: 'Parking Garage L1: Vehicle count — 87/150 capacity', level: 'info' },
  { time: '22:41:15', agent: 'CONCIERGE', message: 'Room 610: Restaurant reservation confirmed — 8:30 PM, 4 guests', level: 'action' },
  { time: '22:41:00', agent: 'SECURITY', message: 'Fire panel status: All zones GREEN', level: 'info' },
  { time: '22:40:45', agent: 'IOT_GATEWAY', message: 'Pool area: Water temp 28.5°C — heater cycling off', level: 'info' },
  { time: '22:40:30', agent: 'EXECUTIVE', message: 'Guest satisfaction pulse survey — 4.7/5.0 rolling average', level: 'info' },
  { time: '22:40:15', agent: 'MAINTENANCE', message: 'Elevator B: Monthly inspection passed — cert #EI-2023-10-B', level: 'info' },
  { time: '22:40:00', agent: 'CLEAN', message: 'Floor 3: Turndown service completed — 12/12 rooms', level: 'info' },
  { time: '22:39:45', agent: 'SENTINEL', message: 'Network perimeter: 0 intrusion attempts in last 6h', level: 'info' },
  { time: '22:39:30', agent: 'IOT_GATEWAY', message: 'Building management: Solar panel output 12.4 kW', level: 'info' },
  { time: '22:39:15', agent: 'RESERVE', message: 'Walk-in guest assigned Room 215 — Express check-in via kiosk', level: 'action' },
  { time: '22:39:00', agent: 'OPERATIONS', message: 'Kitchen equipment diagnostic complete — all units nominal', level: 'info' },
  { time: '22:38:45', agent: 'EXECUTIVE', message: 'Weather advisory updated: Thunderstorm warning until 06:00 UTC', level: 'warning' },
  { time: '22:38:30', agent: 'SECURITY', message: 'Emergency lighting test: All 42 units — PASS', level: 'info' },
]

const AGENTS = ['ALL', 'EXECUTIVE', 'SECURITY', 'OPERATIONS', 'IOT_GATEWAY', 'CONCIERGE', 'SURVEILLANCE', 'MAINTENANCE', 'CLEAN', 'RESERVE', 'SENTINEL', 'LEDGER', 'HOUSEKEEPING']
const LEVELS = ['ALL', 'INFO', 'ACTION', 'WARNING']

export default function Logs() {
  const [logs, setLogs] = useState(FULL_LOG)
  const [paused, setPaused] = useState(false)
  const [agentFilter, setAgentFilter] = useState('ALL')
  const [levelFilter, setLevelFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const logRef = useRef(null)

  // Add new logs periodically
  useEffect(() => {
    if (paused) return
    const interval = setInterval(() => {
      const agents = ['EXECUTIVE', 'SECURITY', 'IOT_GATEWAY', 'CONCIERGE', 'OPERATIONS', 'MAINTENANCE', 'CLEAN']
      const messages = [
        'Heartbeat broadcast — all systems nominal',
        'Room sensor data aggregation cycle complete',
        'Guest request routed to domain handler',
        'Access log batch synchronized',
        'Energy grid load balancing — within tolerance',
        'CCTV frame analysis — no anomalies',
        'Room 504: Service request resolved',
      ]
      const levels = ['info', 'action', 'info', 'info', 'action', 'info', 'info']
      const idx = Math.floor(Math.random() * agents.length)
      const now = new Date()
      const time = [now.getHours(), now.getMinutes(), now.getSeconds()]
        .map(n => String(n).padStart(2, '0')).join(':')

      setLogs(prev => [{
        time,
        agent: agents[idx],
        message: messages[idx],
        level: levels[idx],
      }, ...prev.slice(0, 100)])
    }, 3000)
    return () => clearInterval(interval)
  }, [paused])

  const filteredLogs = logs.filter(log => {
    if (agentFilter !== 'ALL' && log.agent !== agentFilter) return false
    if (levelFilter !== 'ALL' && log.level !== levelFilter.toLowerCase()) return false
    if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase()) && !log.agent.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  const agentCounts = {}
  logs.forEach(log => {
    agentCounts[log.agent] = (agentCounts[log.agent] || 0) + 1
  })

  return (
    <div className="logs-page">
      <div className="logs-header">
        <div className="logs-title">
          <ScrollText size={18} className="text-accent" />
          <h1>SYSTEM EVENT LOGS</h1>
        </div>
        <div className="logs-actions">
          <span className="log-count font-mono text-xs text-muted">{filteredLogs.length} ENTRIES</span>
          <button className={`btn ${paused ? 'btn-primary' : ''}`} onClick={() => setPaused(!paused)}>
            {paused ? <Play size={12} /> : <Pause size={12} />}
            {paused ? 'RESUME' : 'PAUSE'}
          </button>
          <button className="btn">
            <Download size={12} /> EXPORT
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="logs-filters">
        <div className="filter-search">
          <Search size={14} className="search-icon" />
          <input
            type="text"
            className="input"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{ paddingLeft: '32px' }}
          />
          {searchQuery && (
            <button className="search-clear" onClick={() => setSearchQuery('')}>
              <X size={12} />
            </button>
          )}
        </div>

        <div className="filter-group">
          <Filter size={12} className="text-muted" />
          <span className="text-xs text-muted uppercase">Agent:</span>
          <div className="filter-pills">
            {AGENTS.map(agent => (
              <button
                key={agent}
                className={`filter-pill font-mono ${agentFilter === agent ? 'active' : ''}`}
                onClick={() => setAgentFilter(agent)}
              >
                {agent}
                {agent !== 'ALL' && agentCounts[agent] && (
                  <span className="pill-count">{agentCounts[agent]}</span>
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="filter-group">
          <span className="text-xs text-muted uppercase">Level:</span>
          <div className="filter-pills">
            {LEVELS.map(level => (
              <button
                key={level}
                className={`filter-pill font-mono ${levelFilter === level ? 'active' : ''} level-${level.toLowerCase()}`}
                onClick={() => setLevelFilter(level)}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Log Table */}
      <div className="card logs-table-card">
        <div className="logs-table-header font-mono">
          <span className="log-col-time">TIMESTAMP</span>
          <span className="log-col-agent">AGENT</span>
          <span className="log-col-level">LEVEL</span>
          <span className="log-col-message">MESSAGE</span>
        </div>
        <div className="logs-table-body" ref={logRef}>
          {filteredLogs.map((log, i) => (
            <div
              key={`${log.time}-${i}`}
              className={`log-table-row ${log.level} ${i === 0 && !paused ? 'new-entry' : ''}`}
            >
              <span className="log-col-time font-mono text-muted">[{log.time}]</span>
              <span className="log-col-agent font-mono">{log.agent}</span>
              <span className="log-col-level">
                <span className={`level-badge ${log.level}`}>{log.level.toUpperCase()}</span>
              </span>
              <span className="log-col-message font-mono">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
