import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Homepage from './components/Homepage'
import PatientInput from './components/PatientInput'
import Dashboard from './components/Dashboard'
import CaseDetails from './components/CaseDetails'
import './App.css'

function AppContent() {
  const location = useLocation()
  const isHomepage = location.pathname === '/'

  return (
    <div className="app">
      {!isHomepage && (
        <header className="app-header">
          <h1>🏥 JarvisMD - AI Emergency Analysis</h1>
        </header>
      )}
      
      <main className={isHomepage ? "app-main-full" : "app-main"}>
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/input" element={<PatientInput />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/case/:id" element={<CaseDetails />} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App
