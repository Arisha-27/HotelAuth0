import { Link } from 'react-router-dom'
import { Bot, Shield, Zap, ArrowRight, Network } from 'lucide-react'
import './Landing.css'

export default function Landing() {
  return (
    <div className="landing-container">
      <div className="landing-background">
        <div className="grid-overlay"></div>
        <div className="glow-sphere main-sphere"></div>
        <div className="glow-sphere secondary-sphere"></div>
      </div>

      <nav className="landing-nav">
        <div className="nav-logo">
          <Zap className="logo-icon" size={24} />
          <span>LUNARIS</span>
        </div>
        <div className="nav-links">
          <Link to="/dashboard" className="nav-link-btn">
            ENTER DASHBOARD <ArrowRight size={16} />
          </Link>
        </div>
      </nav>

      <main className="landing-main">
        <div className="hero-section">
          <div className="hero-badge font-mono">
            <span className="live-dot"></span> V5.0.0 ONLINE
          </div>
          <h1 className="hero-title">
            The Multi-Agent <br />
            <span className="highlight">Operating System</span>
          </h1>
          <p className="hero-subtitle">
            Harness the power of hierarchical AI agents. Lunaris orchestrates operations, ensures zero-trust security, and automates your hospitality environment with unparalleled precision.
          </p>
          
          <div className="hero-cta-group">
            <Link to="/dashboard" className="btn-primary glow-effect">
              INITIALIZE SYSTEM
            </Link>
          </div>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon-wrapper"><Network size={20} /></div>
            <h3>Hierarchical Agents</h3>
            <p>Executive delegation to specialized domain agents for total operational coverage.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon-wrapper"><Shield size={20} /></div>
            <h3>Zero-Trust HITL</h3>
            <p>Every sensitive action pauses for cryptographically secure human validation.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon-wrapper"><Bot size={20} /></div>
            <h3>Pluggable LLM Brain</h3>
            <p>Powered by adaptive language models with zero vendor lock-in capability.</p>
          </div>
        </div>
      </main>
    </div>
  )
}
