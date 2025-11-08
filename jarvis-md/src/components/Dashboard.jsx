import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './Dashboard.css'

function Dashboard() {
  const navigate = useNavigate()
  
  // Mock data - your teammate will replace this with real API calls
  const [cases, setCases] = useState([
    {
      id: 1,
      patientName: "John Smith",
      age: 45,
      symptoms: "Chest pain, shortness of breath",
      urgencyScore: 9.2,
      urgencyLevel: "critical",
      scanType: "Chest X-Ray",
      timeSubmitted: "2 min ago",
      aiSummary: "Possible cardiac event detected"
    },
    {
      id: 2,
      patientName: "Maria Garcia",
      age: 67,
      symptoms: "Severe headache, vision changes",
      urgencyScore: 8.7,
      urgencyLevel: "high",
      scanType: "Brain CT",
      timeSubmitted: "8 min ago",
      aiSummary: "Potential stroke indicators present"
    },
    {
      id: 3,
      patientName: "David Chen",
      age: 32,
      symptoms: "Abdominal pain, nausea",
      urgencyScore: 6.1,
      urgencyLevel: "moderate",
      scanType: "Abdominal CT",
      timeSubmitted: "15 min ago",
      aiSummary: "Appendicitis likely, requires monitoring"
    },
    {
      id: 4,
      patientName: "Sarah Johnson",
      age: 28,
      symptoms: "Ankle injury from fall",
      urgencyScore: 3.4,
      urgencyLevel: "low",
      scanType: "Ankle X-Ray",
      timeSubmitted: "22 min ago",
      aiSummary: "Mild sprain, no fracture detected"
    }
  ])

  // Sort cases by urgency score (highest first)
  const sortedCases = [...cases].sort((a, b) => b.urgencyScore - a.urgencyScore)

  const getUrgencyColor = (level) => {
    switch (level) {
      case 'critical': return '#e74c3c'
      case 'high': return '#f39c12'
      case 'moderate': return '#f1c40f'
      case 'low': return '#27ae60'
      default: return '#95a5a6'
    }
  }

  const getUrgencyIcon = (level) => {
    switch (level) {
      case 'critical': return '🚨'
      case 'high': return '⚠️'
      case 'moderate': return '⚡'
      case 'low': return '✅'
      default: return '📋'
    }
  }

  const handleCaseClick = (caseId) => {
    navigate(`/case/${caseId}`)
  }

  const addNewPatient = () => {
    navigate('/input')
  }

  return (
    <div className="dashboard">
      <button 
        onClick={() => navigate('/')} 
        className="back-btn"
      >
        ← Back to Home
      </button>
      
      <div className="dashboard-header">
        <div className="header-content">
          <h2>Emergency Room Dashboard</h2>
          <p className="subtitle">Patients sorted by AI urgency analysis</p>
        </div>
        <button onClick={addNewPatient} className="add-patient-btn">
          ➕ New Patient
        </button>
      </div>

      <div className="dashboard-stats">
        <div className="stat-card critical">
          <div className="stat-number">{cases.filter(c => c.urgencyLevel === 'critical').length}</div>
          <div className="stat-label">Critical</div>
        </div>
        <div className="stat-card high">
          <div className="stat-number">{cases.filter(c => c.urgencyLevel === 'high').length}</div>
          <div className="stat-label">High Priority</div>
        </div>
        <div className="stat-card moderate">
          <div className="stat-number">{cases.filter(c => c.urgencyLevel === 'moderate').length}</div>
          <div className="stat-label">Moderate</div>
        </div>
        <div className="stat-card low">
          <div className="stat-number">{cases.filter(c => c.urgencyLevel === 'low').length}</div>
          <div className="stat-label">Low Priority</div>
        </div>
      </div>

      <div className="cases-container">
        {sortedCases.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🏥</div>
            <h3>No patients in queue</h3>
            <p>Add a new patient to get started with AI analysis</p>
            <button onClick={addNewPatient} className="empty-state-btn">
              Add First Patient
            </button>
          </div>
        ) : (
          <div className="cases-grid">
            {sortedCases.map((case_) => (
              <div 
                key={case_.id} 
                className={`case-card ${case_.urgencyLevel}`}
                onClick={() => handleCaseClick(case_.id)}
                style={{
                  borderLeft: `4px solid ${getUrgencyColor(case_.urgencyLevel)}`
                }}
              >
                <div className="case-header">
                  <div className="patient-info">
                    <h3 className="patient-name">{case_.patientName}</h3>
                    <span className="patient-age">Age {case_.age}</span>
                  </div>
                  <div className="urgency-badge">
                    <span className="urgency-icon">{getUrgencyIcon(case_.urgencyLevel)}</span>
                    <span className="urgency-score">{case_.urgencyScore}</span>
                  </div>
                </div>

                <div className="case-content">
                  <div className="symptoms">
                    <strong>Symptoms:</strong> {case_.symptoms}
                  </div>
                  
                  <div className="scan-info">
                    <span className="scan-type">📋 {case_.scanType}</span>
                    <span className="time-submitted">⏱️ {case_.timeSubmitted}</span>
                  </div>

                  <div className="ai-summary">
                    <strong>AI Analysis:</strong> {case_.aiSummary}
                  </div>
                </div>

                <div className="case-actions">
                  <button className="view-details-btn">
                    View Full Analysis →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
