import { useState, useEffect } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Map, Bot, Shield, Settings as SettingsIcon,
  Activity, ScrollText, BarChart3, ChevronLeft, ChevronRight,
  Zap
} from 'lucide-react'
import { SYSTEM_INFO } from '../data/mockData'
import './Layout.css'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'DASHBOARD', icon: LayoutDashboard },
  { path: '/dashboard/floor-plan', label: 'FLOOR PLAN', icon: Map },
  { path: '/dashboard/agents', label: 'AI AGENTS', icon: Bot },
  { path: '/dashboard/security', label: 'SECURITY', icon: Shield },
  { path: '/dashboard/operations', label: 'OPERATIONS', icon: Activity },
  { path: '/dashboard/analytics', label: 'ANALYTICS', icon: BarChart3 },
  { path: '/dashboard/logs', label: 'EVENT LOGS', icon: ScrollText },
  { path: '/dashboard/settings', label: 'SETTINGS', icon: SettingsIcon },
]

function TopBar() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const utcTime = time.toUTCString().split(' ').slice(4, 5).join('')
  const dateStr = time.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    timeZone: 'UTC'
  }).toUpperCase()

  return (
    <header className="topbar">
      <div className="topbar-left">
        <Zap size={16} className="topbar-logo-icon" />
        <span className="topbar-logo">{SYSTEM_INFO.name}</span>
        <span className="topbar-divider">//</span>
        <span className="topbar-version font-mono">{SYSTEM_INFO.version}</span>
      </div>
      <div className="topbar-center">
        <span className="topbar-property">{SYSTEM_INFO.property}</span>
        <span className="topbar-separator">|</span>
        <span className="topbar-time font-mono">{utcTime} UTC</span>
        <span className="topbar-separator">|</span>
        <span className="topbar-date font-mono">{dateStr}</span>
      </div>
      <div className="topbar-right">
        <span className="topbar-status font-mono">AI Status:</span>
        <span className="status-dot active"></span>
        <span className="topbar-status-label font-mono">OPTIMIZED</span>
      </div>
    </header>
  )
}

function Sidebar({ collapsed, onToggle }) {
  const location = useLocation()

  return (
    <nav className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
            end={item.path === '/dashboard'}
            title={item.label}
          >
            <item.icon size={16} />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </div>
      <button className="sidebar-toggle" onClick={onToggle}>
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </nav>
  )
}

export default function Layout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="layout">
      <TopBar />
      <div className="layout-body">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(c => !c)}
        />
        <main className={`layout-main ${sidebarCollapsed ? 'expanded' : ''}`}>
          <div className="page-enter">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
