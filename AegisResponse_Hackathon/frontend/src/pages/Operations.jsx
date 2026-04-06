import { useState, useEffect } from 'react'
import {
  Activity, Wrench, Sparkles, Thermometer, Zap,
  Clock, CheckCircle2, AlertCircle, ArrowRight, Users
} from 'lucide-react'
import { HOUSEKEEPING_TASKS, FLOOR_DATA, ROOMS_DATA } from '../data/mockData'
import { fetchRooms, fetchDashboard, fetchIncidents, fetchIoTSummary } from '../services/api'
import './Operations.css'

const WORK_ORDERS = [
  { id: 'WO-8821', room: '612', issue: 'HVAC compressor fault', priority: 'critical', status: 'in_progress', assignee: 'Tech #M-401', created: '22:46', eta: '45 min' },
  { id: 'WO-8820', room: '305', issue: 'Bathroom faucet leak', priority: 'medium', status: 'pending', assignee: 'Tech #M-205', created: '21:30', eta: '2h' },
  { id: 'WO-8819', room: '801', issue: 'Suite prep — VIP arrival', priority: 'high', status: 'in_progress', assignee: 'Team Alpha', created: '20:15', eta: '30 min' },
  { id: 'WO-8818', room: '509', issue: 'TV remote replacement', priority: 'low', status: 'completed', assignee: 'Tech #M-112', created: '19:45', eta: 'Done' },
  { id: 'WO-8817', room: '411', issue: 'Window seal inspection', priority: 'medium', status: 'completed', assignee: 'Tech #M-302', created: '18:20', eta: 'Done' },
  { id: 'WO-8816', room: 'Lobby', issue: 'Chandelier bulb replacement', priority: 'low', status: 'pending', assignee: 'Tech #M-112', created: '17:00', eta: '3h' },
]

const ENERGY_ZONES = [
  { zone: 'Guest Rooms', usage: 78, trend: 'stable' },
  { zone: 'Common Areas', usage: 45, trend: 'down' },
  { zone: 'Kitchen/Restaurant', usage: 92, trend: 'up' },
  { zone: 'HVAC System', usage: 85, trend: 'stable' },
  { zone: 'Lighting', usage: 34, trend: 'down' },
  { zone: 'Pool/Spa', usage: 61, trend: 'stable' },
]

function WorkOrderCard({ order }) {
  const priorityColors = {
    critical: { border: 'var(--status-critical)', bg: 'var(--status-critical-dim)' },
    high: { border: 'var(--accent-primary)', bg: 'var(--accent-primary-faint)' },
    medium: { border: 'var(--text-muted)', bg: 'transparent' },
    low: { border: 'var(--border-default)', bg: 'transparent' },
  }
  const p = priorityColors[order.priority]

  return (
    <div className="work-order-item" style={{ borderLeftColor: p.border, background: p.bg }}>
      <div className="wo-header">
        <span className="wo-id font-mono">{order.id}</span>
        <span className={`status-badge ${order.status === 'completed' ? 'positive' : order.status === 'in_progress' ? 'active' : 'idle'}`}>
          {order.status === 'in_progress' ? 'IN PROGRESS' : order.status.toUpperCase()}
        </span>
      </div>
      <div className="wo-issue font-mono">{order.issue}</div>
      <div className="wo-details">
        <span className="font-mono text-xs text-muted">Room {order.room}</span>
        <span className="font-mono text-xs text-muted">{order.assignee}</span>
        <span className="font-mono text-xs text-muted">ETA: {order.eta}</span>
      </div>
    </div>
  )
}

function HousekeepingTable() {
  return (
    <div className="card hk-card">
      <div className="card-header">
        <h3>Housekeeping Queue</h3>
        <span className="font-mono text-xs text-muted">{HOUSEKEEPING_TASKS.length} TASKS</span>
      </div>
      <div className="card-body hk-body">
        <table className="hk-table">
          <thead>
            <tr>
              <th className="font-mono">ID</th>
              <th className="font-mono">ROOM</th>
              <th className="font-mono">TASK</th>
              <th className="font-mono">ASSIGNEE</th>
              <th className="font-mono">STATUS</th>
              <th className="font-mono">PRIORITY</th>
            </tr>
          </thead>
          <tbody>
            {HOUSEKEEPING_TASKS.map(task => (
              <tr key={task.id}>
                <td className="font-mono text-muted">{task.id}</td>
                <td className="font-mono">{task.room}</td>
                <td className="font-mono">{task.task}</td>
                <td className="font-mono text-muted">{task.assignee}</td>
                <td>
                  <span className={`status-badge ${task.status === 'completed' ? 'positive' : task.status === 'in_progress' ? 'active' : 'idle'}`}>
                    {task.status === 'in_progress' ? 'IN PROGRESS' : task.status.toUpperCase()}
                  </span>
                </td>
                <td>
                  <span className={`priority-tag ${task.priority}`}>{task.priority.toUpperCase()}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function EnergyMonitor() {
  return (
    <div className="card energy-card">
      <div className="card-header">
        <h3>Energy Consumption</h3>
        <Zap size={14} className="text-accent" />
      </div>
      <div className="card-body energy-body">
        {ENERGY_ZONES.map(zone => (
          <div key={zone.zone} className="energy-zone-row">
            <span className="energy-zone-name font-mono">{zone.zone}</span>
            <div className="energy-bar-wrap">
              <div className="progress-bar" style={{ flex: 1 }}>
                <div
                  className={`progress-bar-fill ${zone.usage > 85 ? '' : 'positive'}`}
                  style={{ width: `${zone.usage}%` }}
                />
              </div>
              <span className="energy-value font-mono">{zone.usage}%</span>
            </div>
            <span className={`energy-trend font-mono text-xs ${zone.trend === 'up' ? 'trend-up' : zone.trend === 'down' ? 'trend-down' : ''}`}>
              {zone.trend === 'up' ? '↑' : zone.trend === 'down' ? '↓' : '—'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function FloorOverview() {
  return (
    <div className="card floor-overview-card">
      <div className="card-header">
        <h3>Floor-by-Floor Overview</h3>
        <span className="font-mono text-xs text-muted">{FLOOR_DATA.length} FLOORS</span>
      </div>
      <div className="card-body floor-overview-body">
        {FLOOR_DATA.map(floor => (
          <div key={floor.floor} className="floor-row">
            <span className="floor-num font-mono">F{String(floor.floor).padStart(2, '0')}</span>
            <div className="floor-occupancy-bar">
              <div className="progress-bar" style={{ flex: 1, height: '6px' }}>
                <div className="progress-bar-fill" style={{ width: `${(floor.occupied / floor.totalRooms) * 100}%` }} />
              </div>
            </div>
            <span className="floor-occ-text font-mono text-xs">{floor.occupied}/{floor.totalRooms}</span>
            <span className="floor-temp font-mono text-xs text-muted">
              <Thermometer size={10} /> {floor.temperature}°C
            </span>
            <span className="floor-energy font-mono text-xs text-muted">
              <Zap size={10} /> {floor.energyUsage}%
            </span>
            {floor.maintenance > 0 && (
              <span className="floor-maint font-mono text-xs" style={{ color: 'var(--status-critical)' }}>
                <Wrench size={10} /> {floor.maintenance}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Operations() {
  const [roomStats, setRoomStats] = useState(ROOMS_DATA)
  const [liveWorkOrders, setLiveWorkOrders] = useState(WORK_ORDERS)

  useEffect(() => {
    // Fetch live dashboard stats
    fetchDashboard('hotel-grandview')
      .then(data => {
        if (data?.rooms) {
          setRoomStats({
            totalRooms: data.rooms.total || ROOMS_DATA.totalRooms,
            occupied: data.rooms.occupied || ROOMS_DATA.occupied,
            available: data.rooms.available || ROOMS_DATA.available,
            maintenance: data.rooms.maintenance || ROOMS_DATA.maintenance,
            cleaning: data.rooms.cleaning || ROOMS_DATA.cleaning,
            occupancyRate: data.rooms.total ? Math.round((data.rooms.occupied / data.rooms.total) * 100) : ROOMS_DATA.occupancyRate,
          })
        }
      })
      .catch(() => {})

    // Fetch incidents as work orders
    fetchIncidents('hotel-grandview')
      .then(data => {
        if (data?.incidents?.length) {
          const liveOrders = data.incidents.slice(0, 6).map((inc, i) => ({
            id: inc.incident_id || `WO-LIVE-${i}`,
            room: inc.location || 'N/A',
            issue: inc.description || inc.type || 'Issue reported',
            priority: inc.severity || 'medium',
            status: inc.status || 'pending',
            assignee: inc.assigned_to || 'Unassigned',
            created: new Date(inc.created_at || Date.now()).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
            eta: inc.eta || 'TBD',
          }))
          setLiveWorkOrders([...liveOrders, ...WORK_ORDERS.slice(liveOrders.length)])
        }
      })
      .catch(() => {})
  }, [])

  return (
    <div className="operations-page">
      <div className="ops-header">
        <div className="ops-title">
          <Activity size={18} className="text-accent" />
          <h1>OPERATIONS CENTER</h1>
        </div>
        <div className="ops-stats font-mono text-xs">
          <div className="ops-stat-item">
            <Users size={12} />
            <span>{roomStats.occupied} OCCUPIED</span>
          </div>
          <div className="ops-stat-item">
            <Wrench size={12} />
            <span>{roomStats.maintenance} MAINTENANCE</span>
          </div>
          <div className="ops-stat-item">
            <Sparkles size={12} />
            <span>{roomStats.cleaning} CLEANING</span>
          </div>
        </div>
      </div>

      {/* Room Overview Stats */}
      <div className="ops-stat-cards">
        <div className="card ops-big-stat">
          <div className="big-stat-value font-mono">{roomStats.occupied}</div>
          <div className="big-stat-label uppercase text-xs text-muted">Occupied Rooms</div>
          <div className="progress-bar" style={{ marginTop: 8 }}>
            <div className="progress-bar-fill" style={{ width: `${roomStats.occupancyRate}%` }} />
          </div>
        </div>
        <div className="card ops-big-stat">
          <div className="big-stat-value font-mono" style={{ color: 'var(--status-positive)' }}>{roomStats.available}</div>
          <div className="big-stat-label uppercase text-xs text-muted">Available</div>
        </div>
        <div className="card ops-big-stat">
          <div className="big-stat-value font-mono" style={{ color: 'var(--status-critical)' }}>{roomStats.maintenance}</div>
          <div className="big-stat-label uppercase text-xs text-muted">Maintenance</div>
        </div>
        <div className="card ops-big-stat">
          <div className="big-stat-value font-mono" style={{ color: '#4A90D9' }}>{roomStats.cleaning}</div>
          <div className="big-stat-label uppercase text-xs text-muted">Cleaning</div>
        </div>
      </div>

      {/* Work Orders + Energy */}
      <div className="ops-main-row">
        <div className="card wo-card">
          <div className="card-header">
            <h3>Work Orders</h3>
            <span className="font-mono text-xs text-muted">{WORK_ORDERS.filter(o => o.status !== 'completed').length} ACTIVE</span>
          </div>
          <div className="card-body wo-body">
            {WORK_ORDERS.map(order => (
              <WorkOrderCard key={order.id} order={order} />
            ))}
          </div>
        </div>

        <div className="ops-side-col">
          <EnergyMonitor />
          <FloorOverview />
        </div>
      </div>

      {/* Housekeeping */}
      <HousekeepingTable />
    </div>
  )
}
