import { useState, useEffect } from 'react'
import {
  BarChart3, TrendingUp, DollarSign, Users, BedDouble,
  Calendar, ArrowUpRight, ArrowDownRight
} from 'lucide-react'
import { REVENUE_DATA, ROOMS_DATA } from '../data/mockData'
import { fetchFinanceSummary, fetchGuests, fetchDashboard, fetchCostSummary } from '../services/api'
import './Analytics.css'

const GUEST_STATS = {
  totalGuests: 412,
  checkIns: 28,
  checkOuts: 15,
  vipGuests: 8,
  avgStay: 3.2,
  satisfactionScore: 4.7,
}

const KPI_CARDS = [
  { label: 'REVPAR', value: '$287.40', change: '+4.2%', trend: 'up', icon: DollarSign },
  { label: 'ADR', value: '$342.18', change: '+2.8%', trend: 'up', icon: TrendingUp },
  { label: 'OCCUPANCY', value: '94%', change: '+1.5%', trend: 'up', icon: BedDouble },
  { label: 'GOPPAR', value: '$198.50', change: '-0.3%', trend: 'down', icon: BarChart3 },
]

const DEPT_PERFORMANCE = [
  { dept: 'Front Desk', score: 97, target: 95 },
  { dept: 'Housekeeping', score: 94, target: 92 },
  { dept: 'F&B', score: 91, target: 90 },
  { dept: 'Concierge', score: 98, target: 95 },
  { dept: 'Maintenance', score: 89, target: 90 },
  { dept: 'Security', score: 96, target: 94 },
  { dept: 'Spa', score: 93, target: 91 },
]

function RevenueChart() {
  const max = Math.max(...REVENUE_DATA.map(d => d.revenue))

  return (
    <div className="card revenue-chart-card">
      <div className="card-header">
        <h3>Revenue Overview</h3>
        <div className="chart-period-toggle">
          <button className="btn btn-primary">12M</button>
          <button className="btn">6M</button>
          <button className="btn">3M</button>
        </div>
      </div>
      <div className="card-body revenue-chart-body">
        <div className="bar-chart">
          {REVENUE_DATA.map((d, i) => {
            const height = (d.revenue / max) * 100

            return (
              <div key={d.month} className="bar-col">
                <div className="bar-value font-mono text-xs text-muted">
                  ${(d.revenue / 1000000).toFixed(1)}M
                </div>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{
                      height: `${height}%`,
                      animationDelay: `${i * 60}ms`,
                    }}
                  />
                </div>
                <div className="bar-label font-mono text-xs text-muted">{d.month}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function RevPARTrend() {
  const data = REVENUE_DATA
  const min = Math.min(...data.map(d => d.revpar)) - 10
  const max = Math.max(...data.map(d => d.revpar)) + 10

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * 280 + 10
    const y = 100 - ((d.revpar - min) / (max - min)) * 80
    return { x, y, ...d }
  })

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const areaD = `${pathD} L ${points[points.length - 1].x} 100 L ${points[0].x} 100 Z`

  return (
    <div className="card revpar-card">
      <div className="card-header">
        <h3>RevPAR Trend</h3>
        <span className="font-mono text-accent text-sm">$287.40</span>
      </div>
      <div className="card-body revpar-body">
        <svg viewBox="0 0 300 110" className="revpar-svg" preserveAspectRatio="none">
          <defs>
            <linearGradient id="revparGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FF9900" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#FF9900" stopOpacity="0" />
            </linearGradient>
          </defs>
          {/* Grid lines */}
          {[20, 40, 60, 80].map(y => (
            <line key={y} x1="10" y1={y} x2="290" y2={y} stroke="#1A1A1D" strokeWidth="0.5" />
          ))}
          {/* Area */}
          <path d={areaD} fill="url(#revparGrad)" />
          {/* Line */}
          <path d={pathD} fill="none" stroke="#FF9900" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            style={{ filter: 'drop-shadow(0 0 4px rgba(255,153,0,0.4))' }}
          />
          {/* Dots */}
          {points.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r="3" fill="#0A0A0B" stroke="#FF9900" strokeWidth="1.5" />
          ))}
        </svg>
        <div className="revpar-labels font-mono text-xs text-muted">
          {data.map(d => (
            <span key={d.month}>{d.month}</span>
          ))}
        </div>
      </div>
    </div>
  )
}

function GuestAnalytics() {
  return (
    <div className="card guest-analytics-card">
      <div className="card-header">
        <h3>Guest Analytics</h3>
        <Users size={14} className="text-accent" />
      </div>
      <div className="card-body">
        <div className="guest-stats-grid">
          <div className="guest-stat">
            <span className="guest-stat-value font-mono">{GUEST_STATS.totalGuests}</span>
            <span className="guest-stat-label text-xs text-muted uppercase">Total Guests</span>
          </div>
          <div className="guest-stat">
            <span className="guest-stat-value font-mono" style={{ color: 'var(--status-positive)' }}>{GUEST_STATS.checkIns}</span>
            <span className="guest-stat-label text-xs text-muted uppercase">Check-ins Today</span>
          </div>
          <div className="guest-stat">
            <span className="guest-stat-value font-mono">{GUEST_STATS.checkOuts}</span>
            <span className="guest-stat-label text-xs text-muted uppercase">Check-outs Today</span>
          </div>
          <div className="guest-stat">
            <span className="guest-stat-value font-mono" style={{ color: 'var(--accent-primary-light)' }}>{GUEST_STATS.vipGuests}</span>
            <span className="guest-stat-label text-xs text-muted uppercase">VIP Guests</span>
          </div>
          <div className="guest-stat">
            <span className="guest-stat-value font-mono">{GUEST_STATS.avgStay}d</span>
            <span className="guest-stat-label text-xs text-muted uppercase">Avg Stay</span>
          </div>
          <div className="guest-stat">
            <span className="guest-stat-value font-mono" style={{ color: 'var(--status-positive)' }}>{GUEST_STATS.satisfactionScore}</span>
            <span className="guest-stat-label text-xs text-muted uppercase">Satisfaction</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function DeptPerformance() {
  return (
    <div className="card dept-card">
      <div className="card-header">
        <h3>Department Performance</h3>
        <span className="font-mono text-xs text-muted">VS TARGET</span>
      </div>
      <div className="card-body dept-body">
        {DEPT_PERFORMANCE.map(dept => {
          const isAbove = dept.score >= dept.target

          return (
            <div key={dept.dept} className="dept-row">
              <span className="dept-name font-mono">{dept.dept}</span>
              <div className="dept-bar-wrap">
                <div className="progress-bar" style={{ flex: 1 }}>
                  <div
                    className={`progress-bar-fill ${isAbove ? 'positive' : ''}`}
                    style={{ width: `${dept.score}%` }}
                  />
                </div>
                {/* Target marker */}
                <div className="dept-target-marker" style={{ left: `${dept.target}%` }} />
              </div>
              <span className={`dept-score font-mono ${isAbove ? '' : 'below-target'}`}>
                {dept.score}%
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function Analytics() {
  const [kpis, setKpis] = useState(KPI_CARDS)
  const [guestStats, setGuestStats] = useState(GUEST_STATS)

  useEffect(() => {
    // Fetch finance summary from backend
    fetchFinanceSummary('hotel-grandview')
      .then(data => {
        if (data?.total_revenue) {
          setKpis(prev => prev.map(k => {
            if (k.label === 'REVPAR') return { ...k, value: `$${(data.total_revenue / (data.total_rooms || 300) / 365).toFixed(2)}` }
            return k
          }))
        }
      })
      .catch(() => {})

    // Fetch real guests
    fetchGuests()
      .then(data => {
        if (data?.guests?.length) {
          const vip = data.guests.filter(g => g.vip || g.is_vip)
          setGuestStats(prev => ({
            ...prev,
            totalGuests: data.guests.length,
            vipGuests: vip.length,
          }))
        }
      })
      .catch(() => {})

    // Fetch cost summary
    fetchCostSummary()
      .then(data => {
        // We can overlay cost data if needed
      })
      .catch(() => {})
  }, [])

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div className="analytics-title">
          <BarChart3 size={18} className="text-accent" />
          <h1>ANALYTICS & INTELLIGENCE</h1>
        </div>
        <div className="analytics-date font-mono text-xs text-muted">
          <Calendar size={12} /> REPORT PERIOD: OCT 2023
        </div>
      </div>

      {/* KPI Row */}
      <div className="kpi-row">
        {kpis.map(kpi => (
          <div key={kpi.label} className="card kpi-card">
            <div className="kpi-icon-wrap">
              <kpi.icon size={16} />
            </div>
            <div className="kpi-content">
              <div className="kpi-label text-xs text-muted uppercase">{kpi.label}</div>
              <div className="kpi-value font-mono">{kpi.value}</div>
              <div className={`kpi-change font-mono text-xs ${kpi.trend}`}>
                {kpi.trend === 'up' ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                {kpi.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="analytics-charts-row">
        <RevenueChart />
        <RevPARTrend />
      </div>

      {/* Bottom Row */}
      <div className="analytics-bottom-row">
        <GuestAnalytics />
        <DeptPerformance />
      </div>
    </div>
  )
}
