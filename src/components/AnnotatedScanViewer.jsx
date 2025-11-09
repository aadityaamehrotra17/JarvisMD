import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import './AnnotatedScanViewer.css'

// Separate component for handling annotated images with proper bounding box positioning
function AnnotatedImageContainer({ 
  scanImage, 
  boundingBoxes, 
  scanDimensions, 
  visibleBoxes, 
  getSeverityClass, 
  isModal = false
}) {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 })
  const imageRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    const updateImageDimensions = () => {
      if (imageRef.current) {
        const img = imageRef.current
        setImageDimensions({
          width: img.offsetWidth,
          height: img.offsetHeight
        })
      }
    }

    if (imageLoaded) {
      updateImageDimensions()
      window.addEventListener('resize', updateImageDimensions)
      return () => window.removeEventListener('resize', updateImageDimensions)
    }
  }, [imageLoaded])

  const handleImageLoad = () => {
    setImageLoaded(true)
  }

  const calculateBoxStyle = (box) => {
    if (!imageLoaded || !imageDimensions.width || !imageDimensions.height) {
      return { display: 'none' }
    }

    // Calculate scale factors based on actual image dimensions vs scan dimensions
    const scaleX = imageDimensions.width / (scanDimensions.width || imageDimensions.width)
    const scaleY = imageDimensions.height / (scanDimensions.height || imageDimensions.height)

    return {
      position: 'absolute',
      left: `${(box.x * scaleX)}px`,
      top: `${(box.y * scaleY)}px`,
      width: `${box.width * scaleX}px`,
      height: `${box.height * scaleY}px`,
    }
  }



  return (
    <div ref={containerRef} className={`${isModal ? 'simple-image-container-inner' : 'scan-image-container'}`}>
      <img 
        ref={imageRef}
        src={scanImage} 
        alt={isModal ? "Annotated Medical Scan" : "Medical Scan"} 
        className={isModal ? "simple-comparison-image" : "scan-image"}
        onLoad={handleImageLoad}
        style={{ cursor: isModal ? 'default' : 'pointer' }}
      />
      
      {/* Render bounding boxes */}
      {imageLoaded && boundingBoxes && boundingBoxes.length > 0 && boundingBoxes
        .filter(box => visibleBoxes[box.id])
        .map((box) => (
          <div
            key={box.id}
            className={`${isModal ? 'modal-bounding-box' : 'bounding-box'} ${getSeverityClass(box.severity)}`}
            style={calculateBoxStyle(box)}
            title={!isModal ? `${box.pathology}: ${(box.confidence * 100).toFixed(1)}%` : undefined}
          >
            <div className={`${isModal ? 'modal-box-label' : 'box-label'}`}>
              <span className="pathology-name">{box.pathology}</span>
              <span className="confidence">{(box.confidence * 100).toFixed(1)}%</span>
            </div>
          </div>
        ))}
    </div>
  )
}

function AnnotatedScanViewer({ scanImage, boundingBoxes = [], scanDimensions = {}, aiFindings = {} }) {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [containerDimensions, setContainerDimensions] = useState({ width: 0, height: 0 })
  const [showAnnotations, setShowAnnotations] = useState(true)
  const [visibleBoxes, setVisibleBoxes] = useState({})
  const [isImageModalOpen, setIsImageModalOpen] = useState(false)
  const imageRef = useRef(null)
  const containerRef = useRef(null)

  // Initialize all boxes as visible when boundingBoxes change
  useEffect(() => {
    if (boundingBoxes && boundingBoxes.length > 0) {
      const initialVisibility = {}
      boundingBoxes.forEach(box => {
        initialVisibility[box.id] = true
      })
      setVisibleBoxes(initialVisibility)
    }
  }, [boundingBoxes])

  useEffect(() => {
    const updateDimensions = () => {
      if (imageRef.current && containerRef.current) {
        const img = imageRef.current
        const container = containerRef.current
        
        setContainerDimensions({
          width: img.offsetWidth,
          height: img.offsetHeight,
          containerWidth: container.offsetWidth,
          containerHeight: container.offsetHeight
        })
      }
    }

    if (imageLoaded) {
      updateDimensions()
      window.addEventListener('resize', updateDimensions)
      return () => window.removeEventListener('resize', updateDimensions)
    }
  }, [imageLoaded])

  const handleImageLoad = () => {
    setImageLoaded(true)
  }

  const handleImageClick = (e) => {
    // Open modal when clicking anywhere in the scan container (image or background)
    // But don't open if clicking on a bounding box
    if (!e.target.classList.contains('bounding-box') && 
        !e.target.closest('.bounding-box')) {
      setIsImageModalOpen(true)
    }
  }

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

  const calculateBoxPosition = (box) => {
    if (!containerDimensions.width || !scanDimensions.width) return null

    // Calculate scale factors
    const scaleX = containerDimensions.width / scanDimensions.width
    const scaleY = containerDimensions.height / scanDimensions.height

    return {
      left: box.x * scaleX,
      top: box.y * scaleY,
      width: box.width * scaleX,
      height: box.height * scaleY
    }
  }

  const getSeverityClass = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'HIGH': return 'severity-high'
      case 'MODERATE': return 'severity-moderate'
      case 'MILD': return 'severity-mild'
      default: return 'severity-moderate'
    }
  }

  const toggleBoxVisibility = (boxId) => {
    setVisibleBoxes(prev => ({
      ...prev,
      [boxId]: !prev[boxId]
    }))
  }

  return (
    <div className="annotated-scan-viewer">
      {/* Toggle Controls - Only show if there are annotations */}
      {boundingBoxes && boundingBoxes.length > 0 && (
        <div className="annotation-controls">
          <div className="toggle-container">
            <button 
              className={`toggle-btn ${showAnnotations ? 'active' : ''}`}
              onClick={() => setShowAnnotations(true)}
            >
              🎯 Annotated View
            </button>
            <button 
              className={`toggle-btn ${!showAnnotations ? 'active' : ''}`}
              onClick={() => setShowAnnotations(false)}
            >
              📸 Original Scan
            </button>
          </div>
          

        </div>
      )}

      <div className="scan-container" ref={containerRef} onClick={handleImageClick} title="Click to enlarge">
        {showAnnotations ? (
          <AnnotatedImageContainer
            scanImage={scanImage}
            boundingBoxes={boundingBoxes}
            scanDimensions={scanDimensions}
            visibleBoxes={visibleBoxes}
            getSeverityClass={getSeverityClass}
            isModal={false}
          />
        ) : (
          <img 
            src={scanImage} 
            alt="Original Medical Scan" 
            className="scan-image"
          />
        )}
      </div>



      {/* Visual Findings Summary */}
      <div className="findings-summary">
        <h4>🔬 AI Findings</h4>
        <div className="findings-list">
          {boundingBoxes && boundingBoxes.length > 0 ? boundingBoxes.map((box, index) => (
            <div 
              key={box.id} 
              className={`finding-item ${!visibleBoxes[box.id] ? 'hidden-box' : ''}`}
            >
              <div 
                className="finding-main-content"
                onClick={() => toggleBoxVisibility(box.id)}
              >
                <div className="finding-info">
                  <div className="finding-name">{box.pathology}</div>
                </div>
                <div className="finding-right">
                  <span className="pin-icon">📍</span>
                  <span className={`finding-severity severity-${box.severity?.toLowerCase() || 'moderate'}`}>
                    {box.severity || 'MODERATE'}
                  </span>
                  <span className="finding-confidence">{(box.confidence * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          )) : (
            // Show AI findings when no bounding boxes exist
            aiFindings && Object.keys(aiFindings).length > 0 ? (
              Object.entries(aiFindings)
                .filter(([pathology, probability]) => pathology && probability > 0.1)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([pathology, probability], index) => (
                  <div key={index} className="finding-item">
                    <div className="finding-main-content">
                      <div className="finding-info">
                        <div className="finding-name">{pathology}</div>
                      </div>
                      <div className="finding-right">
                        <span className={`finding-severity ${probability > 0.5 ? 'severity-high' : probability > 0.3 ? 'severity-moderate' : 'severity-mild'}`}>
                          {probability > 0.5 ? 'HIGH' : probability > 0.3 ? 'MODERATE' : 'MILD'}
                        </span>
                        <span className="finding-confidence">{(probability * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                ))
            ) : (
              <div className="no-findings-message">
                No significant abnormalities detected
              </div>
            )
          )}
        </div>
      </div>

      {/* Simplified Comparison Modal - Rendered as Portal */}
      {isImageModalOpen && createPortal(
        <div className="comparison-modal-overlay" onClick={() => setIsImageModalOpen(false)}>
          <div className="simple-modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Close Button */}
            <button 
              className="simple-modal-close"
              onClick={() => setIsImageModalOpen(false)}
              title="Close (ESC)"
            >
              ✕
            </button>
            
            <div className="simple-comparison-container">
              {/* Original Scan Side */}
              <div className="simple-comparison-side">
                <div className="simple-scan-title">Original Scan</div>
                <div className="simple-image-container">
                  <img 
                    src={scanImage} 
                    alt="Original Medical Scan" 
                    className="simple-comparison-image"
                  />
                </div>
              </div>

              {/* Annotated Scan Side */}
              <div className="simple-comparison-side">
                <div className="simple-scan-title">Annotated View</div>
                <div className="simple-image-container">
                  <AnnotatedImageContainer
                    scanImage={scanImage}
                    boundingBoxes={boundingBoxes}
                    scanDimensions={scanDimensions}
                    visibleBoxes={visibleBoxes}
                    getSeverityClass={getSeverityClass}
                    isModal={true}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}

export default AnnotatedScanViewer
