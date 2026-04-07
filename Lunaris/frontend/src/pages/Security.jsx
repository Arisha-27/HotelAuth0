import { useState, useEffect } from 'react'
import {
  Shield, Camera, DoorOpen, AlertTriangle, UserCheck,
  MapPin, Clock, Eye, Lock, Unlock, Radio, FileWarning
} from 'lucide-react'
import { SECURITY_EVENTS } from '../data/mockData'
import './Security.css'

const CAMERAS = [
  { id: 'CAM-01', location: 'Main Lobby', status: 'online', occupancy: 34, capacity: 150 },
  { id: 'CAM-02', location: 'Pool Area', status: 'online', occupancy: 12, capacity: 40 },
  { id: 'CAM-03', location: 'Parking Garage L1', status: 'online', occupancy: null, capacity: null },
  { id: 'CAM-04', location: 'Floor 3 Corridor', status: 'alert', occupancy: null, capacity: null },
  { id: 'CAM-05', location: 'Restaurant', status: 'online', occupancy: 67, capacity: 120 },
  { id: 'CAM-06', location: 'Spa Entrance', status: 'online', occupancy: 8, capacity: 30 },
  { id: 'CAM-07', location: 'Floor 7 Elevator', status: 'online', occupancy: null, capacity: null },
  { id: 'CAM-08', location: 'Back Entrance', status: 'online', occupancy: null, capacity: null },
]

const ACCESS_LOG = [
  { time: '22:48:01', type: 'grant', person: 'Staff #A-2291', location: 'Floor 7 Elevator', method: 'Badge' },
  { time: '22:47:45', type: 'grant', person: 'Guest #W-4412', location: 'Pool Area', method: 'Wristband' },
  { time: '22:47:30', type: 'deny', person: 'Unknown', location: 'Staff Only — Floor 3', method: 'Badge (Expired)' },
  { time: '22:46:55', type: 'grant', person: 'Staff #A-1105', location: 'Parking Garage L1', method: 'Badge' },
  { time: '22:46:20', type: 'grant', person: 'Guest #W-5501', location: 'Floor 3 Entry', method: 'Wristband' },
  { time: '22:45:40', type: 'grant', person: 'Guest #W-3221', location: 'Spa Entrance', method: 'Wristband' },
  { time: '22:45:12', type: 'grant', person: 'Staff #A-3340', location: 'Main Lobby', method: 'Badge' },
  { time: '22:44:55', type: 'anomaly', person: 'Guest #W-5501', location: 'Floor 3 Entry', method: 'Double-scan detected' },
]

function CameraFeed({ camera }) {
  return (
    <div className={`camera-feed card ${camera.status === 'alert' ? 'camera-alert' : ''}`}>
      <div className="camera-viewport">
        {/* Simulated static / feed */}
        <div className="camera-static">
          <div className="camera-scanline" />
          <div className="camera-noise" />
        </div>
        <div className="camera-overlay">
          <div className="camera-id font-mono">{camera.id}</div>
          <div className="camera-rec">
            <span className="rec-dot" />
            <span className="font-mono">REC</span>
          </div>
        </div>
        {camera.status === 'alert' && (
          <div className="camera-alert-badge">
            <AlertTriangle size={10} />
            <span className="font-mono">ALERT</span>
          </div>
        )}
      </div>
      <div className="camera-info">
        <div className="camera-location font-mono">{camera.location}</div>
        {camera.occupancy !== null && (
          <div className="camera-occupancy font-mono text-xs">
            <Users size={10} /> {camera.occupancy}/{camera.capacity}
          </div>
        )}
      </div>
    </div>
  )
}

function Users({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  )
}

function ThreatLevel() {
  return (
    <div className="card threat-card">
      <div className="card-header">
        <h3>Threat Level</h3>
        <Shield size={14} className="text-accent" />
      </div>
      <div className="card-body threat-body">
        <div className="threat-gauge">
          <div className="threat-level-indicator">
            <div className="threat-bar">
              <div className="threat-segments">
                <div className="threat-seg low active" />
                <div className="threat-seg guarded active" />
                <div className="threat-seg elevated" />
                <div className="threat-seg high" />
                <div className="threat-seg severe" />
              </div>
              <div className="threat-marker" style={{ left: '35%' }} />
            </div>
            <div className="threat-labels font-mono text-xs">
              <span>LOW</span>
              <span>GUARDED</span>
              <span>ELEVATED</span>
              <span>HIGH</span>
              <span>SEVERE</span>
            </div>
          </div>
          <div className="threat-current">
            <span className="threat-current-level font-mono">GUARDED</span>
            <span className="text-xs text-muted font-mono">Weather advisory in effect</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function PerimeterStatus() {
  const zones = [
    { name: 'North Entrance', status: 'secure' },
    { name: 'South Entrance', status: 'secure' },
    { name: 'East Wing', status: 'secure' },
    { name: 'West Wing', status: 'monitoring' },
    { name: 'Parking Structure', status: 'secure' },
    { name: 'Pool/Garden', status: 'secure' },
    { name: 'Loading Dock', status: 'secure' },
    { name: 'Rooftop', status: 'locked' },
  ]

  return (
    <div className="card perimeter-card">
      <div className="card-header">
        <h3>Perimeter Zones</h3>
        <span className="font-mono text-xs text-muted">{zones.filter(z => z.status === 'secure').length}/{zones.length} SECURE</span>
      </div>
      <div className="card-body">
        <div className="perimeter-grid">
          {zones.map(zone => (
            <div key={zone.name} className={`perimeter-zone ${zone.status}`}>
              <div className="perimeter-zone-icon">
                {zone.status === 'secure' ? <Lock size={12} /> :
                 zone.status === 'monitoring' ? <Eye size={12} /> :
                 <Lock size={12} />}
              </div>
              <div className="perimeter-zone-info">
                <span className="zone-name font-mono">{zone.name}</span>
                <span className="zone-status font-mono text-xs">{zone.status.toUpperCase()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function Security() {
  const [selectedEvent, setSelectedEvent] = useState(null)

  return (
    <div className="security-page">
      <div className="security-header">
        <div className="security-title">
          <Shield size={18} className="text-accent" />
          <h1>SECURITY COMMAND</h1>
        </div>
        <div className="security-stats font-mono text-xs">
          <span className="sec-stat">
            <Camera size={12} /> {CAMERAS.filter(c => c.status === 'online').length}/{CAMERAS.length} CAMS
          </span>
          <span className="sec-stat">
            <DoorOpen size={12} /> 42 DOORS MONITORED
          </span>
          <span className="sec-stat alert-stat">
            <AlertTriangle size={12} /> {CAMERAS.filter(c => c.status === 'alert').length} ALERT
          </span>
        </div>
      </div>

      {/* Threat + Perimeter row */}
      <div className="security-top-row">
        <ThreatLevel />
        <PerimeterStatus />
      </div>

      {/* Camera Grid */}
      <div className="card">
        <div className="card-header">
          <h3>CCTV Surveillance Grid</h3>
          <span className="font-mono text-xs text-muted">{CAMERAS.length} FEEDS</span>
        </div>
        <div className="camera-grid">
          {CAMERAS.map(cam => (
            <CameraFeed key={cam.id} camera={cam} />
          ))}
        </div>
      </div>

      {/* Access Log + Events */}
      <div className="security-bottom-row">
        <div className="card access-log-card">
          <div className="card-header">
            <h3>Access Control Log</h3>
            <span className="font-mono text-xs text-muted">LIVE</span>
          </div>
          <div className="card-body access-log-body font-mono">
            {ACCESS_LOG.map((entry, i) => (
              <div key={i} className={`access-entry ${entry.type}`}>
                <span className="access-time text-muted">[{entry.time}]</span>
                <span className={`access-type-badge ${entry.type}`}>
                  {entry.type === 'grant' ? <Unlock size={10} /> :
                   entry.type === 'deny' ? <Lock size={10} /> :
                   <FileWarning size={10} />}
                  {entry.type.toUpperCase()}
                </span>
                <span className="access-person">{entry.person}</span>
                <span className="access-location text-muted">→ {entry.location}</span>
                <span className="access-method text-xs text-muted">{entry.method}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card events-card">
          <div className="card-header">
            <h3>Security Events</h3>
          </div>
          <div className="card-body events-body">
            {SECURITY_EVENTS.map(event => (
              <div
                key={event.id}
                className={`security-event ${event.status}`}
                onClick={() => setSelectedEvent(event)}
              >
                <div className="event-header">
                  <span className="event-type font-mono">{event.type.replace(/_/g, ' ').toUpperCase()}</span>
                  <span className={`status-badge ${event.status === 'resolved' ? 'positive' : event.status === 'investigating' ? 'active' : 'idle'}`}>
                    {event.status.toUpperCase()}
                  </span>
                </div>
                <div className="event-details">
                  <span className="font-mono text-xs"><MapPin size={10} /> {event.location}</span>
                  <span className="font-mono text-xs text-muted"><Clock size={10} /> {event.time}</span>
                </div>
                {event.person && (
                  <span className="font-mono text-xs text-muted"><UserCheck size={10} /> {event.person}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
