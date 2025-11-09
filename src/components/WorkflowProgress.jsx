import React, { useState, useEffect, useRef } from 'react';
import './WorkflowProgress.css';

const WorkflowProgress = ({ sessionId, isVisible, onClose }) => {
  const [workflowState, setWorkflowState] = useState({
    status: 'idle',
    current_step: null,
    completed_steps: [],
    progress_percentage: 0,
    messages: [],
    agent_activities: [], // New: Track individual agent activities
    current_agent: null, // New: Current active agent
    workflow_steps: [
      { id: 'triage', name: 'Case Triage', status: 'pending', agent: 'CaseTriageAgent' },
      { id: 'doctor_matching', name: 'Doctor Matching', status: 'pending', agent: 'DoctorMatchingAgent' },
      { id: 'appointment_coordination', name: 'Appointment Coordination', status: 'pending', agent: 'AppointmentCoordinatorAgent' },
      { id: 'doctor_simulation', name: 'Doctor Response Simulation', status: 'pending', agent: 'DoctorResponseSimulatorAgent' },
      { id: 'calendar_integration', name: 'Calendar Integration', status: 'pending', agent: 'CalendarIntegrationAgent' },
      { id: 'health_recommendations', name: 'Health Recommendations', status: 'pending', agent: 'HealthAdvisorAgent' }
    ]
  });

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [activeTab, setActiveTab] = useState('progress'); // New: Tab state for different views
  const websocket = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [workflowState.messages]);

  useEffect(() => {
    if (!sessionId || !isVisible) return;

    // Connect to WebSocket
    const connectWebSocket = () => {
      try {
        const wsUrl = `ws://localhost:8000/ws/${sessionId}`;
        websocket.current = new WebSocket(wsUrl);

        websocket.current.onopen = () => {
          console.log('🔌 Connected to workflow progress WebSocket');
          setIsConnected(true);
          setConnectionError(null);
          
          // Send ping to get initial status
          websocket.current.send(JSON.stringify({ type: 'get_status' }));
        };

        websocket.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'progress_update') {
              setWorkflowState(prevState => {
                const newState = {
                  ...prevState,
                  ...data.data,
                };

                // Add new messages
                if (data.data.message) {
                  newState.messages = [...prevState.messages, {
                    ...data.data.message,
                    timestamp: new Date().toLocaleTimeString()
                  }];
                }

                // Track agent activities
                if (data.data.current_agent || data.data.agent_activity) {
                  const activity = {
                    id: Date.now(),
                    timestamp: new Date().toLocaleTimeString(),
                    agent: data.data.current_agent || data.data.agent_activity?.agent,
                    action: data.data.agent_activity?.action || data.data.message?.content || 'Processing...',
                    status: data.data.agent_activity?.status || 'running',
                    details: data.data.agent_activity?.details || null
                  };

                  newState.agent_activities = [...prevState.agent_activities, activity];
                  newState.current_agent = data.data.current_agent;
                }

                // Update workflow steps status
                if (data.data.current_step) {
                  newState.workflow_steps = prevState.workflow_steps.map(step => {
                    if (step.id === data.data.current_step) {
                      return { ...step, status: 'running' };
                    } else if (prevState.completed_steps?.includes(step.id)) {
                      return { ...step, status: 'completed' };
                    }
                    return step;
                  });
                }

                return newState;
              });
            } else if (data.type === 'session_update') {
              setWorkflowState(prevState => ({
                ...prevState,
                ...data.data
              }));
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        websocket.current.onclose = () => {
          console.log('🔌 WebSocket connection closed');
          setIsConnected(false);
        };

        websocket.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionError('Connection failed');
          setIsConnected(false);
        };

      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setConnectionError('Failed to establish connection');
      }
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (websocket.current) {
        websocket.current.close();
      }
    };
  }, [sessionId, isVisible]);

  const getStepIcon = (step) => {
    switch (step.status) {
      case 'completed':
        return <div className="step-icon completed">✓</div>;
      case 'running':
        return <div className="step-icon running">⟳</div>;
      case 'error':
        return <div className="step-icon error">✗</div>;
      default:
        return <div className="step-icon pending">○</div>;
    }
  };

  const getStepDescription = (step) => {
    const descriptions = {
      triage: 'Analyzing case severity and classification',
      doctor_matching: 'Finding suitable specialists based on findings',
      appointment_coordination: 'Sending requests to available doctors',
      doctor_simulation: 'Processing doctor responses and confirmations',
      calendar_integration: 'Creating calendar events and finalizing appointments',
      health_recommendations: 'Generating personalized health recommendations'
    };
    return descriptions[step.id] || step.name;
  };

  const getAgentIcon = (agentName) => {
    const icons = {
      'CaseTriageAgent': '🏥',
      'DoctorMatchingAgent': '👨‍⚕️',
      'AppointmentCoordinatorAgent': '📅',
      'DoctorResponseSimulatorAgent': '🤖',
      'CalendarIntegrationAgent': '🗓️',
      'HealthAdvisorAgent': '🏃‍♂️'
    };
    return icons[agentName] || '🔍';
  };

  const getStatusColor = (status) => {
    const colors = {
      'running': '#3498db',
      'completed': '#27ae60',
      'error': '#e74c3c',
      'pending': '#95a5a6',
      'success': '#27ae60'
    };
    return colors[status] || '#95a5a6';
  };

  const formatAgentActivity = (activity) => {
    // Extract key information from agent activities
    if (activity.action.includes('classified as')) {
      return `🏥 Case classified: ${activity.action.split('classified as: ')[1]}`;
    }
    if (activity.action.includes('Selected') && activity.action.includes('doctors')) {
      return `👨‍⚕️ Found specialists for consultation`;
    }
    if (activity.action.includes('Sent appointment requests')) {
      return `📅 Appointment requests sent to doctors`;
    }
    if (activity.action.includes('ACCEPTED') || activity.action.includes('confirmed')) {
      return `✅ Appointment confirmed with doctor`;
    }
    if (activity.action.includes('Calendar integration')) {
      return `🗓️ Calendar event created successfully`;
    }
    return activity.action;
  };

  if (!isVisible) return null;

  return (
    <div className="workflow-progress-overlay">
      <div className="workflow-progress-modal">
        <div className="progress-header">
          <h2>🤖 AI Multi-Agent System</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="connection-status">
          {isConnected ? (
            <div className="status connected">
              <span className="status-dot connected"></span>
              Connected to workflow system
              {workflowState.current_agent && (
                <span className="current-agent">
                  {getAgentIcon(workflowState.current_agent)} {workflowState.current_agent}
                </span>
              )}
            </div>
          ) : (
            <div className="status disconnected">
              <span className="status-dot disconnected"></span>
              {connectionError || 'Connecting...'}
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button 
            className={`tab ${activeTab === 'progress' ? 'active' : ''}`}
            onClick={() => setActiveTab('progress')}
          >
            📊 Progress Overview
          </button>
          <button 
            className={`tab ${activeTab === 'agents' ? 'active' : ''}`}
            onClick={() => setActiveTab('agents')}
          >
            🤖 Agent Activity
          </button>
          <button 
            className={`tab ${activeTab === 'messages' ? 'active' : ''}`}
            onClick={() => setActiveTab('messages')}
          >
            💬 Live Messages
          </button>
        </div>

        {/* Progress Overview Tab */}
        {activeTab === 'progress' && (
          <>
            <div className="progress-bar-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${workflowState.progress_percentage}%` }}
                ></div>
              </div>
              <div className="progress-text">
                {workflowState.progress_percentage}% Complete
              </div>
            </div>

            <div className="workflow-steps">
              <h3>Workflow Steps</h3>
              {workflowState.workflow_steps.map((step, index) => (
                <div 
                  key={step.id} 
                  className={`workflow-step ${step.status} ${workflowState.current_step === step.id ? 'active' : ''}`}
                >
                  <div className="step-number">{index + 1}</div>
                  {getStepIcon(step)}
                  <div className="step-content">
                    <div className="step-name">
                      {getAgentIcon(step.agent)} {step.name}
                    </div>
                    <div className="step-description">{getStepDescription(step)}</div>
                    {step.data && (
                      <div className="step-data">
                        {step.data.classification && (
                          <span className="data-tag">{step.data.classification}</span>
                        )}
                        {step.data.selected_doctors && (
                          <span className="data-tag">
                            {step.data.selected_doctors.length} doctors contacted
                          </span>
                        )}
                        {step.data.confirmed_appointment && (
                          <span className="data-tag success">
                            Appointment confirmed!
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Agent Activity Tab */}
        {activeTab === 'agents' && (
          <div className="agent-activities">
            <h3>🤖 AI Agent Activities</h3>
            <div className="activities-container">
              {workflowState.agent_activities.length === 0 ? (
                <div className="no-activities">
                  <div className="waiting-animation">🔄</div>
                  <p>Waiting for AI agents to start processing...</p>
                </div>
              ) : (
                workflowState.agent_activities.map((activity, index) => (
                  <div key={activity.id} className={`activity-item ${activity.status}`}>
                    <div className="activity-header">
                      <div className="activity-agent">
                        {getAgentIcon(activity.agent)} 
                        <strong>{activity.agent}</strong>
                      </div>
                      <div className="activity-time">{activity.timestamp}</div>
                    </div>
                    <div className="activity-content">
                      <div className="activity-action">
                        {formatAgentActivity(activity)}
                      </div>
                      {activity.details && (
                        <div className="activity-details">
                          {typeof activity.details === 'object' ? 
                            JSON.stringify(activity.details, null, 2) : 
                            activity.details
                          }
                        </div>
                      )}
                      <div className="activity-status" style={{ color: getStatusColor(activity.status) }}>
                        {activity.status === 'running' && '⟳ Processing...'}
                        {activity.status === 'completed' && '✓ Completed'}
                        {activity.status === 'error' && '✗ Error'}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Live Messages Tab */}
        {activeTab === 'messages' && (
          <div className="messages-section">
            <h3>💬 Live System Messages</h3>
            <div className="messages-container">
              {workflowState.messages.length === 0 ? (
                <div className="no-messages">
                  <div className="waiting-animation">📡</div>
                  <p>Waiting for workflow updates...</p>
                </div>
              ) : (
                workflowState.messages.map((message, index) => (
                  <div key={index} className="message">
                    <div className="message-header">
                      <span className="message-time">
                        {message.timestamp || new Date().toLocaleTimeString()}
                      </span>
                      {message.agent && (
                        <span className="message-agent">
                          {getAgentIcon(message.agent)} {message.agent}
                        </span>
                      )}
                    </div>
                    <div className="message-content">
                      {typeof message === 'object' ? message.content || message.text : message}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        {workflowState.status === 'completed' && (
          <div className="completion-summary">
            <h3>🎉 Workflow Completed!</h3>
            {workflowState.final_result?.final_appointment ? (
              <div className="appointment-success">
                <p>✅ Appointment scheduled with Dr. {workflowState.final_result.final_appointment.doctor_name}</p>
                <p>📅 {new Date(workflowState.final_result.final_appointment.appointment_datetime).toLocaleString()}</p>
              </div>
            ) : workflowState.final_result?.health_recommendations ? (
              <div className="health-recommendations">
                <p>📋 Personalized health recommendations provided</p>
                <p>This case was classified as low-risk</p>
              </div>
            ) : (
              <div className="workflow-complete">
                <p>Workflow processing completed</p>
              </div>
            )}
          </div>
        )}

        {workflowState.status === 'error' && (
          <div className="error-summary">
            <h3>⚠️ Workflow Error</h3>
            <p>An error occurred during processing. Please try again.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowProgress;
