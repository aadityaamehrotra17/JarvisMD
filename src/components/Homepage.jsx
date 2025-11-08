import { useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import logo from '../assets/logo.png'
import './Homepage.css'

function Homepage() {
  const navigate = useNavigate()

  // Scroll to top when component loads
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  const navigationOptions = [
    {
      title: "New Patient Analysis",
      description: "Upload medical scans and enter patient information for AI analysis",
      icon: "🏥",
      path: "/input",
      color: "blue"
    },
    {
      title: "Emergency Dashboard", 
      description: "View current patients sorted by urgency and AI analysis results",
      icon: "🚨",
      path: "/dashboard",
      color: "red"
    }
  ]

  return (
    <div className="homepage">
      {/* Dynamic header with gradient */}
      <header className="top-header">
        <div className="header-content">
          <div className="brand">
            <img src={logo} alt="JarvisMD Logo" className="logo-icon" />
            <span className="brand-name">JarvisMD</span>
          </div>
        </div>
      </header>

      {/* Hero section with dynamic elements */}
      <div className="hero-section">
        <div className="hero-background">
          <div className="floating-icons">
            <span className="float-icon" style={{animationDelay: '0s'}}>🧠</span>
            <span className="float-icon" style={{animationDelay: '2s'}}>💊</span>
            <span className="float-icon" style={{animationDelay: '4s'}}>🔬</span>
            <span className="float-icon" style={{animationDelay: '1s'}}>⚡</span>
            <span className="float-icon" style={{animationDelay: '3s'}}>🩺</span>
          </div>
        </div>
        <div className="hero-content">
          <div className="hero-badge">
            <span>🚀 Next-Generation Medical AI</span>
          </div>
          <h1 className="hero-title">
            <span className="gradient-text">Revolutionary</span><br />
            Medical Diagnosis
          </h1>
          <p className="hero-description">
            Harness the power of AI to analyze medical scans instantly, 
            prioritize emergency cases, and save lives with unprecedented accuracy.
          </p>
          <div className="hero-stats">
            <div className="stat">
              <span className="stat-number">99.7%</span>
              <span className="stat-label">Accuracy</span>
            </div>
            <div className="stat">
              <span className="stat-number">&lt;30s</span>
              <span className="stat-label">Analysis Time</span>
            </div>
            <div className="stat">
              <span className="stat-number">24/7</span>
              <span className="stat-label">Available</span>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced actions section */}
      <div className="actions-section">
        <div className="container">
          <div className="nav-grid">
            {navigationOptions.map((option, index) => (
              <div 
                key={index}
                className={`nav-card ${option.color}`}
                onClick={() => navigate(option.path)}
              >
                <div className="nav-icon">{option.icon}</div>
                <h3 className="nav-title">{option.title}</h3>
                <p className="nav-description">{option.description}</p>
                <div className="nav-arrow">→</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Homepage
