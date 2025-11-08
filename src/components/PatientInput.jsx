import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './PatientInput.css'

function PatientInput() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    patientName: '',
    age: '',
    symptoms: '',
    scanFiles: []
  })
  const [dragActive, setDragActive] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleFileUpload = (files) => {
    setFormData(prev => ({
      ...prev,
      scanFiles: [...prev.scanFiles, ...Array.from(files)]
    }))
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files)
    }
  }

  const removeFile = (indexToRemove) => {
    setFormData(prev => ({
      ...prev,
      scanFiles: prev.scanFiles.filter((_, index) => index !== indexToRemove)
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    console.log('🚀 Form submitted!')
    console.log('Form validation:', {
      hasName: !!formData.patientName,
      hasAge: !!formData.age,
      hasSymptoms: !!formData.symptoms,
      hasScans: formData.scanFiles.length > 0
    })
    
    if (!formData.patientName) {
      alert('Please enter patient name')
      return
    }
    
    if (!formData.age) {
      alert('Please enter patient age')
      return
    }
    
    if (!formData.symptoms) {
      alert('Please enter symptoms')
      return
    }
    
    if (formData.scanFiles.length === 0) {
      alert('Please upload a chest X-ray scan - this is required for AI analysis')
      return
    }
    
    console.log('✅ All validation passed, starting analysis...')
    setIsAnalyzing(true)
    setAnalysisProgress(10)
    
    try {
      // Format medical history from simplified fields
      let medicalHistory = ''
      if (formData.conditionName && formData.conditionDuration) {
        medicalHistory = `${formData.conditionName} (${formData.conditionDuration} years)`
      } else if (formData.conditionName) {
        medicalHistory = formData.conditionName
      }
      
      // Prepare form data for backend API
      const apiFormData = new FormData()
      apiFormData.append('patient_name', formData.patientName)
      apiFormData.append('patient_age', formData.age)
      apiFormData.append('symptoms', formData.symptoms)
      apiFormData.append('medical_history', medicalHistory)
      apiFormData.append('scan', formData.scanFiles[0]) // Send first scan file
      
      setAnalysisProgress(30)
      
      // Call simplified backend API
      console.log('🔄 Starting analysis for:', formData.patientName)
      
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: apiFormData,
      })
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`)
      }
      
      setAnalysisProgress(80)
      const analysisResult = await response.json()
      
      // Convert uploaded scan to base64 for storage
      const scanFile = formData.scanFiles[0]
      let scanImageData = null
      
      if (scanFile) {
        try {
          const reader = new FileReader()
          scanImageData = await new Promise((resolve) => {
            reader.onload = (e) => resolve(e.target.result)
            reader.readAsDataURL(scanFile)
          })
        } catch (error) {
          console.error('Error converting image to base64:', error)
        }
      }

      // Add timestamp and scan image to the analysis result
      const timestampedResult = {
        ...analysisResult,
        time_submitted: new Date().toISOString(),
        submitted_at: new Date().toLocaleString(),
        scan_image: scanImageData,
        scan_filename: scanFile ? scanFile.name : null,
        scan_size: scanFile ? scanFile.size : null
      }
      
      // Store result in sessionStorage for dashboard access
      sessionStorage.setItem('latestAnalysis', JSON.stringify(timestampedResult))
      
      // Add to existing cases in sessionStorage
      const existingCases = JSON.parse(sessionStorage.getItem('allCases') || '[]')
      existingCases.unshift(timestampedResult) // Add to beginning of array
      sessionStorage.setItem('allCases', JSON.stringify(existingCases))
      
      setAnalysisProgress(100)
      
      // Navigate to case details page with the analysis
      console.log('🎯 Navigating to case details with:', analysisResult.patient_id)
      console.log('📦 Analysis result to pass:', analysisResult)
      
      navigate(`/case/${analysisResult.patient_id}`, { 
        state: { analysisData: analysisResult }
      })
      
    } catch (error) {
      console.error('❌ Analysis failed:', error)
      alert(`Analysis failed: ${error.message}\n\nTroubleshooting:\n1. Make sure the backend server is running\n2. Check your internet connection\n3. Verify the image file is valid`)
      
      // Don't navigate away on error - stay on the form
      setAnalysisProgress(0)
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="patient-input">
      <div className="container">
        <div className="navigation-buttons">
          <button 
            onClick={() => navigate('/')} 
            className="back-btn"
          >
            ← Back to Home
          </button>
          <button 
            onClick={() => navigate('/dashboard')} 
            className="back-btn dashboard-btn"
          >
            ← Dashboard
          </button>
        </div>
        
        <div className="page-header">
          <h2>New Patient Analysis</h2>
        </div>
        
        <form onSubmit={handleSubmit} className="patient-form">
          

          
          {/* Two Column Layout */}
          <div className="form-columns">
            
            {/* Left Column: Patient Information */}
            <div className="form-section form-column-left">
              <h3>Patient Information</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="patientName">Patient Name *</label>
                  <input
                    type="text"
                    id="patientName"
                    name="patientName"
                    value={formData.patientName}
                    onChange={handleInputChange}
                    required
                    placeholder="Enter full name"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="age">Age *</label>
                  <input
                    type="number"
                    id="age"
                    name="age"
                    value={formData.age}
                    onChange={handleInputChange}
                    required
                    placeholder="Age"
                    min="0"
                    max="150"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="symptoms">Symptoms *</label>
                <textarea
                  id="symptoms"
                  name="symptoms"
                  value={formData.symptoms}
                  onChange={handleInputChange}
                  required
                  placeholder="Describe the patient's symptoms and reason for visit..."
                  rows="4"
                />
              </div>

              {/* Medical History - Separate Box */}
              <div className="medical-history-box">
                <h4>📋 Medical History</h4>
                <div className="history-fields">
                  <div className="form-group compact">
                    <label htmlFor="conditionName">Condition Name</label>
                    <input
                      type="text"
                      id="conditionName"
                      name="conditionName"
                      value={formData.conditionName}
                      onChange={handleInputChange}
                      placeholder="e.g., Diabetes, Hypertension, Asthma..."
                    />
                  </div>
                  <div className="form-group compact">
                    <label htmlFor="conditionDuration">Years Affected</label>
                    <input
                      type="number"
                      id="conditionDuration"
                      name="conditionDuration"
                      value={formData.conditionDuration}
                      onChange={handleInputChange}
                      placeholder="Years"
                      min="0"
                      max="100"
                    />
                  </div>
                </div>
                <small className="form-hint">Enter the most relevant condition for risk assessment</small>
              </div>
            </div>

            {/* Right Column: File Upload */}
            <div className="form-section form-column-right">
            <h3>Medical Scan *</h3>
            <div 
              className={`file-upload-area ${dragActive ? 'drag-active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <div className="upload-content">
                <div className="upload-icon">📁</div>
                <p>Drag and drop medical scans here *</p>
                <p className="upload-subtext">or click to browse files (required)</p>
                <input
                  type="file"
                  multiple
                  accept=".jpg,.jpeg,.png,.dcm,.dicom"
                  onChange={(e) => handleFileUpload(e.target.files)}
                  className="file-input"
                />
              </div>
            </div>
            
            {formData.scanFiles.length > 0 && (
              <div className="uploaded-files">
                <h4>Uploaded Files ({formData.scanFiles.length})</h4>
                <div className="file-list">
                  {formData.scanFiles.map((file, index) => (
                    <div key={index} className="file-item">
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                      <button 
                        type="button" 
                        onClick={() => removeFile(index)}
                        className="remove-file"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          </div>

          {/* Analysis Progress */}
          {isAnalyzing && (
            <div className="analysis-progress">
              <div className="progress-header">
                <h3>...</h3>
                <span>{analysisProgress}%</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${analysisProgress}%` }}
                ></div>
              </div>
              <p className="progress-text">
                {analysisProgress < 30 && "Uploading scan and processing image..."}
                {analysisProgress >= 30 && analysisProgress < 80 && "Running analysis on medical scan..."}
                {analysisProgress >= 80 && "Generating diagnostic report..."}
              </p>
            </div>
          )}

          {/* Submit Button */}
          <div className="form-actions">
            <button 
              type="submit" 
              className="submit-btn"
              disabled={isAnalyzing || !formData.patientName || !formData.age || !formData.symptoms || formData.scanFiles.length === 0}
            >
              {isAnalyzing ? '🔄 Analyzing...' : 'Submit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default PatientInput
