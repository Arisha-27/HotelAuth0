import { useState, useEffect, useCallback } from 'react'
import {
  Cpu, Wrench, Users, ShieldAlert, Globe, Zap, Brain, Bug,
  AlertTriangle, CheckCircle, TrendingUp, TrendingDown, Activity,
  BarChart3, Heart, Star, DollarSign, ThermometerSun, GitBranch,
  RotateCcw, ChevronRight, Eye
} from 'lucide-react'
import {
  initializeAdvancedFeatures, fetchAdvancedDashboard,
  fetchMaintenancePredictions, analyzeMaintenace, fetchMaintenanceSummary,
  fetchGuestProfiles, analyzeGuests, fetchGuestPersonalizationStats,
  scanForFraud, fetchFraudAlerts, fetchFraudStats,
  fetchChainOverview, broadcastCrossHotelAlert, fetchCrossHotelEvents,
  fetchFullOptimization,
  generateExplainabilityDemos, fetchExplainabilityEntries,
  runChaosTest, runAllChaosTests, fetchChaosResults,
} from '../services/api'
import './Advanced.css'

/* ═══════════════════════════════════════════
   TAB: Predictive Maintenance (Step 91)
   ═══════════════════════════════════════════ */
function MaintenanceTab() {
  const [predictions, setPredictions] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)

  const analyze = async () => {
    setLoading(true)
    try {
      const data = await analyzeMaintenace('hotel-downtown')
      setPredictions(data?.predictions || [])
      setSummary(data?.summary || null)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  useEffect(() => {
    fetchMaintenancePredictions().then(d => setPredictions(d?.predictions || []))
    fetchMaintenanceSummary().then(setSummary)
  }, [])

  return (
    <div>
      <div className="section-header">
        <h3 className="font-mono" style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Wrench size={14} />PREDICTIVE MAINTENANCE ENGINE
        </h3>
        <button className="btn-init" onClick={analyze} disabled={loading}>
          {loading ? '⏳ ANALYZING...' : '🔍 ANALYZE IoT DEVICES'}
        </button>
      </div>

      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 12 }}>
          <div className="adv-stat card">
            <div className="adv-stat-label"><Activity size={9} />DEVICES</div>
            <div className="adv-stat-val font-mono">{summary.total_devices_analyzed || 0}</div>
          </div>
          <div className="adv-stat card">
            <div className="adv-stat-label"><AlertTriangle size={9} />PREDICTIONS</div>
            <div className="adv-stat-val font-mono" style={{ color: '#FF9900' }}>{summary.predictions_generated || 0}</div>
          </div>
          <div className="adv-stat card">
            <div className="adv-stat-label"><Wrench size={9} />URGENT</div>
            <div className="adv-stat-val font-mono" style={{ color: '#E53935' }}>{summary.devices_requiring_immediate_attention || 0}</div>
          </div>
          <div className="adv-stat card">
            <div className="adv-stat-label"><DollarSign size={9} />EST. COST</div>
            <div className="adv-stat-val font-mono" style={{ fontSize: '1rem' }}>${(summary.total_estimated_cost || 0).toLocaleString()}</div>
          </div>
        </div>
      )}

      <div className="pred-grid">
        {predictions.length === 0 ? (
          <div className="empty-state-adv">Click "ANALYZE IoT DEVICES" to run predictive maintenance</div>
        ) : predictions.map(pred => (
          <div key={pred.prediction_id} className="pred-card card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="font-mono" style={{ fontSize: '0.65rem', color: 'var(--text-primary)' }}>
                {pred.device_type?.toUpperCase()}
              </span>
              <span className={`risk-badge ${pred.priority}`}>{pred.priority?.toUpperCase()}</span>
            </div>
            <span className="font-mono" style={{ fontSize: '0.55rem', color: 'var(--text-muted)' }}>{pred.device_id}</span>
            <span style={{ fontSize: '0.55rem', color: 'var(--text-secondary)' }}>{pred.location}</span>
            <div className="pred-bar-track">
              <div className={`pred-bar-fill ${pred.priority}`} style={{ width: `${pred.failure_probability * 100}%` }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.5rem', color: 'var(--text-muted)' }}>
              <span>Fail: {(pred.failure_probability * 100).toFixed(0)}%</span>
              <span>{pred.days_until_failure}d remaining</span>
              <span>Conf: {(pred.confidence * 100).toFixed(0)}%</span>
            </div>
            {pred.degradation_indicators?.slice(0, 2).map((ind, i) => (
              <div key={i} className="font-mono" style={{ fontSize: '0.48rem', color: '#FFB84D' }}>⚠ {ind}</div>
            ))}
            <div className="font-mono" style={{ fontSize: '0.5rem', color: '#66BB6A', marginTop: 2 }}>→ {pred.recommended_action}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   TAB: Guest Personalization (Step 92)
   ═══════════════════════════════════════════ */
function GuestTab() {
  const [profiles, setProfiles] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  const analyze = async () => {
    setLoading(true)
    try {
      const data = await analyzeGuests('hotel-downtown')
      setProfiles(data?.profiles || [])
      setStats(data?.stats || null)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  useEffect(() => {
    fetchGuestProfiles().then(d => setProfiles(d?.profiles || []))
    fetchGuestPersonalizationStats().then(setStats)
  }, [])

  return (
    <div>
      <div className="section-header">
        <h3 className="font-mono" style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Users size={14} />GUEST PERSONALIZATION AI
        </h3>
        <button className="btn-init" onClick={analyze} disabled={loading}>
          {loading ? '⏳ ANALYZING...' : '🧠 ANALYZE GUESTS'}
        </button>
      </div>

      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8, marginBottom: 12 }}>
          {['platinum', 'gold', 'silver', 'standard'].map(tier => (
            <div key={tier} className="adv-stat card">
              <div className="adv-stat-label"><Star size={9} />{tier.toUpperCase()}</div>
              <div className="adv-stat-val font-mono">{stats.by_tier?.[tier] || 0}</div>
            </div>
          ))}
          <div className="adv-stat card">
            <div className="adv-stat-label"><Heart size={9} />AVG SATISFACTION</div>
            <div className="adv-stat-val font-mono" style={{ color: '#66BB6A' }}>{stats.avg_satisfaction || '--'}</div>
          </div>
        </div>
      )}

      <div className="guest-grid">
        {profiles.length === 0 ? (
          <div className="empty-state-adv">Click "ANALYZE GUESTS" to generate personalization profiles</div>
        ) : profiles.map(p => (
          <div key={p.guest_id} className="guest-card card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-primary)' }}>{p.name}</span>
              <span className={`tier-badge ${p.loyalty_tier}`}>{p.loyalty_tier?.toUpperCase()}</span>
            </div>
            <div style={{ fontSize: '0.55rem', color: 'var(--text-muted)', display: 'flex', gap: 10 }}>
              <span>⭐ {p.satisfaction_score}/5.0</span>
              <span>🏨 {p.stay_history?.[0]?.stays || 0} stays</span>
              <span>💰 ${(p.stay_history?.[0]?.total_spend || 0).toLocaleString()}</span>
            </div>
            <div style={{ fontSize: '0.5rem', color: 'var(--text-muted)', display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              <span>🌡 {p.preferences?.room_temperature}°C</span>
              <span>🛏 {p.preferences?.pillow_type}</span>
              <span>🏔 {p.preferences?.floor_preference} floor</span>
              <span>👁 {p.preferences?.view_preference} view</span>
            </div>
            {p.personalization_recommendations?.slice(0, 3).map((rec, i) => (
              <div key={i} className="font-mono" style={{ fontSize: '0.48rem', color: rec.priority === 'critical' ? '#E53935' : rec.priority === 'high' ? '#FFB84D' : '#66BB6A' }}>
                → [{rec.type}] {rec.action}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   TAB: Fraud Detection (Step 93)
   ═══════════════════════════════════════════ */
function FraudTab() {
  const [alerts, setAlerts] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  const scan = async () => {
    setLoading(true)
    try {
      const data = await scanForFraud('hotel-downtown')
      // Combine all alert types
      const all = [...(data?.transaction_alerts || []), ...(data?.access_alerts || []), ...(data?.demo_alerts || [])]
      setAlerts(all)
      setStats(data?.stats || null)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  useEffect(() => {
    fetchFraudAlerts().then(d => setAlerts(d?.alerts || []))
    fetchFraudStats().then(setStats)
  }, [])

  return (
    <div>
      <div className="section-header">
        <h3 className="font-mono" style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: 6 }}>
          <ShieldAlert size={14} />FRAUD DETECTION MODULE
        </h3>
        <button className="btn-init" onClick={scan} disabled={loading}>
          {loading ? '⏳ SCANNING...' : '🔎 SCAN TRANSACTIONS'}
        </button>
      </div>

      {stats && stats.total_alerts > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 12 }}>
          <div className="adv-stat card">
            <div className="adv-stat-label">TOTAL</div>
            <div className="adv-stat-val font-mono">{stats.total_alerts}</div>
          </div>
          <div className="adv-stat card">
            <div className="adv-stat-label">FLAGGED $</div>
            <div className="adv-stat-val font-mono" style={{ color: '#E53935', fontSize: '1rem' }}>${stats.total_flagged_amount?.toLocaleString()}</div>
          </div>
          <div className="adv-stat card">
            <div className="adv-stat-label">AUTO-BLOCKED</div>
            <div className="adv-stat-val font-mono" style={{ color: '#FF9900' }}>{stats.auto_blocked}</div>
          </div>
          <div className="adv-stat card">
            <div className="adv-stat-label">CRITICAL</div>
            <div className="adv-stat-val font-mono" style={{ color: '#E53935' }}>{stats.by_risk?.critical || 0}</div>
          </div>
        </div>
      )}

      <div className="fraud-list">
        {alerts.length === 0 ? (
          <div className="empty-state-adv">Click "SCAN TRANSACTIONS" to run fraud detection</div>
        ) : alerts.map(a => (
          <div key={a.alert_id} className="fraud-item card">
            <span className={`risk-badge ${a.risk_level}`}>{a.risk_level?.toUpperCase()}</span>
            <span className="font-mono" style={{ fontSize: '0.55rem', color: 'var(--text-muted)' }}>{a.category?.replace(/_/g, ' ').toUpperCase()}</span>
            <div>
              <div className="font-mono" style={{ fontSize: '0.6rem', color: 'var(--text-primary)' }}>{a.description}</div>
              <div style={{ display: 'flex', gap: 6, marginTop: 3 }}>
                {a.indicators?.slice(0, 2).map((ind, i) => (
                  <span key={i} className="font-mono" style={{ fontSize: '0.48rem', color: '#FFB84D' }}>⚠ {ind}</span>
                ))}
              </div>
              <div className="font-mono" style={{ fontSize: '0.48rem', color: '#66BB6A', marginTop: 2 }}>→ {a.recommended_action}</div>
            </div>
            {a.amount > 0 && (
              <span className="font-mono" style={{ fontSize: '0.7rem', color: '#E53935', fontWeight: 700 }}>
                ${a.amount?.toLocaleString()}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   TAB: Cross-Hotel (Step 94)
   ═══════════════════════════════════════════ */
function CrossHotelTab() {
  const [overview, setOverview] = useState(null)
  const [events, setEvents] = useState([])

  useEffect(() => {
    fetchChainOverview().then(d => { setOverview(d); setEvents(d?.recent_events || []) })
  }, [])

  const broadcast = async () => {
    await broadcastCrossHotelAlert('hotel-downtown', 'Security advisory: Elevated threat level — all properties on alert', 'high')
    fetchChainOverview().then(d => { setOverview(d); setEvents(d?.recent_events || []) })
  }

  return (
    <div>
      <div className="section-header">
        <h3 className="font-mono" style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Globe size={14} />CROSS-HOTEL COORDINATION
        </h3>
        <button className="btn-init" onClick={broadcast}>📡 BROADCAST ALERT</button>
      </div>

      {overview?.hotels && (
        <div className="hotel-chain-grid" style={{ marginBottom: 12 }}>
          {Object.entries(overview.hotels).map(([id, hotel]) => (
            <div key={id} className="hotel-chain-card card">
              <div className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-primary)', marginBottom: 4 }}>{hotel.name}</div>
              <div className="hotel-occupancy font-mono" style={{ color: hotel.occupancy > 0.9 ? '#E53935' : hotel.occupancy > 0.8 ? '#FF9900' : '#66BB6A' }}>
                {(hotel.occupancy * 100).toFixed(0)}%
              </div>
              <div style={{ fontSize: '0.5rem', color: 'var(--text-muted)' }}>
                {hotel.rooms} rooms • {hotel.city}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="card" style={{ padding: 14 }}>
        <div className="card-header"><h3>COORDINATION EVENTS</h3><span className="font-mono text-xs text-muted">{events.length} events</span></div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 250, overflowY: 'auto' }}>
          {events.map(evt => (
            <div key={evt.event_id} style={{ display: 'flex', gap: 8, padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.03)', fontSize: '0.58rem' }}>
              <span className="font-mono" style={{ color: '#B388FF', minWidth: 80 }}>{evt.event_type?.toUpperCase()}</span>
              <span style={{ color: 'var(--text-secondary)', flex: 1 }}>{evt.description}</span>
              <span className="font-mono" style={{ color: 'var(--text-muted)' }}>{new Date(evt.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
          {events.length === 0 && <div className="empty-state-adv">No coordination events yet</div>}
        </div>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   TAB: Resource Optimization (Step 95)
   ═══════════════════════════════════════════ */
function OptimizationTab() {
  const [data, setData] = useState(null)

  useEffect(() => { fetchFullOptimization().then(setData) }, [])

  if (!data) return <div className="empty-state-adv">Loading optimization data...</div>

  const staffing = data.staffing?.staffing || {}
  const energy = data.energy || {}
  const pricing = data.pricing || {}

  return (
    <div>
      <div className="section-header">
        <h3 className="font-mono" style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: 6 }}>
          <TrendingUp size={14} />RESOURCE OPTIMIZATION
        </h3>
      </div>

      <div className="opt-grid">
        {/* Staffing */}
        <div className="opt-section card">
          <h4 className="font-mono" style={{ fontSize: '0.6rem', color: '#B388FF', marginBottom: 8 }}>👥 STAFFING</h4>
          {Object.entries(staffing).map(([role, info]) => (
            <div key={role} className="opt-row">
              <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>{role.replace(/_/g, ' ')}</span>
              <span className="font-mono">
                <span style={{ color: 'var(--text-muted)' }}>{info.current}</span>
                <span style={{ color: '#B388FF' }}> → {info.recommended}</span>
              </span>
            </div>
          ))}
          <div style={{ marginTop: 8, fontSize: '0.55rem', color: '#66BB6A', fontWeight: 600 }}>
            Daily savings: ${data.staffing?.daily_labor_savings?.toLocaleString()}
          </div>
        </div>

        {/* Energy */}
        <div className="opt-section card">
          <h4 className="font-mono" style={{ fontSize: '0.6rem', color: '#66BB6A', marginBottom: 8 }}>⚡ ENERGY</h4>
          {Object.entries(energy.zones || {}).map(([zone, info]) => (
            <div key={zone} className="opt-row">
              <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>{zone.replace(/_/g, ' ')}</span>
              <span className="font-mono">
                <span style={{ color: 'var(--text-muted)' }}>{info.current_kwh}</span>
                <span style={{ color: '#66BB6A' }}> → {info.optimized_kwh} kWh</span>
              </span>
            </div>
          ))}
          <div style={{ marginTop: 8, fontSize: '0.55rem', color: '#66BB6A', fontWeight: 600 }}>
            Savings: {energy.savings_percent}% • ${energy.estimated_monthly_savings_usd?.toFixed(0)}/mo
          </div>
        </div>

        {/* Pricing */}
        <div className="opt-section card">
          <h4 className="font-mono" style={{ fontSize: '0.6rem', color: '#FFB84D', marginBottom: 8 }}>💰 DYNAMIC PRICING</h4>
          <div className="opt-row"><span>Base Rate</span><span className="font-mono">${pricing.base_rate}</span></div>
          <div className="opt-row"><span>Optimized Rate</span><span className="font-mono" style={{ color: '#FFB84D' }}>${pricing.optimized_rate}</span></div>
          <div className="opt-row"><span>Demand Multiplier</span><span className="font-mono">{pricing.demand_multiplier}x</span></div>
          <div className="opt-row"><span>Occupancy</span><span className="font-mono">{(pricing.current_occupancy * 100).toFixed(0)}%</span></div>
          <div style={{ marginTop: 8, fontSize: '0.55rem', color: pricing.revenue_impact > 0 ? '#66BB6A' : '#E53935', fontWeight: 600 }}>
            Revenue impact: {pricing.revenue_impact > 0 ? '+' : ''}${pricing.revenue_impact?.toLocaleString()}
          </div>
          <div className="font-mono" style={{ fontSize: '0.48rem', color: 'var(--text-muted)', marginTop: 4 }}>
            Competitors: ${pricing.competitor_rates?.min}–${pricing.competitor_rates?.max} (avg ${pricing.competitor_rates?.avg})
          </div>
        </div>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   TAB: AI Explainability (Step 96)
   ═══════════════════════════════════════════ */
function ExplainabilityTab() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    setLoading(true)
    try {
      await generateExplainabilityDemos()
      const data = await fetchExplainabilityEntries()
      setEntries(data?.entries || [])
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  useEffect(() => {
    fetchExplainabilityEntries().then(d => setEntries(d?.entries || []))
  }, [])

  return (
    <div>
      <div className="section-header">
        <h3 className="font-mono" style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Brain size={14} />AI EXPLAINABILITY PANEL
        </h3>
        <button className="btn-init" onClick={generate} disabled={loading}>
          {loading ? '⏳ GENERATING...' : '🧠 GENERATE EXPLANATIONS'}
        </button>
      </div>

      <div className="explain-list">
        {entries.length === 0 ? (
          <div className="empty-state-adv">Click "GENERATE EXPLANATIONS" to see AI reasoning chains</div>
        ) : entries.map(entry => (
          <div key={entry.entry_id} className="explain-card card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span className="font-mono" style={{ fontSize: '0.65rem', color: '#B388FF' }}>{entry.agent_id?.toUpperCase()}</span>
                <span className="font-mono" style={{ fontSize: '0.55rem', color: 'var(--text-muted)', marginLeft: 10 }}>{entry.action}</span>
              </div>
              <span className="font-mono" style={{ fontSize: '0.55rem', color: '#66BB6A' }}>
                Confidence: {(entry.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="font-mono" style={{ fontSize: '0.65rem', color: 'var(--text-primary)', padding: '4px 0' }}>
               Decision: {entry.decision}
            </div>

            {/* Reasoning Chain */}
            <div className="explain-chain">
              <div className="font-mono" style={{ fontSize: '0.5rem', color: 'var(--text-muted)', marginBottom: 4, letterSpacing: '0.08em' }}>REASONING CHAIN</div>
              {entry.reasoning_chain?.map((step, i) => (
                <div key={i} className="explain-step">
                  <span className="explain-step-num">{i + 1}.</span>
                  <span>{step}</span>
                </div>
              ))}
            </div>

            {/* Inputs */}
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {entry.inputs_used?.map((inp, i) => (
                <span key={i} className="font-mono" style={{ fontSize: '0.45rem', padding: '1px 6px', borderRadius: 3, background: 'rgba(179,136,255,0.1)', color: '#B388FF' }}>
                  {inp}
                </span>
              ))}
            </div>

            {/* Alternatives */}
            {entry.alternatives_considered?.length > 0 && (
              <div>
                <div className="font-mono" style={{ fontSize: '0.48rem', color: 'var(--text-muted)', marginBottom: 2 }}>ALTERNATIVES CONSIDERED</div>
                {entry.alternatives_considered.map((alt, i) => (
                  <div key={i} className="explain-alt">
                    <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>{alt.option}</span>
                    <span className="font-mono" style={{ color: 'var(--text-muted)', marginLeft: 8 }}>— {alt.reason}</span>
                    <span className="font-mono" style={{ color: '#FFB84D', marginLeft: 8 }}>Score: {(alt.score * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            )}

            {/* Risk */}
            {entry.risk_assessment && (
              <div className="font-mono" style={{ fontSize: '0.48rem', color: entry.risk_assessment.startsWith('CRITICAL') ? '#E53935' : entry.risk_assessment.startsWith('HIGH') ? '#FF9900' : '#66BB6A', marginTop: 2 }}>
                ⚡ Risk: {entry.risk_assessment}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   TAB: Chaos Testing (Step 97)
   ═══════════════════════════════════════════ */
const CHAOS_SCENARIOS = [
  { id: 'network_partition', name: 'Network Partition', icon: Globe },
  { id: 'database_failure', name: 'Database Failure', icon: Activity },
  { id: 'iot_mass_offline', name: 'IoT Mass Offline', icon: Zap },
  { id: 'agent_crash', name: 'Agent Crash', icon: Bug },
  { id: 'auth_service_down', name: 'Auth Service Down', icon: ShieldAlert },
  { id: 'high_load', name: 'High Load', icon: TrendingUp },
  { id: 'data_corruption', name: 'Data Corruption', icon: AlertTriangle },
  { id: 'cascading_failure', name: 'Cascading Failure', icon: GitBranch },
]

function ChaosTab() {
  const [results, setResults] = useState({})
  const [running, setRunning] = useState(null)
  const [allRunning, setAllRunning] = useState(false)
  const [summary, setSummary] = useState(null)

  const runSingle = async (id) => {
    setRunning(id)
    try {
      const r = await runChaosTest(id)
      setResults(prev => ({ ...prev, [id]: r }))
    } catch (e) { setResults(prev => ({ ...prev, [id]: { system_survived: false, error: e.message } })) }
    setRunning(null)
  }

  const runAll = async () => {
    setAllRunning(true)
    try {
      const data = await runAllChaosTests()
      const mapped = {}
      data.results?.forEach(r => { mapped[r.scenario] = r })
      setResults(mapped)
      setSummary(data.summary)
    } catch (e) { console.error(e) }
    setAllRunning(false)
  }

  return (
    <div>
      <div className="section-header">
        <h3 className="font-mono" style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Bug size={14} />CHAOS TESTING MODE
        </h3>
        <button className="btn-init" onClick={runAll} disabled={allRunning}>
          {allRunning ? '⏳ TESTING...' : '💥 RUN ALL CHAOS TESTS'}
        </button>
      </div>

      <div className="chaos-grid">
        {CHAOS_SCENARIOS.map(sc => {
          const r = results[sc.id]
          const isRunning = running === sc.id || allRunning
          const resilience = r?.resilience_score || 0
          const color = resilience >= 80 ? '#66BB6A' : resilience >= 60 ? '#FFB84D' : '#E53935'
          return (
            <div key={sc.id} className="chaos-card card" onClick={() => !isRunning && runSingle(sc.id)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <sc.icon size={14} style={{ color: r ? color : 'var(--text-muted)' }} />
                {r ? (
                  <span className={`risk-badge ${r.system_survived ? 'low' : 'critical'}`}>
                    {r.system_survived ? 'SURVIVED' : 'FAILED'}
                  </span>
                ) : (
                  <span className="risk-badge clear">{isRunning ? '...' : 'READY'}</span>
                )}
              </div>
              <span className="font-mono" style={{ fontSize: '0.6rem', fontWeight: 600, color: 'var(--text-primary)' }}>{sc.name}</span>
              {r && (
                <>
                  <div className="resilience-bar">
                    <div className="resilience-fill" style={{ width: `${resilience}%`, background: color }} />
                  </div>
                  <div className="font-mono" style={{ fontSize: '0.48rem', color: 'var(--text-muted)' }}>
                    Resilience: {resilience} • {r.degradation_level} • {r.recovery_time_ms}ms recovery
                  </div>
                </>
              )}
            </div>
          )
        })}
      </div>

      {/* Summary */}
      {summary && (
        <div className="card" style={{ marginTop: 12, padding: 14 }}>
          <div className="card-header">
            <h3>RESILIENCE REPORT</h3>
            <span className="font-mono" style={{ fontSize: '0.65rem', color: summary.avg_resilience_score >= 70 ? '#66BB6A' : '#FF9900' }}>
              AVG RESILIENCE: {summary.avg_resilience_score}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginTop: 10 }}>
            <div className="adv-stat card" style={{ textAlign: 'center' }}><div className="adv-stat-val font-mono" style={{ color: '#66BB6A' }}>{summary.survived}</div><div className="adv-stat-sub">SURVIVED</div></div>
            <div className="adv-stat card" style={{ textAlign: 'center' }}><div className="adv-stat-val font-mono">{summary.total_tests}</div><div className="adv-stat-sub">TOTAL</div></div>
            <div className="adv-stat card" style={{ textAlign: 'center' }}><div className="adv-stat-val font-mono" style={{ color: summary.data_integrity_maintained ? '#66BB6A' : '#E53935' }}>{summary.data_integrity_maintained ? '✓' : '✗'}</div><div className="adv-stat-sub">DATA INTEGRITY</div></div>
            <div className="adv-stat card" style={{ textAlign: 'center' }}><div className="adv-stat-val font-mono" style={{ color: '#B388FF' }}>{summary.avg_resilience_score}</div><div className="adv-stat-sub">RESILIENCE</div></div>
          </div>

          {/* Detailed results */}
          <div style={{ marginTop: 12 }}>
            {Object.entries(results).map(([scenario, r]) => (
              <div key={scenario} style={{ padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.58rem', marginBottom: 3 }}>
                  <span className="font-mono" style={{ color: 'var(--text-primary)' }}>{scenario.replace(/_/g, ' ').toUpperCase()}</span>
                  <span className="font-mono" style={{ color: r.resilience_score >= 80 ? '#66BB6A' : r.resilience_score >= 60 ? '#FFB84D' : '#E53935' }}>
                    Score: {r.resilience_score}
                  </span>
                </div>
                {r.failure_points?.map((fp, i) => (
                  <div key={i} className="font-mono" style={{ fontSize: '0.48rem', color: '#FFB84D' }}>⚠ {fp}</div>
                ))}
                {r.recommendations?.map((rec, i) => (
                  <div key={i} className="font-mono" style={{ fontSize: '0.48rem', color: '#66BB6A' }}>→ {rec}</div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════ */
export default function Advanced() {
  const [tab, setTab] = useState('maintenance')
  const [initializing, setInitializing] = useState(false)

  const initAll = async () => {
    setInitializing(true)
    try {
      await initializeAdvancedFeatures('hotel-downtown')
      window.location.reload()
    } catch (e) { console.error(e) }
    setInitializing(false)
  }

  const tabs = [
    { id: 'maintenance', label: '🔧 MAINTENANCE', icon: Wrench },
    { id: 'guests', label: '👤 GUEST AI', icon: Users },
    { id: 'fraud', label: '🛡️ FRAUD', icon: ShieldAlert },
    { id: 'cross-hotel', label: '🌐 MULTI-HOTEL', icon: Globe },
    { id: 'optimization', label: '📈 OPTIMIZATION', icon: TrendingUp },
    { id: 'explainability', label: '🧠 EXPLAIN AI', icon: Brain },
    { id: 'chaos', label: '💥 CHAOS TEST', icon: Bug },
  ]

  return (
    <div className="adv-page">
      {/* Header */}
      <div className="adv-header">
        <div className="adv-title">
          <Cpu size={18} style={{ color: '#B388FF' }} />
          <h1>ADVANCED INTELLIGENCE</h1>
          <span className="adv-badge">PHASE 8</span>
        </div>
        <button className="btn-init" onClick={initAll} disabled={initializing}>
          {initializing ? '⏳ INITIALIZING...' : '🚀 INITIALIZE ALL FEATURES'}
        </button>
      </div>

      {/* Tabs */}
      <div className="adv-tabs">
        {tabs.map(t => (
          <button key={t.id} className={`adv-tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {tab === 'maintenance' && <MaintenanceTab />}
      {tab === 'guests' && <GuestTab />}
      {tab === 'fraud' && <FraudTab />}
      {tab === 'cross-hotel' && <CrossHotelTab />}
      {tab === 'optimization' && <OptimizationTab />}
      {tab === 'explainability' && <ExplainabilityTab />}
      {tab === 'chaos' && <ChaosTab />}
    </div>
  )
}
