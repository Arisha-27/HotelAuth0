import { useState } from 'react'
import { Bot, Cpu, MemoryStick, Clock, Activity, ChevronRight, Zap, CheckCircle } from 'lucide-react'
import { AGENTS } from '../data/mockData'
import './Agents.css'

function flattenAgents(agents, depth = 0) {
  let result = []
  for (const agent of agents) {
    result.push({ ...agent, depth })
    if (agent.children) {
      result = result.concat(flattenAgents(agent.children, depth + 1))
    }
  }
  return result
}

function AgentDetailCard({ agent, onClose }) {
  const [showTasks, setShowTasks] = useState(false)
  const mockTasks = [
    { id: 'T-001', name: 'Health check broadcast', status: 'completed', time: '2m ago' },
    { id: 'T-002', name: 'Sensor data aggregation', status: 'completed', time: '5m ago' },
    { id: 'T-003', name: 'Room status query #712', status: 'completed', time: '8m ago' },
    { id: 'T-004', name: 'HVAC fault analysis', status: 'in_progress', time: '12m ago' },
    { id: 'T-005', name: 'Guest request routing', status: 'completed', time: '15m ago' },
  ]

  return (
    <div className="agent-detail-card card">
      <div className="card-header">
        <div className="agent-detail-title">
          <Bot size={14} className="text-accent" />
          <h3 style={{ color: 'var(--text-primary)', fontSize: '0.8rem' }}>{agent.codename || agent.name}</h3>
          <span className={`status-badge ${agent.status}`}>
            <span className={`status-dot ${agent.status}`} />
            {agent.status.toUpperCase()}
          </span>
        </div>
        <span className="font-mono text-xs text-muted">{agent.id}</span>
      </div>

      <div className="card-body">
        {/* Metrics Grid */}
        <div className="agent-metrics-grid">
          <div className="agent-metric-box">
            <div className="metric-icon"><Cpu size={14} /></div>
            <div className="metric-content">
              <div className="metric-label">CPU LOAD</div>
              <div className="metric-value font-mono">{agent.cpu}%</div>
              <div className="progress-bar"><div className="progress-bar-fill" style={{ width: `${agent.cpu}%` }} /></div>
            </div>
          </div>
          <div className="agent-metric-box">
            <div className="metric-icon"><MemoryStick size={14} /></div>
            <div className="metric-content">
              <div className="metric-label">MEMORY</div>
              <div className="metric-value font-mono">{agent.memory}%</div>
              <div className="progress-bar"><div className="progress-bar-fill" style={{ width: `${agent.memory}%` }} /></div>
            </div>
          </div>
          <div className="agent-metric-box">
            <div className="metric-icon"><CheckCircle size={14} /></div>
            <div className="metric-content">
              <div className="metric-label">TASKS DONE</div>
              <div className="metric-value font-mono">{agent.tasksCompleted.toLocaleString()}</div>
            </div>
          </div>
          <div className="agent-metric-box">
            <div className="metric-icon"><Clock size={14} /></div>
            <div className="metric-content">
              <div className="metric-label">UPTIME</div>
              <div className="metric-value font-mono">{agent.uptime}</div>
            </div>
          </div>
        </div>

        {/* Version & Type */}
        <div className="agent-info-row">
          <div className="agent-info-item">
            <span className="info-label">VERSION</span>
            <span className="info-value font-mono">{agent.version}</span>
          </div>
          <div className="agent-info-item">
            <span className="info-label">TYPE</span>
            <span className="info-value font-mono">{agent.type.toUpperCase()}</span>
          </div>
          <div className="agent-info-item">
            <span className="info-label">CHILDREN</span>
            <span className="info-value font-mono">{agent.children?.length || 0}</span>
          </div>
        </div>

        {/* Recent Tasks */}
        <div className="agent-tasks-section">
          <button className="agent-tasks-toggle" onClick={() => setShowTasks(!showTasks)}>
            <span className="uppercase text-xs" style={{ letterSpacing: '0.1em' }}>Recent Tasks</span>
            <ChevronRight size={12} className={showTasks ? 'rotated' : ''} />
          </button>
          {showTasks && (
            <div className="agent-tasks-list">
              {mockTasks.map(task => (
                <div key={task.id} className="agent-task-item">
                  <span className={`task-status-dot ${task.status === 'completed' ? 'positive' : 'active'}`} />
                  <span className="task-name font-mono">{task.name}</span>
                  <span className="task-time font-mono text-muted">{task.time}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ── Redesigned Topology SVG ── */
function AgentTopology({ onSelectAgent }) {
  const executive = AGENTS[0]

  // Layout constants — much more spacious
  const svgW = 900
  const svgH = 500
  const centerX = svgW / 2

  // Executive position
  const execY = 60

  // Domain agents — wide spread
  const domains = executive.children
  const domainY = 210
  const domainSpacing = svgW / (domains.length + 1)

  // Sub-agent row
  const subY = 370

  return (
    <div className="card topology-card">
      <div className="card-header">
        <h3>AGENT TOPOLOGY</h3>
        <span className="font-mono text-xs text-muted">LIVE NETWORK MAP</span>
      </div>
      <div className="topology-body">
        <svg viewBox={`0 0 ${svgW} ${svgH}`} className="topology-svg" preserveAspectRatio="xMidYMid meet">
          <defs>
            <filter id="nodeGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="lineGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" />
            </filter>
            {/* Animated pulse ring */}
            <radialGradient id="pulseGrad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#FF9900" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#FF9900" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* ── Background grid ── */}
          {Array.from({ length: Math.floor(svgW / 40) + 1 }).map((_, i) => (
            <line key={`gv${i}`} x1={i * 40} y1="0" x2={i * 40} y2={svgH}
              stroke="#141416" strokeWidth="0.5" />
          ))}
          {Array.from({ length: Math.floor(svgH / 40) + 1 }).map((_, i) => (
            <line key={`gh${i}`} x1="0" y1={i * 40} x2={svgW} y2={i * 40}
              stroke="#141416" strokeWidth="0.5" />
          ))}

          {/* ── Executive ("Brain") Node ── */}
          <g>
            {/* Pulse ring */}
            <circle cx={centerX} cy={execY} r="38" fill="url(#pulseGrad)">
              <animate attributeName="r" values="30;42;30" dur="3s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.6;0.15;0.6" dur="3s" repeatCount="indefinite" />
            </circle>
            {/* Outer ring */}
            <circle cx={centerX} cy={execY} r="30" fill="none" stroke="#FF9900" strokeWidth="2" opacity="0.7" />
            {/* Inner fill */}
            <circle cx={centerX} cy={execY} r="30" fill="rgba(255,153,0,0.06)" />
            {/* Core dot */}
            <circle cx={centerX} cy={execY} r="6" fill="#FF9900">
              <animate attributeName="r" values="5;7;5" dur="2s" repeatCount="indefinite" />
            </circle>
            {/* Label */}
            <text x={centerX} y={execY + 48} textAnchor="middle"
              fill="#FFB84D" fontSize="13" fontFamily="'JetBrains Mono', monospace" fontWeight="600" letterSpacing="1">
              NEXUS.AI
            </text>
            <text x={centerX} y={execY + 63} textAnchor="middle"
              fill="#5A5A63" fontSize="9" fontFamily="'JetBrains Mono', monospace" letterSpacing="2">
              EXECUTIVE BRAIN
            </text>
          </g>

          {/* ── Connection lines to domain agents ── */}
          {domains.map((agent, i) => {
            const dx = domainSpacing * (i + 1)
            const isActive = agent.status === 'active'

            return (
              <g key={`conn-${agent.id}`}>
                {/* Glow line behind */}
                {isActive && (
                  <line x1={centerX} y1={execY + 30} x2={dx} y2={domainY - 24}
                    stroke="#FF9900" strokeWidth="3" opacity="0.08" filter="url(#lineGlow)" />
                )}
                {/* Main line */}
                <line x1={centerX} y1={execY + 30} x2={dx} y2={domainY - 24}
                  stroke={isActive ? '#FF9900' : '#2A2A2E'} strokeWidth={isActive ? '1.5' : '0.8'}
                  opacity={isActive ? '0.45' : '0.3'}
                  strokeDasharray={isActive ? 'none' : '4 4'}
                >
                  {isActive && (
                    <animate attributeName="opacity" values="0.3;0.6;0.3" dur="4s" repeatCount="indefinite" />
                  )}
                </line>
                {/* Data packet flowing */}
                {isActive && (
                  <circle r="3" fill="#FF9900" opacity="0.9">
                    <animateMotion dur={`${2 + i * 0.5}s`} repeatCount="indefinite"
                      path={`M${centerX},${execY + 30} L${dx},${domainY - 24}`} />
                  </circle>
                )}
                {/* Junction dot at top */}
                <circle cx={centerX} cy={execY + 30} r="2" fill="#FF9900" opacity="0.5" />
              </g>
            )
          })}

          {/* ── Domain Agent Nodes ── */}
          {domains.map((agent, i) => {
            const dx = domainSpacing * (i + 1)
            const isActive = agent.status === 'active'
            const nodeW = 140
            const nodeH = 48

            return (
              <g key={agent.id}
                className="topology-node-group"
                onClick={() => onSelectAgent(agent)}
                style={{ cursor: 'pointer' }}
              >
                {/* Node box */}
                <rect x={dx - nodeW / 2} y={domainY - nodeH / 2} width={nodeW} height={nodeH} rx="6"
                  fill={isActive ? 'rgba(255,153,0,0.04)' : 'rgba(26,26,29,0.7)'}
                  stroke={isActive ? 'rgba(255,153,0,0.3)' : '#2A2A2E'} strokeWidth="1.5"
                />
                {/* Status dot */}
                <circle cx={dx - nodeW / 2 + 16} cy={domainY} r="5"
                  fill={isActive ? '#FF9900' : '#555560'} />
                {/* Active glow on dot */}
                {isActive && (
                  <circle cx={dx - nodeW / 2 + 16} cy={domainY} r="8"
                    fill="none" stroke="#FF9900" opacity="0.25">
                    <animate attributeName="r" values="6;10;6" dur="2s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.3;0.1;0.3" dur="2s" repeatCount="indefinite" />
                  </circle>
                )}
                {/* Agent name */}
                <text x={dx - nodeW / 2 + 28} y={domainY + 4}
                  fill={isActive ? '#F3F3F4' : '#5A5A63'} fontSize="12"
                  fontFamily="'JetBrains Mono', monospace" fontWeight="600">
                  {agent.codename.split('.')[0].toUpperCase()}
                </text>
                {/* Domain label below */}
                <text x={dx} y={domainY + nodeH / 2 + 16} textAnchor="middle"
                  fill="#5A5A63" fontSize="8" fontFamily="'JetBrains Mono', monospace" letterSpacing="1.5">
                  {agent.name.toUpperCase()}
                </text>

                {/* ── Sub-agent connections ── */}
                {agent.children?.map((sub, j) => {
                  const subCount = agent.children.length
                  const subSpread = Math.min(subCount * 55, nodeW + 40)
                  const startX = dx - subSpread / 2 + (subSpread / (subCount + 1)) * (j + 1)
                  const subActive = sub.status === 'active'

                  return (
                    <g key={sub.id}>
                      {/* Connection line */}
                      <line x1={dx} y1={domainY + nodeH / 2} x2={startX} y2={subY - 15}
                        stroke={subActive ? '#2A2A2E' : '#1A1A1D'} strokeWidth="0.8" />
                      {/* Sub-node */}
                      <rect x={startX - 28} y={subY - 15} width="56" height="30" rx="4"
                        fill={subActive ? 'rgba(180,196,177,0.04)' : '#111113'}
                        stroke={subActive ? 'rgba(180,196,177,0.15)' : '#1E1E22'} strokeWidth="1"
                      />
                      {/* Status dot */}
                      <circle cx={startX - 16} cy={subY} r="3"
                        fill={subActive ? '#B4C4B1' : '#555560'} />
                      {/* Name */}
                      <text x={startX - 8} y={subY + 3.5}
                        fill={subActive ? '#B0B0B8' : '#555560'} fontSize="7.5"
                        fontFamily="'JetBrains Mono', monospace" fontWeight="500">
                        {sub.codename ? sub.codename.split('.')[0].slice(0, 7).toUpperCase() : sub.name.slice(0, 7).toUpperCase()}
                      </text>
                      {/* Label below */}
                      <text x={startX} y={subY + 26} textAnchor="middle"
                        fill="#4A4A50" fontSize="6.5" fontFamily="'JetBrains Mono', monospace" letterSpacing="0.5">
                        {sub.name.toUpperCase().slice(0, 8)}
                      </text>
                    </g>
                  )
                })}
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}

export default function Agents() {
  const [selectedAgent, setSelectedAgent] = useState(null)
  const allAgents = flattenAgents(AGENTS)

  return (
    <div className="agents-page">
      <div className="agents-header">
        <div className="agents-title">
          <Bot size={18} className="text-accent" />
          <h1>AI AGENT MANAGEMENT</h1>
        </div>
        <div className="agents-summary font-mono text-xs text-muted">
          {allAgents.length} AGENTS • {allAgents.filter(a => a.status === 'active').length} ACTIVE
        </div>
      </div>

      {/* Topology — full width */}
      <AgentTopology onSelectAgent={setSelectedAgent} />

      {/* Agent List + Detail */}
      <div className="agents-bottom">
        <div className="card agents-list-card">
          <div className="card-header">
            <h3>ALL AGENTS</h3>
          </div>
          <div className="card-body agents-list-body">
            {allAgents.map(agent => (
              <div
                key={agent.id}
                className={`agent-list-item ${selectedAgent?.id === agent.id ? 'selected' : ''}`}
                style={{ paddingLeft: `${12 + agent.depth * 16}px` }}
                onClick={() => setSelectedAgent(agent)}
              >
                <span className={`status-dot ${agent.status}`} />
                <span className="agent-list-name font-mono">{agent.codename || agent.name}</span>
                <span className="agent-list-version font-mono text-xs text-muted">{agent.version}</span>
                <span className={`status-badge ${agent.status}`}>{agent.status.toUpperCase()}</span>
                <ChevronRight size={12} className="text-muted" />
              </div>
            ))}
          </div>
        </div>

        {/* Detail Panel */}
        {selectedAgent && (
          <AgentDetailCard agent={selectedAgent} />
        )}
      </div>
    </div>
  )
}
