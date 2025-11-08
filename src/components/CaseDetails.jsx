import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import './CaseDetails.css'

function CaseDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [caseData, setCaseData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [parsedReport, setParsedReport] = useState(null)
  const [parsedUrgency, setParsedUrgency] = useState(null)
  const [isImageModalOpen, setIsImageModalOpen] = useState(false)

  // Helper function to safely parse JSON from AI responses
  const parseJsonFromText = (text) => {
    try {
      if (!text || typeof text !== 'string') {
        return null
      }
      // Try to extract JSON from text that might have additional formatting
      const jsonMatch = text.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0])
      }
      return null
    } catch (error) {
      console.error('Error parsing JSON:', error)
      return null
    }
  }

  const getUrgencyLevel = (data) => {
    if (data.urgency_score >= 7) return 'critical'
    if (data.urgency_score >= 4) return 'priority'
    return 'routine'
  }

  const getUrgencyLevelText = (data) => {
    if (data.urgency_label && typeof data.urgency_label === 'string') {
      if (data.urgency_label.includes('CRITICAL')) return 'CRITICAL'
      if (data.urgency_label.includes('PRIORITY')) return 'PRIORITY'
      if (data.urgency_label.includes('ROUTINE')) return 'ROUTINE'
    }
    // Fallback to score-based assessment
    if (data.urgency_score >= 7) return 'CRITICAL'
    if (data.urgency_score >= 4) return 'PRIORITY'
    return 'ROUTINE'
  }

  // Load analysis data from route state or sessionStorage
  useEffect(() => {
    console.log('🔍 CaseDetails loading for patient ID:', id)
    console.log('📍 Location state:', location.state)
    console.log('💾 SessionStorage keys:', Object.keys(sessionStorage))
    
    let analysisData = null
    
    // First try to get from route state (direct navigation from form)
    if (location.state?.analysisData) {
      console.log('✅ Found analysis data in route state')
      analysisData = location.state.analysisData
    } else {
      console.log('⚠️ No data in route state, searching for case by ID...')
      
      // Search for the specific case by ID in allCases
      const storedCases = sessionStorage.getItem('allCases')
      if (storedCases) {
        try {
          const allCases = JSON.parse(storedCases)
          console.log('📚 All stored cases:', allCases.map(c => ({ id: c.patient_id, name: c.patient_name })))
          
          // Find the case with matching patient_id
          analysisData = allCases.find(caseItem => caseItem.patient_id === id)
          
          if (analysisData) {
            console.log('✅ Found matching case for ID:', id, 'Patient:', analysisData.patient_name)
          } else {
            console.log('❌ No case found with ID:', id)
            console.log('Available IDs:', allCases.map(c => c.patient_id))
          }
        } catch (error) {
          console.error('❌ Error parsing stored cases:', error)
        }
      }
      
      // Fallback to latestAnalysis if no specific case found
      if (!analysisData) {
        console.log('⚠️ Falling back to latestAnalysis...')
        const storedAnalysis = sessionStorage.getItem('latestAnalysis')
        if (storedAnalysis) {
          try {
            analysisData = JSON.parse(storedAnalysis)
            console.log('✅ Found latest analysis as fallback')
          } catch (error) {
            console.error('❌ Error parsing stored analysis:', error)
          }
        }
      }
    }
    
    if (analysisData) {
      console.log('🎯 Setting case data:', analysisData)
      setCaseData(analysisData)
      
      // Parse the structured report and urgency assessment
      const report = parseJsonFromText(analysisData.structured_report)
      const urgency = parseJsonFromText(analysisData.urgency_level)
      
      console.log('📊 Parsed report:', report)
      console.log('🚨 Parsed urgency:', urgency)
      
      setParsedReport(report)
      setParsedUrgency(urgency)
    } else {
      console.log('❌ No analysis data found for patient ID:', id)
      // No fallback to mock data - let the error state handle it
    }
    
    setLoading(false)
  }, [id, location.state])

  // Handle ESC key for closing modal
  useEffect(() => {
    const handleEscKey = (event) => {
      if (event.key === 'Escape' && isImageModalOpen) {
        setIsImageModalOpen(false)
      }
    }

    if (isImageModalOpen) {
      document.addEventListener('keydown', handleEscKey)
      document.body.style.overflow = 'hidden' // Prevent background scrolling
    }

    return () => {
      document.removeEventListener('keydown', handleEscKey)
      document.body.style.overflow = 'unset' // Restore scrolling
    }
  }, [isImageModalOpen])

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
        <p>Patient ID: {id}</p>
        <p>Location state: {location.state ? 'Present' : 'Missing'}</p>
        <p>SessionStorage: {sessionStorage.getItem('latestAnalysis') ? 'Present' : 'Missing'}</p>
        <button onClick={() => navigate('/dashboard')}>← Back to Dashboard</button>
        <button onClick={() => navigate('/input')}>← Back to Input</button>
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
            <h1>{caseData.patient_name || caseData.patient_info?.name || 'Unknown Patient'}</h1>
            <div className="patient-meta">
              <span>Age {caseData.patient_age || caseData.patient_info?.age || 'N/A'}</span>
              <span>•</span>
              <span>{caseData.timestamp ? new Date(caseData.timestamp).toLocaleString() : 'Unknown time'}</span>
            </div>
            <div className="patient-id">
              ID: {caseData.patient_id || 'N/A'}
            </div>
          </div>
        </div>
        
        <div className={`urgency-indicator-separate ${getUrgencyLevel(caseData)}`}>
          <div className="urgency-score">{caseData.urgency_score?.toFixed(1) || 'N/A'}</div>
          <div className="urgency-label">{getUrgencyLevelText(caseData)}</div>
        </div>
      </div>

      <div className="case-content">
        <div className="content-grid">
          
          {/* Left Column - Patient & Clinical Info */}
          <div className="left-column">
            
            {/* Patient Summary */}
            <div className="section compact">
              <h3>🩺 Symptoms</h3>
              <div className="content-card small">
                <p>{caseData.symptoms || caseData.patient_info?.symptoms}</p>
              </div>
            </div>

            {/* Clinical Summary from AI */}
            {parsedReport && (
              <div className="section compact">
                <h3>📋 Clinical Assessment</h3>
                <div className="content-card small">
                  <div className="clinical-summary">
                    <div className="summary-item">
                      <strong>Findings:</strong> {parsedReport.findings_summary}
                    </div>
                    {parsedReport.risk_assessment && (
                      <div className="summary-item risk-assessment-item">
                        <strong>Risk Assessment:</strong>
                        <div className="risk-assessment-content">
                          {(() => {
                            // Try to extract risk level (HIGH, MODERATE, LOW) from the text
                            const riskText = parsedReport.risk_assessment;
                            const riskLevelMatch = riskText.match(/(HIGH|MODERATE|LOW|CRITICAL|PRIORITY|ROUTINE)/i);
                            const riskLevel = riskLevelMatch ? riskLevelMatch[0].toUpperCase() : null;
                            
                            if (riskLevel) {
                              // Remove the risk level from the description
                              const description = riskText.replace(new RegExp(`\\b${riskLevel}\\b`, 'gi'), '').trim();
                              return (
                                <>
                                  <div className={`risk-level-badge-inline ${riskLevel.toLowerCase()}`}>
                                    {riskLevel} RISK
                                  </div>
                                  <div className="risk-description">
                                    {description.replace(/^[:\-\s]+/, '')}
                                  </div>
                                </>
                              );
                            }
                            // Fallback to original text if no risk level found
                            return <div className="risk-description">{riskText}</div>;
                          })()}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

          </div>

          {/* Right Column - Medical Scan */}
          <div className="right-column">
            
            {/* Medical Scan Display */}
            <div className="section compact">
              <h3>📸 Medical Scan</h3>
              <div className="content-card small">
                {caseData.scan_image ? (
                  <div className="scan-display">
                    <img 
                      src={caseData.scan_image} 
                      alt="Medical Scan" 
                      className="medical-scan-image"
                      onClick={() => setIsImageModalOpen(true)}
                      title="Click to enlarge"
                    />
                  </div>
                ) : (
                  <div className="no-scan">No scan image available</div>
                )}
              </div>
            </div>

            {/* AI Pathology Detection - Compact Version */}
            <div className="section compact">
              <h3>🔬 Pathology Detection</h3>
              <div className="content-card small">
                
                {/* Top 5 Findings Only */}
                <div className="pathology-compact">
                  {caseData.ai_findings && Object.keys(caseData.ai_findings).length > 0 ? (
                    Object.entries(caseData.ai_findings)
                      .filter(([pathology, probability]) => pathology && probability > 0.1)
                      .sort(([,a], [,b]) => b - a)
                      .slice(0, 5) // Only show top 5
                      .map(([pathology, probability], index) => (
                        <div key={index} className="pathology-row">
                          <span className="pathology-name">{pathology}</span>
                          <div className="pathology-right">
                            <div className="pathology-mini-bar">
                              <div 
                                className="pathology-mini-fill"
                                style={{ 
                                  width: `${probability * 100}%`,
                                  backgroundColor: probability > 0.5 ? '#ef4444' : probability > 0.3 ? '#f59e0b' : '#10b981'
                                }}
                              />
                            </div>
                            <span className="pathology-percent">{(probability * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      ))
                  ) : (
                    <div className="no-findings">No significant findings detected</div>
                  )}
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* Image Modal */}
      {isImageModalOpen && caseData?.scan_image && (
        <div className="image-modal-overlay" onClick={() => setIsImageModalOpen(false)}>
          <div className="image-modal-content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="image-modal-close"
              onClick={() => setIsImageModalOpen(false)}
              title="Close (ESC)"
            >
              ✕
            </button>
            <img 
              src={caseData.scan_image} 
              alt="Medical Scan - Enlarged View" 
              className="image-modal-img"
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default CaseDetails
