import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import './CaseDetails.css'

function CaseDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [caseData, setCaseData] = useState(null)
  const [loading, setLoading] = useState(true)

  // Mock detailed data - your teammate will replace with real API
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      const mockCase = {
        id: parseInt(id),
        patientName: "John Smith",
        age: 45,
        gender: "Male",
        symptoms: "Chest pain, shortness of breath, sweating",
        timeSubmitted: "2 min ago",
        
        // Urgency Assessment
        urgencyScore: 9.2,
        urgencyLevel: "critical",
        riskFactors: [
          "Age over 40",
          "History of hypertension", 
          "Family history of cardiac disease",
          "Elevated troponin levels"
        ],
        
        // Scan Analysis
        scanType: "Chest X-Ray",
        scanResults: {
          findings: [
            "Possible cardiomegaly (enlarged heart)",
            "Mild pulmonary edema",
            "No pneumothorax detected",
            "Clear lung fields in lower lobes"
          ],
          confidence: 94,
          aiModel: "CardioVision AI v2.3"
        },
        
        // Medical History
        medicalHistory: {
          conditions: ["Hypertension", "Type 2 Diabetes"],
          medications: ["Lisinopril 10mg", "Metformin 500mg"],
          allergies: ["Penicillin"],
          lastVisit: "6 months ago - routine checkup"
        },
        
        // Recommendations
        recommendations: [
          {
            priority: "immediate",
            action: "Order ECG and cardiac enzymes",
            reason: "Rule out myocardial infarction"
          },
          {
            priority: "urgent", 
            action: "Administer oxygen therapy",
            reason: "Patient showing signs of respiratory distress"
          },
          {
            priority: "monitor",
            action: "Continuous cardiac monitoring",
            reason: "Track for arrhythmias"
          }
        ],
        
        // Risk Assessment
        riskAssessment: {
          cardiacEvent: 85,
          requiresSurgery: 40,
          hospitalization: 95,
          mortality: 12
        }
      }
      setCaseData(mockCase)
      setLoading(false)
    }, 500)
  }, [id])

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'immediate': return '#e74c3c'
      case 'urgent': return '#f39c12'
      case 'monitor': return '#3498db'
      default: return '#95a5a6'
    }
  }

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'immediate': return '🚨'
      case 'urgent': return '⚠️'
      case 'monitor': return '👁️'
      default: return '📋'
    }
  }

  if (loading) {
    return (
      <div className="case-details loading">
        <div className="loading-spinner">🔄 Loading patient analysis...</div>
      </div>
    )
  }

  if (!caseData) {
    return (
      <div className="case-details error">
        <h2>Case not found</h2>
        <button onClick={() => navigate('/dashboard')}>← Back to Dashboard</button>
      </div>
    )
  }

  return (
    <div className="case-details">
      <div className="case-header">
        <button 
          onClick={() => navigate('/dashboard')} 
          className="back-btn"
        >
          ← Back to Dashboard
        </button>
        
        <div className="patient-header">
          <div className="patient-info">
            <h1>{caseData.patientName}</h1>
            <div className="patient-meta">
              <span>Age {caseData.age}</span>
              <span>•</span>
              <span>{caseData.gender}</span>
              <span>•</span>
              <span>{caseData.timeSubmitted}</span>
            </div>
          </div>
          
          <div className={`urgency-indicator ${caseData.urgencyLevel}`}>
            <div className="urgency-score">{caseData.urgencyScore}</div>
            <div className="urgency-label">{caseData.urgencyLevel.toUpperCase()}</div>
          </div>
        </div>
      </div>

      <div className="case-content">
        <div className="content-grid">
          
          {/* Left Column */}
          <div className="left-column">
            
            {/* Symptoms & Chief Complaint */}
            <div className="section">
              <h2>🩺 Chief Complaint & Symptoms</h2>
              <div className="content-card">
                <p>{caseData.symptoms}</p>
              </div>
            </div>

            {/* AI Scan Analysis */}
            <div className="section">
              <h2>🤖 AI Scan Analysis</h2>
              <div className="content-card">
                <div className="scan-header">
                  <h3>{caseData.scanType}</h3>
                  <div className="confidence">
                    <span className="confidence-label">Confidence:</span>
                    <span className="confidence-value">{caseData.scanResults.confidence}%</span>
                  </div>
                </div>
                
                <div className="findings">
                  <h4>Key Findings:</h4>
                  <ul>
                    {caseData.scanResults.findings.map((finding, index) => (
                      <li key={index}>{finding}</li>
                    ))}
                  </ul>
                </div>
                
                <div className="ai-model">
                  <small>Analysis by: {caseData.scanResults.aiModel}</small>
                </div>
              </div>
            </div>

            {/* Medical History */}
            <div className="section">
              <h2>📋 Medical History</h2>
              <div className="content-card">
                <div className="history-grid">
                  <div className="history-item">
                    <h4>Conditions</h4>
                    <ul>
                      {caseData.medicalHistory.conditions.map((condition, index) => (
                        <li key={index}>{condition}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="history-item">
                    <h4>Current Medications</h4>
                    <ul>
                      {caseData.medicalHistory.medications.map((med, index) => (
                        <li key={index}>{med}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="history-item">
                    <h4>Allergies</h4>
                    <ul>
                      {caseData.medicalHistory.allergies.map((allergy, index) => (
                        <li key={index}>{allergy}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="history-item">
                    <h4>Last Visit</h4>
                    <p>{caseData.medicalHistory.lastVisit}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="right-column">
            
            {/* Risk Factors */}
            <div className="section">
              <h2>⚠️ Risk Factors</h2>
              <div className="content-card">
                <ul className="risk-factors">
                  {caseData.riskFactors.map((risk, index) => (
                    <li key={index}>{risk}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* AI Risk Assessment */}
            <div className="section">
              <h2>📊 AI Risk Assessment</h2>
              <div className="content-card">
                <div className="risk-metrics">
                  {Object.entries(caseData.riskAssessment).map(([key, value]) => (
                    <div key={key} className="risk-metric">
                      <div className="metric-label">
                        {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                      </div>
                      <div className="metric-bar">
                        <div 
                          className="metric-fill" 
                          style={{ 
                            width: `${value}%`,
                            backgroundColor: value > 70 ? '#e74c3c' : value > 40 ? '#f39c12' : '#27ae60'
                          }}
                        ></div>
                      </div>
                      <div className="metric-value">{value}%</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Recommendations */}
            <div className="section">
              <h2>💡 AI Recommendations</h2>
              <div className="content-card">
                <div className="recommendations">
                  {caseData.recommendations.map((rec, index) => (
                    <div key={index} className={`recommendation ${rec.priority}`}>
                      <div className="rec-header">
                        <span className="rec-icon">{getPriorityIcon(rec.priority)}</span>
                        <h4 className="rec-action">{rec.action}</h4>
                      </div>
                      <p className="rec-reason">{rec.reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CaseDetails
