import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './Dashboard.css'

function Dashboard() {
  const navigate = useNavigate()
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalCases: 0,
    criticalCases: 0,
    serverStatus: 'unknown'
  })

  // Helper functions
  const getUrgencyLevel = (score) => {
    if (score >= 7) return 'critical'
    if (score >= 4) return 'priority'  
    return 'routine'
  }

  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return "Recently"
    
    const now = new Date()
    const submittedTime = new Date(timestamp)
    const diffInMinutes = Math.floor((now - submittedTime) / (1000 * 60))
    
    if (diffInMinutes < 1) return "Just now"
    if (diffInMinutes < 60) return `${diffInMinutes} min ago`
    
    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `${diffInHours} hr ago`
    
    const diffInDays = Math.floor(diffInHours / 24)
    return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`
  }

  const getAISummary = (analysis) => {
    // Create a meaningful clinical summary for dashboard view
    try {
      const report = JSON.parse(analysis.structured_report.replace('```json', '').replace('```', ''))
      
      // Priority 1: Use clinical diagnosis from AI analysis (most meaningful)
      if (report.preliminary_diagnosis) {
        let diagnosis = report.preliminary_diagnosis.trim()
        // Truncate if too long but keep it meaningful
        if (diagnosis.length > 80) {
          diagnosis = diagnosis.substring(0, 77) + '...'
        }
        return diagnosis
      }
      
      // Priority 2: Use findings summary from AI analysis
      if (report.findings_summary) {
        let findings = report.findings_summary.trim()
        if (findings.length > 80) {
          findings = findings.substring(0, 77) + '...'
        }
        return findings
      }
      
      // Priority 3: Use preliminary impression
      if (report.preliminary_impression) {
        let impression = report.preliminary_impression.trim()
        if (impression.length > 80) {
          impression = impression.substring(0, 77) + '...'
        }
        return impression
      }
      
      // Priority 4: Show significant pathology findings (fallback)
      if (analysis.ai_findings) {
        const significantFindings = Object.entries(analysis.ai_findings)
          .filter(([_, prob]) => prob > 0.5) // Only high confidence findings
          .sort(([,a], [,b]) => b - a) // Sort by probability
          .slice(0, 2) // Take top 2
          .map(([pathology, prob]) => `${pathology} (${(prob * 100).toFixed(0)}%)`)
        
        if (significantFindings.length > 0) {
          return `Detected: ${significantFindings.join(', ')}`
        }
      }
      
      // Final fallback: Just show urgency
      return `Urgency Score: ${analysis.urgency_score?.toFixed(1)}/10`
    } catch (error) {
      console.error('Error parsing AI summary:', error)
      return `Urgency Score: ${analysis.urgency_score?.toFixed(1)}/10`
    }
  }

  // Check server health and load cases
  useEffect(() => {
    checkServerHealth()
    loadCases()
  }, [])

  const checkServerHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health')
      if (response.ok) {
        setStats(prev => ({ ...prev, serverStatus: 'online' }))
      } else {
        setStats(prev => ({ ...prev, serverStatus: 'offline' }))
      }
    } catch (error) {
      console.log('Server offline or unreachable')
      setStats(prev => ({ ...prev, serverStatus: 'offline' }))
    }
  }

  const loadCases = () => {
    // Load all cases from sessionStorage
    const storedCases = sessionStorage.getItem('allCases')
    let realCases = []
    
    if (storedCases) {
      try {
        realCases = JSON.parse(storedCases)
        console.log('Loaded real cases:', realCases)
      } catch (error) {
        console.error('Error parsing stored cases:', error)
      }
    }

    // Convert real cases to dashboard format
    const convertedCases = realCases.map(analysis => {
      const submittedTime = new Date(analysis.time_submitted)
      const waitingTimeMinutes = Math.floor((new Date() - submittedTime) / (1000 * 60))
      
      return {
        id: analysis.patient_id,
        patientName: analysis.patient_name,
        age: parseInt(analysis.patient_age) || 0,
        symptoms: analysis.symptoms,
        urgencyScore: parseFloat(analysis.urgency_score?.toFixed(1)) || 0,
        urgencyLevel: getUrgencyLevel(analysis.urgency_score),
        scanType: "Chest X-Ray",
        timeSubmitted: formatTimeAgo(analysis.time_submitted),
        submittedAt: analysis.submitted_at || "Unknown time",
        waitingTimeMinutes: waitingTimeMinutes,
        submittedTimestamp: submittedTime,
        aiSummary: getAISummary(analysis)
      }
    })

    // Use only real analysis cases (no more demo data)
    setCases(convertedCases)

    // Calculate stats
    const totalCases = convertedCases.length
    const criticalCases = convertedCases.filter(c => c.urgencyLevel === 'critical').length

    setStats(prev => ({
      ...prev,
      totalCases,
      criticalCases
    }))

    setLoading(false)
  }

  // Advanced sorting: 1) Urgency Score (highest first), 2) Waiting Time (longest first), 3) Age (oldest first)
  const sortedCases = [...cases].sort((a, b) => {
    // Primary sort: Urgency Score (highest first)
    if (a.urgencyScore !== b.urgencyScore) {
      return b.urgencyScore - a.urgencyScore
    }
    
    // Secondary sort: Waiting Time (longest waiting first)
    if (a.waitingTimeMinutes !== b.waitingTimeMinutes) {
      return b.waitingTimeMinutes - a.waitingTimeMinutes
    }
    
    // Tertiary sort: Age (oldest patients first)
    return b.age - a.age
  })

  const getUrgencyColor = (level) => {
    switch (level) {
      case 'critical': return '#e74c3c'
      case 'priority': return '#eab308'
      case 'routine': return '#27ae60'
      default: return '#95a5a6'
    }
  }

  const getUrgencyIcon = (level) => {
    switch (level) {
      case 'critical': return '🚨'
      case 'priority': return '⚠️'
      case 'routine': return '📋'
      default: return '📋'
    }
  }

  const handleCaseClick = (caseId) => {
    // Find the specific case data to pass along
    const caseData = cases.find(c => c.id === caseId)
    
    if (caseData) {
      // Find the full analysis data for the case
      const storedCases = JSON.parse(sessionStorage.getItem('allCases') || '[]')
      const fullAnalysisData = storedCases.find(analysis => analysis.patient_id === caseId)
      
      if (fullAnalysisData) {
        navigate(`/case/${caseId}`, { 
          state: { analysisData: fullAnalysisData }
        })
        return
      }
    }
    
    // Fallback navigation without state
    navigate(`/case/${caseId}`)
  }

  const handleProcessCase = (caseId, patientName, e) => {
    e.stopPropagation() // Prevent row click when button is clicked
    
    const confirmMessage = `Begin treating ${patientName}?\n\nThis will move them from the triage queue to active treatment.`
    
    if (window.confirm(confirmMessage)) {
      // Remove from sessionStorage
      const storedCases = JSON.parse(sessionStorage.getItem('allCases') || '[]')
      const updatedCases = storedCases.filter(analysis => analysis.patient_id !== caseId)
      sessionStorage.setItem('allCases', JSON.stringify(updatedCases))
      
      // Also update latestAnalysis if it matches the processed case
      const latestAnalysis = sessionStorage.getItem('latestAnalysis')
      if (latestAnalysis) {
        try {
          const latest = JSON.parse(latestAnalysis)
          if (latest.patient_id === caseId) {
            sessionStorage.removeItem('latestAnalysis')
          }
        } catch (error) {
          console.error('Error checking latest analysis:', error)
        }
      }
      
      // Reload the cases to update the display
      loadCases()
      
      console.log(`✅ Patient ${patientName} (ID: ${caseId}) moved to treatment - removed from triage queue`)
    }
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
          {/* <div className="server-status">
            <span className={`status-indicator ${stats.serverStatus}`}></span>
            Server: {stats.serverStatus === 'online' ? 'Online' : 'Offline'}
            {stats.serverStatus === 'online' && <span className="pulse-dot"></span>}
          </div> */}
        </div>
        <button onClick={addNewPatient} className="add-patient-btn">
          ➕ New Patient Analysis
        </button>
      </div>

      <div className="dashboard-stats">
        <div className="stat-card total">
          <div className="stat-number">{stats.totalCases}</div>
          <div className="stat-label">Total Cases</div>
        </div>
        <div className="stat-card critical">
          <div className="stat-number">{stats.criticalCases}</div>
          <div className="stat-label">High Priority</div>
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
          <div className="cases-table-container">
            <table className="cases-table">
              <thead>
                <tr>
                  <th>Priority</th>
                  <th>Patient</th>
                  <th>Age</th>
                  <th>Symptoms</th>
                  <th>Time</th>
                  <th>Score</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedCases.map((case_) => (
                  <tr 
                    key={case_.id} 
                    className={`case-row ${case_.urgencyLevel}`}
                    onClick={() => handleCaseClick(case_.id)}
                    style={{
                      borderLeft: `4px solid ${getUrgencyColor(case_.urgencyLevel)}`
                    }}
                  >
                    <td className="priority-cell">
                      <span className="urgency-icon">{getUrgencyIcon(case_.urgencyLevel)}</span>
                    </td>
                    <td className="patient-cell">
                      <span className="patient-name">{case_.patientName}</span>
                    </td>
                    <td className="age-cell">{case_.age}</td>
                    <td className="symptoms-cell">
                      <span className="symptoms-text" title={case_.symptoms}>
                        {case_.symptoms.length > 60 ? `${case_.symptoms.substring(0, 60)}...` : case_.symptoms}
                      </span>
                    </td>
                    <td className="time-cell">{case_.timeSubmitted}</td>
                    <td className="score-cell">
                      <span className={`score-badge ${case_.urgencyLevel}`}>
                        {case_.urgencyScore.toFixed(1)}
                      </span>
                    </td>
                    <td className="action-cell">
                      <div className="action-buttons">
                        <button 
                          className="view-btn" 
                          onClick={(e) => { e.stopPropagation(); handleCaseClick(case_.id); }}
                          title="View full analysis"
                        >
                          View
                        </button>
                        <button 
                          className="treat-btn" 
                          onClick={(e) => handleProcessCase(case_.id, case_.patientName, e)}
                          title="Begin treating patient"
                        >
                          Treat
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
