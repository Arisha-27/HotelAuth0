import { useState } from 'react'
import {
  Settings as SettingsIcon, User, Bell, Shield, Palette,
  Database, Globe, Key, Monitor, Save, RotateCcw, ToggleLeft, ToggleRight
} from 'lucide-react'
import './Settings.css'

function Toggle({ checked, onChange, label }) {
  return (
    <button className={`toggle-switch ${checked ? 'on' : ''}`} onClick={() => onChange(!checked)}>
      {checked ? <ToggleRight size={20} /> : <ToggleLeft size={20} />}
    </button>
  )
}

function SettingSection({ icon: Icon, title, description, children }) {
  return (
    <div className="card setting-section">
      <div className="card-header">
        <div className="setting-section-title">
          <Icon size={14} className="text-accent" />
          <h3>{title}</h3>
        </div>
        {description && <span className="text-xs text-muted">{description}</span>}
      </div>
      <div className="card-body setting-section-body">
        {children}
      </div>
    </div>
  )
}

function SettingRow({ label, description, children }) {
  return (
    <div className="setting-row">
      <div className="setting-row-info">
        <span className="setting-row-label">{label}</span>
        {description && <span className="setting-row-desc text-xs text-muted">{description}</span>}
      </div>
      <div className="setting-row-control">
        {children}
      </div>
    </div>
  )
}

export default function Settings() {
  const [settings, setSettings] = useState({
    darkMode: true,
    accentColor: '#FF9900',
    animations: true,
    soundAlerts: false,
    desktopNotifications: true,
    criticalAlerts: true,
    agentUpdates: false,
    maintenanceAlerts: true,
    twoFactor: true,
    sessionTimeout: '30',
    auditLog: true,
    ipWhitelist: false,
    autoRefresh: true,
    refreshInterval: '5',
    dataRetention: '90',
    timezone: 'UTC',
    language: 'en',
    dateFormat: 'DD/MM/YYYY',
  })

  const update = (key, value) => setSettings(prev => ({ ...prev, [key]: value }))

  return (
    <div className="settings-page">
      <div className="settings-header">
        <div className="settings-title">
          <SettingsIcon size={18} className="text-accent" />
          <h1>SYSTEM CONFIGURATION</h1>
        </div>
        <div className="settings-actions">
          <button className="btn">
            <RotateCcw size={12} /> RESET DEFAULTS
          </button>
          <button className="btn btn-primary">
            <Save size={12} /> SAVE CHANGES
          </button>
        </div>
      </div>

      <div className="settings-grid">
        {/* Appearance */}
        <SettingSection icon={Palette} title="APPEARANCE" description="Visual preferences">
          <SettingRow label="Dark Mode" description="Industrial obsidian theme">
            <Toggle checked={settings.darkMode} onChange={v => update('darkMode', v)} />
          </SettingRow>
          <SettingRow label="Accent Color" description="Primary UI accent">
            <div className="color-picker-row">
              {['#FF9900', '#E53935', '#4CAF50', '#2196F3', '#9C27B0', '#00BCD4'].map(color => (
                <button
                  key={color}
                  className={`color-swatch ${settings.accentColor === color ? 'active' : ''}`}
                  style={{ background: color }}
                  onClick={() => update('accentColor', color)}
                />
              ))}
            </div>
          </SettingRow>
          <SettingRow label="Animations" description="UI micro-animations and transitions">
            <Toggle checked={settings.animations} onChange={v => update('animations', v)} />
          </SettingRow>
          <SettingRow label="Sound Alerts" description="Audible notifications for critical events">
            <Toggle checked={settings.soundAlerts} onChange={v => update('soundAlerts', v)} />
          </SettingRow>
        </SettingSection>

        {/* Notifications */}
        <SettingSection icon={Bell} title="NOTIFICATIONS" description="Alert preferences">
          <SettingRow label="Desktop Notifications" description="Push notifications to browser">
            <Toggle checked={settings.desktopNotifications} onChange={v => update('desktopNotifications', v)} />
          </SettingRow>
          <SettingRow label="Critical Alerts" description="Immediate alerts for emergencies">
            <Toggle checked={settings.criticalAlerts} onChange={v => update('criticalAlerts', v)} />
          </SettingRow>
          <SettingRow label="Agent Status Updates" description="Notify when agent status changes">
            <Toggle checked={settings.agentUpdates} onChange={v => update('agentUpdates', v)} />
          </SettingRow>
          <SettingRow label="Maintenance Alerts" description="Work order and equipment alerts">
            <Toggle checked={settings.maintenanceAlerts} onChange={v => update('maintenanceAlerts', v)} />
          </SettingRow>
        </SettingSection>

        {/* Security */}
        <SettingSection icon={Shield} title="SECURITY" description="Access and authentication">
          <SettingRow label="Two-Factor Authentication" description="Require 2FA for login">
            <Toggle checked={settings.twoFactor} onChange={v => update('twoFactor', v)} />
          </SettingRow>
          <SettingRow label="Session Timeout" description="Auto-logout after inactivity (minutes)">
            <select
              className="input setting-select font-mono"
              value={settings.sessionTimeout}
              onChange={e => update('sessionTimeout', e.target.value)}
            >
              <option value="15">15 min</option>
              <option value="30">30 min</option>
              <option value="60">60 min</option>
              <option value="120">120 min</option>
            </select>
          </SettingRow>
          <SettingRow label="Audit Logging" description="Log all administrative actions">
            <Toggle checked={settings.auditLog} onChange={v => update('auditLog', v)} />
          </SettingRow>
          <SettingRow label="IP Whitelist" description="Restrict access to approved IP addresses">
            <Toggle checked={settings.ipWhitelist} onChange={v => update('ipWhitelist', v)} />
          </SettingRow>
        </SettingSection>

        {/* Data & Performance */}
        <SettingSection icon={Database} title="DATA & PERFORMANCE" description="System behavior">
          <SettingRow label="Auto-Refresh Dashboard" description="Live data updates">
            <Toggle checked={settings.autoRefresh} onChange={v => update('autoRefresh', v)} />
          </SettingRow>
          <SettingRow label="Refresh Interval" description="Dashboard update frequency (seconds)">
            <select
              className="input setting-select font-mono"
              value={settings.refreshInterval}
              onChange={e => update('refreshInterval', e.target.value)}
            >
              <option value="1">1s (Real-time)</option>
              <option value="5">5s</option>
              <option value="10">10s</option>
              <option value="30">30s</option>
              <option value="60">60s</option>
            </select>
          </SettingRow>
          <SettingRow label="Data Retention" description="Log history retention period">
            <select
              className="input setting-select font-mono"
              value={settings.dataRetention}
              onChange={e => update('dataRetention', e.target.value)}
            >
              <option value="30">30 days</option>
              <option value="90">90 days</option>
              <option value="180">180 days</option>
              <option value="365">1 year</option>
            </select>
          </SettingRow>
        </SettingSection>

        {/* Localization */}
        <SettingSection icon={Globe} title="LOCALIZATION" description="Regional settings">
          <SettingRow label="Timezone" description="System display timezone">
            <select
              className="input setting-select font-mono"
              value={settings.timezone}
              onChange={e => update('timezone', e.target.value)}
            >
              <option value="UTC">UTC</option>
              <option value="EST">EST (UTC-5)</option>
              <option value="PST">PST (UTC-8)</option>
              <option value="CET">CET (UTC+1)</option>
              <option value="JST">JST (UTC+9)</option>
              <option value="IST">IST (UTC+5:30)</option>
            </select>
          </SettingRow>
          <SettingRow label="Language" description="UI language">
            <select
              className="input setting-select font-mono"
              value={settings.language}
              onChange={e => update('language', e.target.value)}
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
              <option value="ja">日本語</option>
              <option value="ar">العربية</option>
            </select>
          </SettingRow>
          <SettingRow label="Date Format" description="Display format for dates">
            <select
              className="input setting-select font-mono"
              value={settings.dateFormat}
              onChange={e => update('dateFormat', e.target.value)}
            >
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </SettingRow>
        </SettingSection>

        {/* API & Integration */}
        <SettingSection icon={Key} title="API & INTEGRATIONS" description="External connections">
          <SettingRow label="API Endpoint" description="Backend service URL">
            <input
              type="text"
              className="input font-mono"
              value="https://api.ahos.grandview.com/v5"
              readOnly
              style={{ maxWidth: '300px' }}
            />
          </SettingRow>
          <SettingRow label="Auth0 Domain" description="Authentication provider">
            <input
              type="text"
              className="input font-mono"
              value="grandview.auth0.com"
              readOnly
              style={{ maxWidth: '300px' }}
            />
          </SettingRow>
          <SettingRow label="IoT Gateway" description="Device management endpoint">
            <div className="endpoint-status">
              <span className="status-dot active" />
              <span className="font-mono text-xs">Connected — 312 devices</span>
            </div>
          </SettingRow>
        </SettingSection>

        {/* System Info */}
        <SettingSection icon={Monitor} title="SYSTEM INFORMATION" description="Build & version">
          <div className="system-info-grid">
            <div className="sys-info-item">
              <span className="sys-label text-xs text-muted uppercase">Version</span>
              <span className="sys-value font-mono">AHOS V5.2.1</span>
            </div>
            <div className="sys-info-item">
              <span className="sys-label text-xs text-muted uppercase">Build</span>
              <span className="sys-value font-mono">#2023.10.26-b447</span>
            </div>
            <div className="sys-info-item">
              <span className="sys-label text-xs text-muted uppercase">Frontend</span>
              <span className="sys-value font-mono">React 18.2.0</span>
            </div>
            <div className="sys-info-item">
              <span className="sys-label text-xs text-muted uppercase">Backend</span>
              <span className="sys-value font-mono">FastAPI 0.104.1</span>
            </div>
            <div className="sys-info-item">
              <span className="sys-label text-xs text-muted uppercase">AI Engine</span>
              <span className="sys-value font-mono">NEXUS Core v5.2</span>
            </div>
            <div className="sys-info-item">
              <span className="sys-label text-xs text-muted uppercase">License</span>
              <span className="sys-value font-mono">Enterprise — Grandview Resort</span>
            </div>
          </div>
        </SettingSection>
      </div>
    </div>
  )
}
