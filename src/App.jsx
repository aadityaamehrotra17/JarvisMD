import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Homepage from './components/Homepage'
import PatientInput from './components/PatientInput'
import Dashboard from './components/Dashboard'
import CaseDetails from './components/CaseDetails'
import AdminDashboard from './components/AdminDashboard'
import logo from './assets/logo.png'
import './App.css'

function AppContent() {
  const location = useLocation()
  const isHomepage = location.pathname === '/'

  return (
    <div className="app">
      {!isHomepage && (
        <header className="app-header">
          <h1>
            <img src={logo} alt="JarvisMD Logo" className="header-logo" />
            JarvisMD
          </h1>
        </header>
      )}
      
      <main className={isHomepage ? "app-main-full" : "app-main"}>
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/input" element={<PatientInput />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/case/:id" element={<CaseDetails />} />
          <Route path="/admin" element={<AdminDashboard />} />
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
