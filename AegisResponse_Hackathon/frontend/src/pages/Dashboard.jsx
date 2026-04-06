import { useState, useEffect, useRef } from 'react'
import {
  AlertTriangle, Send, MoreHorizontal, Cpu, MemoryStick,
  Thermometer, Users, TrendingUp, Zap, ChevronDown, ChevronRight,
  Bot, Activity, BedDouble, Wrench, Sparkles
} from 'lucide-react'
import { AGENTS, LOG_ENTRIES, CRITICAL_ALERTS, ROOMS_DATA, EFFICIENCY_DATA } from '../data/mockData'
import './Dashboard.css'

/* ── Compact Agent Status Row ── */
function AgentStatusRow({ agent, depth = 0 }) {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = agent.children?.length > 0

  return (
    <>
      <div
        className={`agent-row ${agent.status}`}
        style={{ paddingLeft: `${8 + depth * 14}px` }}
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        <span className={`status-dot ${agent.status}`} />
        <span className="agent-row-name font-mono">{agent.codename || agent.name}</span>
        <span className="agent-row-load font-mono">{agent.cpu}%</span>
        {hasChildren && (
          <ChevronRight size={10} className={`agent-row-chevron ${expanded ? 'open' : ''}`} />
        )}
      </div>
      {expanded && agent.children?.map(child => (
        <AgentStatusRow key={child.id} agent={child} depth={depth + 1} />
      ))}
    </>
  )
}

function AgentPanel() {
  const exec = AGENTS[0]
  const activeCount = (() => {
    let count = 0
    const walk = (a) => { if (a.status === 'active') count++; a.children?.forEach(walk) }
    walk(exec)
    return count
  })()

  return (
    <div className="card dash-card">
      <div className="card-header">
        <h3><Bot size={12} style={{ marginRight: 6, verticalAlign: -1 }} />AGENT STATUS</h3>
        <span className="font-mono text-xs" style={{ color: 'var(--accent-primary-light)' }}>{activeCount} ACTIVE</span>
      </div>
      <div className="agent-list-compact">
        <AgentStatusRow agent={exec} depth={0} />
      </div>
    </div>
  )
}

/* ── Command Input (compact) ── */
function CommandInput() {
  const [value, setValue] = useState('')
  const [lastResponse, setLastResponse] = useState('[IOT_GATEWAY] Room 712 — Occupied | 22.1°C | HVAC: ACTIVE')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!value.trim()) return
    setLastResponse(`[EXECUTIVE] Parsed intent "${value.replace(/\s+/g, '_')}" — delegated.`)
    setValue('')
  }

  return (
    <div className="card dash-card command-compact">
      <div className="command-last-response font-mono">{lastResponse}</div>
      <form className="command-input-bar" onSubmit={handleSubmit}>
        <span className="command-prompt font-mono">&gt;</span>
        <input
          type="text"
          className="command-input font-mono"
          placeholder="Enter command..."
          value={value}
          onChange={e => setValue(e.target.value)}
        />
        <button type="submit" className="command-submit-btn">
          <Send size={12} />
        </button>
      </form>
    </div>
  )
}

/* ── Isometric Floor Plan (SVG) ── */
function FloorWireframe() {
  const rooms = [
    { gx: 0, gy: 0, label: '714', status: 'occupied' },
    { gx: 1, gy: 0, label: '713', status: 'occupied' },
    { gx: 2, gy: 0, label: '715', status: 'available' },
    { gx: 3, gy: 0, label: '720', status: 'occupied' },
    { gx: 4, gy: 0, label: '719', status: 'occupied' },
    { gx: 0, gy: 1, label: '709', status: 'occupied' },
    { gx: 1, gy: 1, label: '706', status: 'maintenance' },
    { gx: 3, gy: 1, label: '721', status: 'occupied' },
    { gx: 4, gy: 1, label: '722', status: 'occupied' },
    { gx: 0, gy: 2, label: '701', status: 'occupied' },
    { gx: 2, gy: 2, label: '711', status: 'highlight', guest: 'S. Chen' },
    { gx: 3, gy: 2, label: '712', status: 'occupied' },
    { gx: 4, gy: 2, label: '723', status: 'occupied' },
    { gx: 0, gy: 3, label: '704', status: 'occupied' },
    { gx: 1, gy: 3, label: '703', status: 'occupied' },
    { gx: 2, gy: 3, label: '702', status: 'occupied' },
    { gx: 3, gy: 3, label: '724', status: 'available' },
    { gx: 0, gy: 4, label: '700', status: 'cleaning' },
    { gx: 1, gy: 4, label: '705', status: 'occupied' },
  ]

  // Isometric projection
  const cellW = 84
  const cellH = 48
  const originX = 320
  const originY = 60
  const isoX = (gx, gy) => originX + (gx - gy) * (cellW / 2)
  const isoY = (gx, gy) => originY + (gx + gy) * (cellH / 2)

  const roomW = 36
  const roomH = 21
  const wallH = 18

  // Diamond shape for iso top face
  const diamond = (cx, cy, w, h) =>
    `${cx},${cy - h} ${cx + w},${cy} ${cx},${cy + h} ${cx - w},${cy}`

  // 3D box paths
  const boxTop = (cx, cy, w, h) => diamond(cx, cy - wallH, w, h)
  const boxLeft = (cx, cy, w, h) =>
    `${cx - w},${cy - wallH} ${cx},${cy + h - wallH} ${cx},${cy + h} ${cx - w},${cy}`
  const boxRight = (cx, cy, w, h) =>
    `${cx + w},${cy - wallH} ${cx},${cy + h - wallH} ${cx},${cy + h} ${cx + w},${cy}`

  const getStroke = (status) => {
    if (status === 'highlight') return '#FF9900'
    if (status === 'maintenance') return '#E53935'
    if (status === 'available') return '#3A5A3A'
    if (status === 'cleaning') return '#3A4A6A'
    return '#4A4530'
  }

  const getFill = (status) => {
    if (status === 'highlight') return 'rgba(255,153,0,0.12)'
    if (status === 'maintenance') return 'rgba(229,57,53,0.08)'
    if (status === 'available') return 'rgba(90,90,99,0.05)'
    if (status === 'cleaning') return 'rgba(74,144,217,0.06)'
    return 'rgba(255,184,77,0.04)'
  }

  return (
    <div className="card dash-card wireframe-card">
      <div className="card-header">
        <h3>3D WIREFRAME</h3>
        <div className="wireframe-floor-badge font-mono">
          Level 7 <ChevronDown size={10} />
        </div>
      </div>
      <div className="wireframe-body">
        <svg viewBox="0 0 640 340" className="wireframe-svg" preserveAspectRatio="xMidYMid meet">
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Grid floor lines */}
          {Array.from({ length: 6 }).map((_, i) => {
            const x1 = isoX(i, -0.5)
            const y1 = isoY(i, -0.5)
            const x2 = isoX(i, 4.5)
            const y2 = isoY(i, 4.5)
            return <line key={`gv-${i}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#1A1A1D" strokeWidth="0.5" />
          })}
          {Array.from({ length: 6 }).map((_, i) => {
            const x1 = isoX(-0.5, i)
            const y1 = isoY(-0.5, i)
            const x2 = isoX(4.5, i)
            const y2 = isoY(4.5, i)
            return <line key={`gh-${i}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#1A1A1D" strokeWidth="0.5" />
          })}

          {/* Rooms */}
          {rooms.map(room => {
            const cx = isoX(room.gx, room.gy)
            const cy = isoY(room.gx, room.gy)
            const stroke = getStroke(room.status)
            const fill = getFill(room.status)
            const isHighlight = room.status === 'highlight'

            return (
              <g key={room.label} className="wireframe-room" filter={isHighlight ? 'url(#glow)' : undefined}>
                {/* Left face */}
                <polygon points={boxLeft(cx, cy, roomW, roomH)}
                  fill={isHighlight ? 'rgba(255,153,0,0.06)' : 'rgba(10,10,11,0.5)'}
                  stroke={stroke} strokeWidth={isHighlight ? 1.5 : 0.7}
                />
                {/* Right face */}
                <polygon points={boxRight(cx, cy, roomW, roomH)}
                  fill={isHighlight ? 'rgba(255,153,0,0.04)' : 'rgba(15,15,18,0.5)'}
                  stroke={stroke} strokeWidth={isHighlight ? 1.5 : 0.7}
                />
                {/* Top face */}
                <polygon points={boxTop(cx, cy, roomW, roomH)}
                  fill={fill}
                  stroke={stroke} strokeWidth={isHighlight ? 1.5 : 0.7}
                />
                {/* Room label */}
                <text x={cx} y={cy - wallH - 4}
                  textAnchor="middle" fontSize="8"
                  fill={isHighlight ? '#FFB84D' : '#6A6A73'}
                  fontFamily="'JetBrains Mono', monospace"
                >
                  {room.label}
                </text>
                {/* Status dot */}
                {room.status === 'occupied' && (
                  <circle cx={cx + 10} cy={cy - wallH - 2} r="2" fill="#B4C4B1" opacity="0.7" />
                )}
                {room.status === 'maintenance' && (
                  <circle cx={cx + 10} cy={cy - wallH - 2} r="2" fill="#E53935" opacity="0.8" />
                )}
                {/* Highlight extra info */}
                {isHighlight && room.guest && (
                  <>
                    <text x={cx} y={cy + roomH + 10} textAnchor="middle" fontSize="6.5"
                      fill="#FFB84D" fontFamily="'JetBrains Mono', monospace">
                      GUEST: {room.guest}
                    </text>
                    <text x={cx} y={cy + roomH + 20} textAnchor="middle" fontSize="6"
                      fill="#8A8A93" fontFamily="'JetBrains Mono', monospace">
                      OCCUPIED • 21.5°C
                    </text>
                  </>
                )}
              </g>
            )
          })}
        </svg>

        <div className="wireframe-legend">
          <span className="legend-item"><span className="legend-dot occupied" /> Occupied</span>
          <span className="legend-item"><span className="legend-dot available" /> Available</span>
          <span className="legend-item"><span className="legend-dot maintenance" /> Maint.</span>
        </div>
      </div>
    </div>
  )
}

/* ── Live Log (compact) ── */
function LiveLog() {
  const [logs, setLogs] = useState(LOG_ENTRIES.slice(0, 12))

  useEffect(() => {
    const interval = setInterval(() => {
      const agents = ['EXECUTIVE', 'SECURITY', 'IOT_GATEWAY', 'CONCIERGE', 'OPERATIONS']
      const messages = [
        'Heartbeat check — all systems nominal',
        'Room sensor data aggregated — 300 endpoints',
        'Guest request processed — Room 405',
        'Access log synchronized with central DB',
        'Energy grid balancing — peak load managed',
      ]
      const levels = ['info', 'action', 'info', 'info', 'action']
      const idx = Math.floor(Math.random() * agents.length)
      const now = new Date()
      const time = [now.getHours(), now.getMinutes(), now.getSeconds()]
        .map(n => String(n).padStart(2, '0')).join(':')
      setLogs(prev => [{
        time, agent: agents[idx], message: messages[idx], level: levels[idx],
      }, ...prev.slice(0, 14)])
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="card dash-card log-card">
      <div className="card-header">
        <h3>LIVE EVENT LOG</h3>
        <button className="btn btn-ghost" style={{ padding: '2px 6px' }}>
          <MoreHorizontal size={12} />
        </button>
      </div>
      <div className="log-body font-mono">
        {logs.map((log, i) => (
          <div key={i} className={`log-entry ${log.level}`}>
            <span className="log-time">[{log.time}]</span>
            <span className="log-agent">{log.agent}:</span>
            <span className="log-message">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── Alerts (compact) ── */
function AlertsPanel() {
  return (
    <div className="card dash-card">
      <div className="card-header">
        <h3><AlertTriangle size={12} style={{ marginRight: 6, verticalAlign: -1, color: 'var(--accent-primary)' }} />ALERTS</h3>
        <span className="font-mono text-xs" style={{ color: 'var(--status-critical)' }}>{CRITICAL_ALERTS.length}</span>
      </div>
      <div className="alerts-compact">
        {CRITICAL_ALERTS.map(alert => (
          <div key={alert.id} className={`alert-row severity-${alert.severity}`}>
            <span className="alert-row-room font-mono">{alert.room}</span>
            <span className="alert-row-issue font-mono">{alert.issue}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── Stats Row ── */
function StatsRow() {
  const { occupancyRate, occupied, totalRooms, available, maintenance, cleaning } = ROOMS_DATA
  const efficiency = EFFICIENCY_DATA[EFFICIENCY_DATA.length - 1].value

  return (
    <div className="stats-row">
      <div className="stat-tile card">
        <BedDouble size={14} className="stat-tile-icon" />
        <div className="stat-tile-data">
          <span className="stat-tile-value font-mono">{occupancyRate}%</span>
          <span className="stat-tile-label">OCCUPANCY</span>
        </div>
        <div className="stat-tile-bar">
          <div className="progress-bar"><div className="progress-bar-fill" style={{ width: `${occupancyRate}%` }} /></div>
        </div>
      </div>
      <div className="stat-tile card">
        <Activity size={14} className="stat-tile-icon" />
        <div className="stat-tile-data">
          <span className="stat-tile-value font-mono">{efficiency}%</span>
          <span className="stat-tile-label">EFFICIENCY</span>
        </div>
        <div className="stat-tile-bar">
          <div className="progress-bar"><div className="progress-bar-fill positive" style={{ width: `${efficiency}%` }} /></div>
        </div>
      </div>
      <div className="stat-tile card">
        <Users size={14} className="stat-tile-icon" />
        <div className="stat-tile-data">
          <span className="stat-tile-value font-mono">{occupied}</span>
          <span className="stat-tile-label">ROOMS OCC.</span>
        </div>
      </div>
      <div className="stat-tile card">
        <Wrench size={14} className="stat-tile-icon" />
        <div className="stat-tile-data">
          <span className="stat-tile-value font-mono" style={{ color: 'var(--status-critical)' }}>{maintenance}</span>
          <span className="stat-tile-label">MAINT.</span>
        </div>
      </div>
    </div>
  )
}

/* ── Dashboard Page ── */
export default function Dashboard() {
  return (
    <div className="dashboard-layout">
      {/* Top stats row */}
      <StatsRow />

      {/* Main content: 3 columns */}
      <div className="dashboard-main">
        {/* Left: Agents + Command */}
        <div className="dash-col-left">
          <AgentPanel />
          <CommandInput />
        </div>

        {/* Center: Floor wireframe */}
        <div className="dash-col-center">
          <FloorWireframe />
        </div>

        {/* Right: Alerts + Log */}
        <div className="dash-col-right">
          <AlertsPanel />
          <LiveLog />
        </div>
      </div>
    </div>
  )
}
