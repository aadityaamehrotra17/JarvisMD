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
    
    // Here you'll send data to your teammate's backend
    console.log('Submitting patient data:', formData)
    
    // For now, navigate to dashboard (you can add loading state here)
    navigate('/dashboard')
  }

  return (
    <div className="patient-input">
      <div className="container">
        <button 
          onClick={() => navigate('/')} 
          className="back-btn"
        >
          ← Back to Home
        </button>
        
        <div className="page-header">
          <h2>New Patient Analysis</h2>
          <p className="subtitle">Upload medical scans and enter patient information for AI analysis</p>
        </div>
        
        <form onSubmit={handleSubmit} className="patient-form">
          
          {/* Patient Information */}
          <div className="form-section">
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
                  placeholder="Enter patient's full name"
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
              <label htmlFor="symptoms">Symptoms & Chief Complaint *</label>
              <textarea
                id="symptoms"
                name="symptoms"
                value={formData.symptoms}
                onChange={handleInputChange}
                required
                placeholder="Describe the patient's symptoms, complaints, and relevant medical history..."
                rows="4"
              />
            </div>
          </div>

          {/* File Upload */}
          <div className="form-section">
            <h3>Medical Scans</h3>
            <div 
              className={`file-upload-area ${dragActive ? 'drag-active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <div className="upload-content">
                <div className="upload-icon">📁</div>
                <p>Drag and drop medical scans here</p>
                <p className="upload-subtext">or click to browse files</p>
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

          {/* Submit Button */}
          <div className="form-actions">
            <button 
              onClick={() => navigate('/dashboard')}
              type="button" 
              className="secondary-btn"
            >
              📊 View Dashboard
            </button>
            <button 
              type="submit" 
              className="submit-btn"
              disabled={!formData.patientName || !formData.age || !formData.symptoms}
            >
              🔍 Analyze with AI
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default PatientInput
