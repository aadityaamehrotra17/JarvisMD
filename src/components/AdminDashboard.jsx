import React, { useState, useEffect } from 'react';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [requests, setRequests] = useState([]);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [viewMode, setViewMode] = useState('calendar'); // calendar, appointments, patients
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchAllData();
    
    // Auto-refresh every 10 seconds for real-time updates
    const refreshInterval = setInterval(() => {
      fetchAllData();
    }, 10000);
    
    return () => clearInterval(refreshInterval);
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      
      // Fetch appointments
      const appointmentsResponse = await fetch('http://localhost:8000/api/admin/appointments');
      const appointmentsData = await appointmentsResponse.json();
      setAppointments(appointmentsData.appointments || []);

      // Fetch patients
      const patientsResponse = await fetch('http://localhost:8000/api/admin/patients');
      const patientsData = await patientsResponse.json();
      setPatients(patientsData.patients || []);

      // Fetch requests
      const requestsResponse = await fetch('http://localhost:8000/api/admin/requests');
      const requestsData = await requestsResponse.json();
      setRequests(requestsData.requests || []);

      console.log('📊 Admin Dashboard Data Loaded:', {
        appointments: appointmentsData.appointments?.length || 0,
        patients: patientsData.patients?.length || 0,
        requests: requestsData.requests?.length || 0
      });
      
    } catch (error) {
      console.error('❌ Error fetching admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateCalendarDays = () => {
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    const days = [];
    const currentDate = new Date(startDate);
    
    for (let i = 0; i < 42; i++) { // 6 weeks
      days.push(new Date(currentDate));
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    return days;
  };

  const getAppointmentsForDate = (date) => {
    const dateStr = date.toISOString().split('T')[0];
    return appointments.filter(apt => 
      apt.appointment_datetime && apt.appointment_datetime.startsWith(dateStr)
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getUrgencyColor = (urgency) => {
    const colors = {
      'CRITICAL': '#e74c3c',
      'PRIORITY': '#f39c12', 
      'ROUTINE': '#3498db',
      'LOW_RISK': '#27ae60'
    };
    return colors[urgency] || '#95a5a6';
  };

  const openAppointmentDetails = (appointment) => {
    setSelectedAppointment(appointment);
    setShowModal(true);
  };

  const sendTestEmail = async (appointment) => {
    try {
      const userEmail = prompt("Enter your email to receive the test appointment email:", "arnav@example.com");
      if (!userEmail) return;
      
      const response = await fetch('http://localhost:8000/api/admin/send-test-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appointment_id: appointment.appointment_id,
          test_email: userEmail
        })
      });

      const result = await response.json();
      if (result.success) {
        alert('✅ Test email sent successfully!');
      } else {
        alert('❌ Failed to send email: ' + result.message);
      }
    } catch (error) {
      console.error('Email send error:', error);
      alert('❌ Error sending email');
    }
  };

  if (loading) {
    return (
      <div className="admin-dashboard loading">
        <div className="loading-spinner">🔄 Loading Admin Dashboard...</div>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <div className="header-top">
          <button 
            onClick={() => window.location.href = '/'}
            className="home-btn"
          >
            ← Home
          </button>
          <h1>🏥 JarvisMD Admin Dashboard</h1>
          <div className="last-updated">
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>
        <div className="admin-stats">
          <div className="stat-card">
            <div className="stat-number">{appointments.length}</div>
            <div className="stat-label">Total Appointments</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{patients.length}</div>
            <div className="stat-label">Patients</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{requests.length}</div>
            <div className="stat-label">Pending Requests</div>
          </div>
        </div>
      </div>

      <div className="admin-navigation">
        <button 
          className={`nav-btn ${viewMode === 'calendar' ? 'active' : ''}`}
          onClick={() => setViewMode('calendar')}
        >
          📅 Calendar View
        </button>
        <button 
          className={`nav-btn ${viewMode === 'appointments' ? 'active' : ''}`}
          onClick={() => setViewMode('appointments')}
        >
          🏥 All Appointments
        </button>
        <button 
          className={`nav-btn ${viewMode === 'patients' ? 'active' : ''}`}
          onClick={() => setViewMode('patients')}
        >
          👥 All Patients
        </button>
        <button 
          className="refresh-btn"
          onClick={fetchAllData}
        >
          🔄 Refresh Data
        </button>
      </div>

      {/* Calendar View */}
      {viewMode === 'calendar' && (
        <div className="calendar-section">
          <div className="calendar-header">
            <button 
              className="month-nav"
              onClick={() => setSelectedDate(new Date(selectedDate.setMonth(selectedDate.getMonth() - 1)))}
            >
              ←
            </button>
            <h2>{selectedDate.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}</h2>
            <button 
              className="month-nav"
              onClick={() => setSelectedDate(new Date(selectedDate.setMonth(selectedDate.getMonth() + 1)))}
            >
              →
            </button>
          </div>

          <div className="calendar-grid">
            <div className="calendar-weekdays">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                <div key={day} className="weekday">{day}</div>
              ))}
            </div>
            
            <div className="calendar-days">
              {generateCalendarDays().map((day, index) => {
                const dayAppointments = getAppointmentsForDate(day);
                const isCurrentMonth = day.getMonth() === selectedDate.getMonth();
                const isToday = day.toDateString() === new Date().toDateString();
                
                return (
                  <div 
                    key={index} 
                    className={`calendar-day ${!isCurrentMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}`}
                  >
                    <div className="day-number">{day.getDate()}</div>
                    <div className="day-appointments">
                      {dayAppointments.slice(0, 3).map((apt, aptIndex) => (
                        <div 
                          key={aptIndex}
                          className="appointment-item"
                          style={{ backgroundColor: getUrgencyColor(apt.case_urgency) }}
                          onClick={() => openAppointmentDetails(apt)}
                          title={`${apt.patient_name} - Dr. ${apt.doctor_name}`}
                        >
                          <div className="apt-time">
                            {new Date(apt.appointment_datetime).toLocaleTimeString('en-GB', { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </div>
                          <div className="apt-patient">{apt.patient_name}</div>
                        </div>
                      ))}
                      {dayAppointments.length > 3 && (
                        <div className="more-appointments">
                          +{dayAppointments.length - 3} more
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Appointments List View */}
      {viewMode === 'appointments' && (
        <div className="appointments-section">
          <h2>📋 All Appointments</h2>
          <div className="appointments-list">
            {appointments.length === 0 ? (
              <div className="no-data">No appointments found</div>
            ) : (
              appointments.map(appointment => (
                <div key={appointment.appointment_id} className="appointment-card">
                  <div className="appointment-header">
                    <div className="patient-info">
                      <h3>{appointment.patient_name}</h3>
                      <span className="appointment-id">ID: {appointment.appointment_id}</span>
                    </div>
                    <span 
                      className="urgency-badge"
                      style={{ backgroundColor: getUrgencyColor(appointment.case_urgency) }}
                    >
                      {appointment.case_urgency}
                    </span>
                  </div>
                  <div className="appointment-details">
                    <div className="detail-row">
                      <span className="label">👨‍⚕️ Doctor:</span>
                      <span className="value">Dr. {appointment.doctor_name}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">📅 Date & Time:</span>
                      <span className="value">{formatDate(appointment.appointment_datetime)}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">📋 Status:</span>
                      <span className={`status ${appointment.status}`}>{appointment.status}</span>
                    </div>
                  </div>
                  <div className="appointment-actions">
                    <button 
                      className="details-btn"
                      onClick={() => openAppointmentDetails(appointment)}
                    >
                      📖 View Details
                    </button>
                    <button 
                      className="email-btn"
                      onClick={() => sendTestEmail(appointment)}
                    >
                      📧 Send Test Email
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Patients List View */}
      {viewMode === 'patients' && (
        <div className="patients-section">
          <h2>👥 All Patients</h2>
          <div className="patients-list">
            {patients.length === 0 ? (
              <div className="no-data">No patients found</div>
            ) : (
              patients.map(patient => (
                <div key={patient.patient_id} className="patient-card">
                  <div className="patient-header">
                    <h3>{patient.patient_name}</h3>
                    <span className="patient-id">ID: {patient.patient_id}</span>
                  </div>
                  <div className="patient-details">
                    <div className="detail-row">
                      <span className="label">👤 Age:</span>
                      <span className="value">{patient.patient_age || 'N/A'}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">📧 Email:</span>
                      <span className="value">{patient.patient_email || 'N/A'}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">📞 Phone:</span>
                      <span className="value">{patient.patient_phone || 'N/A'}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">📅 Last Visit:</span>
                      <span className="value">{formatDate(patient.timestamp)}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Appointment Details Modal */}
      {showModal && selectedAppointment && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📋 Appointment Details</h2>
              <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
            </div>
            
            <div className="modal-body">
              <div className="detail-section">
                <h3>👤 Patient Information</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="label">Name:</span>
                    <span className="value">{selectedAppointment.patient_name}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Patient ID:</span>
                    <span className="value">{selectedAppointment.patient_id}</span>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3>👨‍⚕️ Doctor Information</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="label">Doctor:</span>
                    <span className="value">Dr. {selectedAppointment.doctor_name}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Doctor ID:</span>
                    <span className="value">{selectedAppointment.doctor_id}</span>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3>📅 Appointment Information</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="label">Date & Time:</span>
                    <span className="value">{formatDate(selectedAppointment.appointment_datetime)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Status:</span>
                    <span className={`status ${selectedAppointment.status}`}>{selectedAppointment.status}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Case Urgency:</span>
                    <span 
                      className="urgency-badge"
                      style={{ backgroundColor: getUrgencyColor(selectedAppointment.case_urgency) }}
                    >
                      {selectedAppointment.case_urgency}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Appointment ID:</span>
                    <span className="value">{selectedAppointment.appointment_id}</span>
                  </div>
                </div>
              </div>

              {selectedAppointment.notes && (
                <div className="detail-section">
                  <h3>📝 Notes</h3>
                  <p className="notes">{selectedAppointment.notes}</p>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button 
                className="email-btn"
                onClick={() => sendTestEmail(selectedAppointment)}
              >
                📧 Send Test Email
              </button>
              <button 
                className="close-btn"
                onClick={() => setShowModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
