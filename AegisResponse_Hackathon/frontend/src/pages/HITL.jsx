import { useState, useEffect, useCallback } from 'react'
import {
  Shield, AlertTriangle, CheckCircle, XCircle, Clock, Zap,
  Lock, Unlock, Eye, Play, RotateCcw, ChevronRight, Activity,
  FileWarning, Bug, Fingerprint, Hash, Send
} from 'lucide-react'
import {
  interceptAction, fetchHITLPendingApprovals, decideApproval, escalateApproval,
  fetchApprovalHistory, fetchApprovalStats, fetchConsentLog, verifyConsentIntegrity,
  fetchAnomalyAlerts, acknowledgeAnomaly, runAttackSimulation, runAllSimulations,
  fetchSimulationResults, fetchHITLDashboard,
} from '../services/api'
import './HITL.css'

const SCENARIOS = [
  { id: 'brute_force', name: 'Brute Force', desc: 'Test auth failure detection', icon: Lock },
  { id: 'privilege_escalation', name: 'Priv. Escalation', desc: 'Sub-agent scope bypass', icon: Unlock },
  { id: 'data_exfiltration', name: 'Data Exfil', desc: 'Bulk data extraction attempt', icon: Eye },
  { id: 'rapid_fire_requests', name: 'DDoS Sim', desc: 'Request flood detection', icon: Zap },
  { id: 'social_engineering', name: 'Social Eng.', desc: 'Agent manipulation test', icon: Bug },
  { id: 'token_replay', name: 'Token Replay', desc: 'Stolen token validation', icon: Fingerprint },
  { id: 'agent_manipulation', name: 'Rogue Agent', desc: 'Agent control bypass', icon: Activity },
  { id: 'off_hours_access', name: 'Off-Hours', desc: 'Late-night access check', icon: Clock },
]

const TEST_ACTIONS = [
  { value: 'unlock_door', label: 'Unlock Door', criticality: 'medium' },
  { value: 'unlock_floor', label: 'Unlock Floor', criticality: 'high' },
  { value: 'unlock_all_doors', label: 'Unlock All Doors', criticality: 'critical' },
  { value: 'fire_protocol', label: 'Fire Protocol', criticality: 'high' },
  { value: 'lockdown', label: 'Full Lockdown', criticality: 'critical' },
  { value: 'refund', label: 'Refund ($500+)', criticality: 'high' },
  { value: 'charge_override', label: 'Charge Override', criticality: 'critical' },
  { value: 'delete_guest', label: 'Delete Guest Data', criticality: 'critical' },
  { value: 'export_guest_data', label: 'Export Guest Data', criticality: 'high' },
  { value: 'power_cutoff', label: 'Power Cutoff', criticality: 'critical' },
]

/* ═══════════════════════════════════════════
   TAB: Approvals
   ═══════════════════════════════════════════ */
function ApprovalsTab() {
  const [pending, setPending] = useState([])
  const [history, setHistory] = useState([])
  const [testAction, setTestAction] = useState('unlock_door')
  const [testDesc, setTestDesc] = useState('Emergency unlock request — Room 712')
  const [interceptResult, setInterceptResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [pend, hist] = await Promise.all([
        fetchHITLPendingApprovals(), fetchApprovalHistory(20),
      ])
      setPending(pend?.pending || [])
      setHistory(hist?.history || [])
    } catch (e) { console.error(e) }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const handleIntercept = async () => {
    setLoading(true)
    try {
      const result = await interceptAction({
        action_type: testAction,
        description: testDesc,
        hotel_id: 'hotel-grandview',
        agent_id: 'dashboard_user',
        amount: testAction === 'refund' ? 750 : null,
      })
      setInterceptResult(result)
      await refresh()
    } catch (e) { setInterceptResult({ error: e.message }) }
    setLoading(false)
  }

  const handleDecide = async (approvalId, approved) => {
    try {
      await decideApproval(approvalId, {
        approved,
        approver: 'admin_dashboard',
        approver_role: 'admin',
        reason: approved ? null : 'Denied via dashboard',
      })
      await refresh()
    } catch (e) { console.error(e) }
  }

  return (
    <div className="hitl-section">
      {/* Test Action Trigger */}
      <div className="card" style={{ marginBottom: 12 }}>
        <div className="card-header">
          <h3><Send size={12} style={{ marginRight: 6 }} />TEST ACTION INTERCEPT</h3>
        </div>
        <div className="test-action-form">
          <div className="test-field">
            <label>Action Type</label>
            <select value={testAction} onChange={e => setTestAction(e.target.value)}>
              {TEST_ACTIONS.map(a => (
                <option key={a.value} value={a.value}>{a.label} ({a.criticality})</option>
              ))}
            </select>
          </div>
          <div className="test-field">
            <label>Description</label>
            <input value={testDesc} onChange={e => setTestDesc(e.target.value)} placeholder="Action description..." />
          </div>
          <button className="btn-run-all" onClick={handleIntercept} disabled={loading} style={{ alignSelf: 'end' }}>
            {loading ? 'PROCESSING...' : '⚡ INTERCEPT'}
          </button>
        </div>
        {interceptResult && (
          <div style={{ padding: '8px 16px 12px', fontSize: '0.6rem' }}>
            <span className="font-mono" style={{ color: interceptResult.intercepted ? '#FF9900' : '#66BB6A' }}>
              {interceptResult.intercepted
                ? `🔒 INTERCEPTED — ${interceptResult.criticality?.toUpperCase()} — ID: ${interceptResult.approval_id || 'N/A'}`
                : interceptResult.error || '✅ Action allowed (no approval needed)'}
            </span>
          </div>
        )}
      </div>

      {/* Pending Approvals */}
      <div className="card" style={{ marginBottom: 12 }}>
        <div className="card-header">
          <h3><Clock size={12} style={{ marginRight: 6 }} />PENDING APPROVALS</h3>
          <span className="font-mono text-xs" style={{ color: pending.length > 0 ? '#FF9900' : 'var(--text-muted)' }}>
            {pending.length}
          </span>
        </div>
        <div className="card-body">
          {pending.length === 0 ? (
            <div className="empty-state">No pending approvals</div>
          ) : (
            <div className="approval-list">
              {pending.map(item => (
                <div key={item.approval_id} className="approval-item">
                  <span className={`crit-badge ${item.criticality}`}>{item.criticality?.toUpperCase()}</span>
                  <div className="approval-info">
                    <span className="approval-action-name font-mono">{item.action_type?.replace(/_/g, ' ').toUpperCase()}</span>
                    <span className="approval-desc">{item.action_description}</span>
                    <div className="approval-meta font-mono">
                      <span>ID: {item.approval_id}</span>
                      <span>By: {item.requested_by}</span>
                      <span>{item.requires_step_up ? '🔐 Step-up required' : ''}</span>
                    </div>
                  </div>
                  <div className="approval-meta font-mono" style={{ flexDirection: 'column', textAlign: 'right' }}>
                    <span>{item.category?.toUpperCase()}</span>
                    <span>{item.hotel_id}</span>
                    {item.sms_sent && <span style={{ color: '#66BB6A' }}>📱 SMS Sent</span>}
                  </div>
                  <div className="approval-actions">
                    <button className="btn-approve" onClick={() => handleDecide(item.approval_id, true)}>
                      <CheckCircle size={10} /> APPROVE
                    </button>
                    <button className="btn-deny" onClick={() => handleDecide(item.approval_id, false)}>
                      <XCircle size={10} /> DENY
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Decision History */}
      <div className="card">
        <div className="card-header">
          <h3><FileWarning size={12} style={{ marginRight: 6 }} />DECISION HISTORY</h3>
          <span className="font-mono text-xs text-muted">{history.length} entries</span>
        </div>
        <div className="card-body">
          <div className="approval-list">
            {history.map(item => (
              <div key={item.approval_id} className="approval-item" style={{ opacity: 0.8 }}>
                <span className={`crit-badge ${item.criticality}`}>{item.criticality?.toUpperCase()}</span>
                <div className="approval-info">
                  <span className="approval-action-name font-mono">{item.action_type?.replace(/_/g, ' ').toUpperCase()}</span>
                  <span className="approval-desc">{item.action_description}</span>
                </div>
                <div className="approval-meta font-mono" style={{ flexDirection: 'column' }}>
                  <span>By: {item.approver || '—'}</span>
                  <span>{item.approver_role || ''}</span>
                </div>
                <span className={`crit-badge ${item.status === 'approved' ? 'low' : 'critical'}`}>
                  {item.status === 'approved' ? '✅' : '❌'} {item.status?.toUpperCase()}
                </span>
              </div>
            ))}
            {history.length === 0 && <div className="empty-state">No decisions yet — intercept an action above</div>}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   TAB: Attack Simulation
   ═══════════════════════════════════════════ */
function AttackSimTab() {
  const [results, setResults] = useState({})
  const [running, setRunning] = useState(null)
  const [allRunning, setAllRunning] = useState(false)
  const [summary, setSummary] = useState(null)

  const runSingle = async (scenarioId) => {
    setRunning(scenarioId)
    try {
      const result = await runAttackSimulation(scenarioId)
      setResults(prev => ({ ...prev, [scenarioId]: result }))
    } catch (e) {
      setResults(prev => ({ ...prev, [scenarioId]: { success: false, error: e.message } }))
    }
    setRunning(null)
  }

  const runAll = async () => {
    setAllRunning(true)
    try {
      const data = await runAllSimulations()
      const mapped = {}
      data.results?.forEach(r => { mapped[r.scenario] = r })
      setResults(mapped)
      setSummary(data.summary)
    } catch (e) { console.error(e) }
    setAllRunning(false)
  }

  return (
    <div className="hitl-section">
      <div className="hitl-section-header">
        <h3 className="font-mono" style={{ fontSize: '0.7rem', letterSpacing: '0.1em' }}>
          <Bug size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
          ATTACK SIMULATION SUITE
        </h3>
        <button className="btn-run-all" onClick={runAll} disabled={allRunning}>
          {allRunning ? '⏳ RUNNING ALL...' : '🚀 RUN ALL SCENARIOS'}
        </button>
      </div>

      <div className="sim-grid">
        {SCENARIOS.map(sc => {
          const result = results[sc.id]
          const isRunning = running === sc.id || allRunning
          return (
            <div
              key={sc.id}
              className="sim-scenario-card card"
              onClick={() => !isRunning && runSingle(sc.id)}
              style={{ cursor: isRunning ? 'wait' : 'pointer' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <sc.icon size={14} style={{ color: result?.success === false ? '#E53935' : result?.success ? '#66BB6A' : 'var(--text-muted)' }} />
                {result ? (
                  <span className={`sim-result-badge ${result.success ? 'pass' : 'fail'}`}>
                    {result.success ? 'PASS' : 'FAIL'}
                  </span>
                ) : (
                  <span className="sim-result-badge pending">{isRunning ? '...' : 'READY'}</span>
                )}
              </div>
              <span className="sim-scenario-name">{sc.name}</span>
              <span className="sim-scenario-desc">{sc.desc}</span>
              {result && (
                <div className="font-mono" style={{ fontSize: '0.5rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  {result.alerts_triggered || 0} alerts • {result.steps_executed || 0} steps • {result.duration_ms || 0}ms
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Summary */}
      {summary && (
        <div className="card" style={{ marginTop: 12 }}>
          <div className="card-header">
            <h3>SECURITY REPORT</h3>
            <span className="font-mono text-xs" style={{ color: summary.pass_rate === '100.0%' ? '#66BB6A' : '#FF9900' }}>
              {summary.pass_rate} PASS RATE
            </span>
          </div>
          <div className="sim-summary">
            <div className="sim-summary-item card">
              <div className="sim-summary-value font-mono" style={{ color: '#66BB6A' }}>{summary.passed}</div>
              <div className="sim-summary-label">PASSED</div>
            </div>
            <div className="sim-summary-item card">
              <div className="sim-summary-value font-mono" style={{ color: '#E53935' }}>{summary.failed}</div>
              <div className="sim-summary-label">FAILED</div>
            </div>
            <div className="sim-summary-item card">
              <div className="sim-summary-value font-mono">{summary.total_simulations}</div>
              <div className="sim-summary-label">TOTAL</div>
            </div>
            <div className="sim-summary-item card">
              <div className="sim-summary-value font-mono" style={{ color: '#FFB84D' }}>{summary.total_alerts_triggered}</div>
              <div className="sim-summary-label">ALERTS</div>
            </div>
          </div>
        </div>
      )}

      {/* Detailed results */}
      {Object.keys(results).length > 0 && (
        <div className="card" style={{ marginTop: 12 }}>
          <div className="card-header">
            <h3>DETAILED RESULTS</h3>
          </div>
          <div className="card-body">
            {Object.entries(results).map(([scenario, r]) => (
              <div key={scenario} style={{ marginBottom: 8, padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span className="font-mono" style={{ fontSize: '0.65rem', color: 'var(--text-primary)' }}>
                    {scenario.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  <span className={`sim-result-badge ${r.success ? 'pass' : 'fail'}`}>{r.success ? 'PASS' : 'FAIL'}</span>
                </div>
                {r.defenses_activated?.length > 0 && (
                  <div className="font-mono" style={{ fontSize: '0.5rem', color: '#66BB6A', marginBottom: 2 }}>
                    Defenses: {r.defenses_activated.join(', ')}
                  </div>
                )}
                {r.vulnerabilities_found?.length > 0 && (
                  <div className="font-mono" style={{ fontSize: '0.5rem', color: '#E53935', marginBottom: 2 }}>
                    Vulnerabilities: {r.vulnerabilities_found.join(', ')}
                  </div>
                )}
                {r.recommendations?.map((rec, i) => (
                  <div key={i} className="font-mono" style={{ fontSize: '0.5rem', color: 'var(--text-muted)' }}>
                    → {rec}
                  </div>
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
   TAB: Anomaly Detection
   ═══════════════════════════════════════════ */
function AnomalyTab() {
  const [alerts, setAlerts] = useState([])
  const [stats, setStats] = useState(null)

  const refresh = async () => {
    try {
      const data = await fetchAnomalyAlerts(50)
      setAlerts(data?.alerts || [])
      setStats(data?.stats || null)
    } catch (e) { console.error(e) }
  }

  useEffect(() => { refresh() }, [])

  const handleAck = async (alertId) => {
    await acknowledgeAnomaly(alertId)
    refresh()
  }

  return (
    <div className="hitl-section">
      {stats && (
        <div className="hitl-stats-row" style={{ marginBottom: 12 }}>
          <div className="hitl-stat card">
            <div className="hitl-stat-header"><AlertTriangle size={10} />TOTAL</div>
            <div className="hitl-stat-value font-mono">{stats.total_alerts}</div>
          </div>
          <div className="hitl-stat card">
            <div className="hitl-stat-header"><Eye size={10} />UNACKNOWLEDGED</div>
            <div className="hitl-stat-value font-mono" style={{ color: '#FF9900' }}>{stats.unacknowledged}</div>
          </div>
          <div className="hitl-stat card">
            <div className="hitl-stat-header"><Shield size={10} />AUTO-MITIGATED</div>
            <div className="hitl-stat-value font-mono" style={{ color: '#66BB6A' }}>{stats.auto_mitigated}</div>
          </div>
          <div className="hitl-stat card">
            <div className="hitl-stat-header"><Zap size={10} />CRITICAL</div>
            <div className="hitl-stat-value font-mono" style={{ color: '#E53935' }}>{stats.by_threat_level?.critical || 0}</div>
          </div>
          <div className="hitl-stat card">
            <div className="hitl-stat-header"><Activity size={10} />HIGH</div>
            <div className="hitl-stat-value font-mono" style={{ color: '#FF9900' }}>{stats.by_threat_level?.high || 0}</div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h3><AlertTriangle size={12} style={{ marginRight: 6 }} />ANOMALY ALERTS</h3>
          <button className="btn-ghost font-mono text-xs" onClick={refresh} style={{ padding: '2px 8px', cursor: 'pointer', background: 'none', border: 'none', color: 'var(--accent-primary-light)' }}>
            <RotateCcw size={10} /> REFRESH
          </button>
        </div>
        <div className="card-body">
          {alerts.length === 0 ? (
            <div className="empty-state">No anomalies detected — run attack simulations to generate alerts</div>
          ) : (
            <div className="anomaly-list">
              {alerts.map(alert => (
                <div key={alert.alert_id} className={`anomaly-item ${alert.threat_level}-level`}>
                  <span className={`crit-badge ${alert.threat_level}`}>{alert.threat_level?.toUpperCase()}</span>
                  <span className="font-mono" style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>
                    {alert.anomaly_type?.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  <div>
                    <div className="font-mono" style={{ fontSize: '0.6rem', color: 'var(--text-primary)' }}>{alert.description?.slice(0, 100)}</div>
                    <div className="font-mono" style={{ fontSize: '0.5rem', color: 'var(--text-muted)', marginTop: 2 }}>
                      Source: {alert.source} • {alert.auto_mitigated ? '✅ Auto-mitigated' : '⏳ Pending'}
                    </div>
                  </div>
                  <span className="font-mono" style={{ fontSize: '0.5rem', color: 'var(--text-muted)' }}>
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                  {!alert.acknowledged ? (
                    <button className="btn-approve" style={{ fontSize: '0.5rem', padding: '2px 8px' }} onClick={() => handleAck(alert.alert_id)}>
                      ACK
                    </button>
                  ) : (
                    <span className="font-mono" style={{ fontSize: '0.5rem', color: '#66BB6A' }}>✓</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   TAB: Consent Log
   ═══════════════════════════════════════════ */
function ConsentLogTab() {
  const [entries, setEntries] = useState([])
  const [integrity, setIntegrity] = useState(null)

  useEffect(() => {
    fetchConsentLog(100).then(data => setEntries(data?.entries || [])).catch(() => {})
    verifyConsentIntegrity().then(data => setIntegrity(data)).catch(() => {})
  }, [])

  return (
    <div className="hitl-section">
      {/* Integrity status */}
      <div className="card" style={{ marginBottom: 12 }}>
        <div className="card-header">
          <h3><Hash size={12} style={{ marginRight: 6 }} />CHAIN INTEGRITY</h3>
          {integrity && (
            <span className={`integrity-badge ${integrity.valid ? 'valid' : 'invalid'}`}>
              {integrity.valid ? '✅ CHAIN INTACT' : '⚠️ INTEGRITY VIOLATION'}
              <span className="font-mono" style={{ marginLeft: 8, fontSize: '0.5rem', opacity: 0.7 }}>
                {integrity.entries_checked} entries verified
              </span>
            </span>
          )}
        </div>
      </div>

      {/* Entries */}
      <div className="card">
        <div className="card-header">
          <h3>CONSENT & AUDIT LOG</h3>
          <span className="font-mono text-xs text-muted">{entries.length} entries</span>
        </div>
        <div className="card-body">
          {entries.length === 0 ? (
            <div className="empty-state">No consent entries yet — perform actions to generate audit trail</div>
          ) : (
            <div className="consent-entries">
              <div className="consent-entry" style={{ fontWeight: 600, color: 'var(--text-muted)', borderBottom: '1px solid var(--border-subtle)' }}>
                <span>TIMESTAMP</span>
                <span>TYPE</span>
                <span>DESCRIPTION</span>
                <span>HASH</span>
              </div>
              {entries.map(entry => (
                <div key={entry.entry_id} className="consent-entry">
                  <span className="font-mono" style={{ color: 'var(--text-muted)', fontSize: '0.55rem' }}>
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="font-mono" style={{ color: '#FFB84D', fontSize: '0.55rem' }}>
                    {entry.action_type?.toUpperCase()}
                  </span>
                  <span className="font-mono" style={{ fontSize: '0.55rem', color: 'var(--text-secondary)' }}>
                    {entry.action_description?.slice(0, 80)}
                    {entry.actor && <span style={{ color: 'var(--text-muted)' }}> — by {entry.actor}</span>}
                  </span>
                  <span className="consent-hash font-mono">{entry.entry_hash?.slice(0, 12)}...</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════ */
export default function HITL() {
  const [tab, setTab] = useState('approvals')
  const [dashData, setDashData] = useState(null)

  useEffect(() => {
    fetchHITLDashboard().then(setDashData).catch(() => {})
  }, [])

  const stats = dashData || {}
  const approvalStats = stats.approvals || {}
  const anomalyStats = stats.anomaly_detection || {}
  const simStats = stats.attack_simulations || {}
  const consentStats = stats.consent_log || {}

  return (
    <div className="hitl-page">
      {/* Header */}
      <div className="hitl-header">
        <div className="hitl-title">
          <Shield size={18} className="text-accent" />
          <h1>HUMAN-IN-THE-LOOP COMMAND</h1>
          <span className="hitl-badge">PHASE 6</span>
        </div>
      </div>

      {/* Stats Row */}
      <div className="hitl-stats-row">
        <div className="hitl-stat card">
          <div className="hitl-stat-header"><Clock size={10} />PENDING</div>
          <div className="hitl-stat-value font-mono" style={{ color: '#FF9900' }}>
            {approvalStats.pending || 0}
          </div>
          <div className="hitl-stat-sub font-mono">approval requests</div>
        </div>
        <div className="hitl-stat card">
          <div className="hitl-stat-header"><CheckCircle size={10} />APPROVED</div>
          <div className="hitl-stat-value font-mono" style={{ color: '#66BB6A' }}>
            {approvalStats.approved || 0}
          </div>
          <div className="hitl-stat-sub font-mono">decisions</div>
        </div>
        <div className="hitl-stat card">
          <div className="hitl-stat-header"><XCircle size={10} />DENIED</div>
          <div className="hitl-stat-value font-mono" style={{ color: '#E53935' }}>
            {approvalStats.denied || 0}
          </div>
          <div className="hitl-stat-sub font-mono">decisions</div>
        </div>
        <div className="hitl-stat card">
          <div className="hitl-stat-header"><AlertTriangle size={10} />ANOMALIES</div>
          <div className="hitl-stat-value font-mono" style={{ color: '#FFB84D' }}>
            {anomalyStats.total_alerts || 0}
          </div>
          <div className="hitl-stat-sub font-mono">detected</div>
        </div>
        <div className="hitl-stat card">
          <div className="hitl-stat-header"><Hash size={10} />CONSENT LOG</div>
          <div className="hitl-stat-value font-mono">
            {consentStats.total_entries || 0}
          </div>
          <div className="hitl-stat-sub font-mono">audit entries</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="hitl-tabs">
        <button className={`hitl-tab ${tab === 'approvals' ? 'active' : ''}`} onClick={() => setTab('approvals')}>
          ⚡ APPROVALS
        </button>
        <button className={`hitl-tab ${tab === 'attack-sim' ? 'active' : ''}`} onClick={() => setTab('attack-sim')}>
          🎯 ATTACK SIM
        </button>
        <button className={`hitl-tab ${tab === 'anomalies' ? 'active' : ''}`} onClick={() => setTab('anomalies')}>
          🚨 ANOMALIES
        </button>
        <button className={`hitl-tab ${tab === 'consent' ? 'active' : ''}`} onClick={() => setTab('consent')}>
          📋 CONSENT LOG
        </button>
      </div>

      {/* Tab Content */}
      {tab === 'approvals' && <ApprovalsTab />}
      {tab === 'attack-sim' && <AttackSimTab />}
      {tab === 'anomalies' && <AnomalyTab />}
      {tab === 'consent' && <ConsentLogTab />}
    </div>
  )
}
