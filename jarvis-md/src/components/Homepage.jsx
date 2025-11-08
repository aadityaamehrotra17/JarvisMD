import { useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
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
      <div className="hero-section">
        <div className="hero-content">
          <h1>Welcome to JarvisMD</h1>
          <p className="hero-subtitle">
            AI-Powered Emergency Medical Analysis System
          </p>
          <p className="hero-description">
            Revolutionizing emergency healthcare with intelligent scan analysis, 
            real-time urgency scoring, and comprehensive patient risk assessment.
          </p>
        </div>
      </div>

      <div className="navigation-section">
        <div className="container">
          <h2>Choose Your Action</h2>
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
                <button className="nav-button">
                  Get Started →
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      
    </div>
  )
}

export default Homepage
