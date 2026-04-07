import { useNavigate } from 'react-router-dom'
import {
  Shield, Zap, Bot, Activity, BarChart3,
  Globe, Cpu, ArrowRight, ChevronRight
} from 'lucide-react'
import './Landing.css'

const FEATURES = [
  {
    icon: Bot,
    title: 'Hierarchical AI Agents',
    description: 'Executive, Domain, and Sub-agents work in concert to orchestrate complex hotel operations autonomously.',
  },
  {
    icon: Shield,
    title: 'Zero-Trust Security',
    description: 'Human-in-the-Loop approvals, anomaly detection, and attack simulation ensure every action is verified.',
  },
  {
    icon: Zap,
    title: 'Pluggable LLM Brain',
    description: 'Switch between OpenAI, Gemini, Mistral, or local models with a single config change. Zero vendor lock-in.',
  },
  {
    icon: Activity,
    title: 'Real-Time Monitoring',
    description: 'IoT device control, live event streams, and operational dashboards across your entire hotel chain.',
  },
  {
    icon: Globe,
    title: 'Cross-Platform Integrations',
    description: 'Gmail, Notion, Twilio, and IoT systems connected out of the box for seamless operations.',
  },
  {
    icon: BarChart3,
    title: 'Predictive Analytics',
    description: 'AI-driven maintenance forecasting, fraud detection, guest personalization, and resource optimization.',
  },
]

const STATS = [
  { value: '8+', label: 'AI Agents' },
  { value: '120+', label: 'IoT Devices' },
  { value: '3', label: 'Hotels Managed' },
  { value: '99.9%', label: 'Uptime SLA' },
]

export default function Landing() {
  const navigate = useNavigate()

  const enterDashboard = () => navigate('/')

  return (
    <div className="landing">
      {/* Animated background grid */}
      <div className="landing-bg-grid" />
      <div className="landing-bg-glow landing-bg-glow--1" />
      <div className="landing-bg-glow landing-bg-glow--2" />

      {/* Navigation */}
      <nav className="landing-nav">
        <div className="landing-nav-left">
          <Zap size={22} className="landing-nav-icon" />
          <span className="landing-nav-brand">AEGIS</span>
          <span className="landing-nav-sep">//</span>
          <span className="landing-nav-sub">Hospitality OS</span>
        </div>
        <button className="landing-nav-login" onClick={enterDashboard}>
          <Cpu size={14} />
          Launch Dashboard
        </button>
      </nav>

      {/* Hero */}
      <section className="landing-hero">
        <div className="landing-hero-badge">
          <Cpu size={14} />
          <span>Research-Grade Multi-Agent System</span>
        </div>
        <h1 className="landing-hero-title">
          The AI Operating System<br />
          <span className="landing-hero-accent">for Modern Hospitality</span>
        </h1>
        <p className="landing-hero-subtitle">
          Aegis Hospitality OS orchestrates your entire hotel chain through an autonomous
          hierarchy of AI agents — from security protocols to guest services — with
          human oversight at every critical decision point.
        </p>
        <div className="landing-hero-actions">
          <button className="landing-btn-primary" onClick={enterDashboard}>
            <span>Access Command Center</span>
            <ArrowRight size={18} />
          </button>
          <a className="landing-btn-secondary" href="https://github.com/Arisha-27/HotelAuth0" target="_blank" rel="noopener noreferrer">
            View on GitHub
            <ChevronRight size={16} />
          </a>
        </div>
      </section>

      {/* Stats row */}
      <section className="landing-stats">
        {STATS.map((stat) => (
          <div key={stat.label} className="landing-stat">
            <span className="landing-stat-value">{stat.value}</span>
            <span className="landing-stat-label">{stat.label}</span>
          </div>
        ))}
      </section>

      {/* Features */}
      <section className="landing-features">
        <h2 className="landing-section-title">
          <span className="landing-section-accent">Core Capabilities</span>
        </h2>
        <div className="landing-features-grid">
          {FEATURES.map((f) => (
            <div key={f.title} className="landing-feature-card">
              <div className="landing-feature-icon-wrap">
                <f.icon size={24} />
              </div>
              <h3>{f.title}</h3>
              <p>{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture preview */}
      <section className="landing-arch">
        <h2 className="landing-section-title">
          <span className="landing-section-accent">Agent Hierarchy</span>
        </h2>
        <div className="landing-arch-visual">
          <div className="landing-arch-node landing-arch-exec">
            <Bot size={20} />
            <span>Executive Agent</span>
          </div>
          <div className="landing-arch-connectors">
            <div className="landing-arch-line" />
            <div className="landing-arch-line" />
            <div className="landing-arch-line" />
          </div>
          <div className="landing-arch-row">
            <div className="landing-arch-node landing-arch-domain">
              <Shield size={16} />
              <span>Security</span>
            </div>
            <div className="landing-arch-node landing-arch-domain">
              <Activity size={16} />
              <span>Operations</span>
            </div>
            <div className="landing-arch-node landing-arch-domain">
              <BarChart3 size={16} />
              <span>Finance</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="landing-cta">
        <h2>Ready to take command?</h2>
        <p>Enter the Aegis OS dashboard and start managing your hotel chain with AI.</p>
        <button className="landing-btn-primary" onClick={enterDashboard}>
          <Cpu size={16} />
          <span>Launch Command Center</span>
          <ArrowRight size={18} />
        </button>
      </section>

      <footer className="landing-footer">
        <span>© 2026 Aegis Hospitality OS</span>
        <span className="landing-footer-sep">•</span>
        <span>Powered by Gemini AI</span>
      </footer>
    </div>
  )
}
