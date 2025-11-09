"""
Enhanced Multi-Agent System with Real-time Progress Tracking
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict, Annotated
from dataclasses import dataclass
import operator
import asyncio

# LangGraph imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Local imports
from scheduling_storage import SchedulingStorage

# Simplified Manchester doctors data - directly embedded
DOCTORS_DATABASE = {
    "dr_james_hartwell": {
        "id": "dr_james_hartwell",
        "name": "Dr. James Hartwell",
        "specialty": "Cardiologist", 
        "email": "j.hartwell@manchesterheart.nhs.uk",
        "phone": "+44-161-276-1234",
        "hospital": "Manchester Royal Infirmary",
        "expertise": ["Heart Failure", "Cardiomegaly", "Arrhythmia"],
        "experience_years": 18,
        "rating": 4.9,
        "seniority": "Consultant"
    },
    "dr_sarah_mitchell": {
        "id": "dr_sarah_mitchell", 
        "name": "Dr. Sarah Mitchell",
        "specialty": "Cardiologist",
        "email": "s.mitchell@wythenshawe.nhs.uk",
        "phone": "+44-161-291-2345",
        "hospital": "Wythenshawe Hospital",
        "expertise": ["Interventional Cardiology", "Cardiomegaly"],
        "experience_years": 22,
        "rating": 4.8,
        "seniority": "Senior Consultant"
    },
    "dr_lisa_patel": {
        "id": "dr_lisa_patel",
        "name": "Dr. Lisa Patel",
        "specialty": "Pulmonologist",
        "email": "l.patel@cmft.nhs.uk", 
        "phone": "+44-161-276-6789",
        "hospital": "Manchester Royal Infirmary",
        "expertise": ["Pneumonia", "COPD", "Lung Cancer"],
        "experience_years": 15,
        "rating": 4.8,
        "seniority": "Consultant"
    },
    "dr_david_wilson": {
        "id": "dr_david_wilson",
        "name": "Dr. David Wilson", 
        "specialty": "Pulmonologist",
        "email": "d.wilson@wythenshawe.nhs.uk",
        "phone": "+44-161-291-7890",
        "hospital": "Wythenshawe Hospital",
        "expertise": ["Lung Transplant", "Pneumonia"],
        "experience_years": 20,
        "rating": 4.9,
        "seniority": "Senior Consultant"
    },
    "dr_karen_white": {
        "id": "dr_karen_white",
        "name": "Dr. Karen White",
        "specialty": "Emergency Medicine",
        "email": "k.white@cmft.nhs.uk",
        "phone": "+44-161-276-0123", 
        "hospital": "Manchester Royal Infirmary",
        "expertise": ["Trauma", "Critical Care"],
        "experience_years": 17,
        "rating": 4.8,
        "seniority": "Consultant"
    },
    "dr_mark_davis": {
        "id": "dr_mark_davis",
        "name": "Dr. Mark Davis",
        "specialty": "Emergency Medicine",
        "email": "m.davis@wythenshawe.nhs.uk",
        "phone": "+44-161-291-1234",
        "hospital": "Wythenshawe Hospital", 
        "expertise": ["Emergency Surgery", "Critical Care"],
        "experience_years": 19,
        "rating": 4.9,
        "seniority": "Senior Consultant"
    }
}

# Simple helper functions
def get_recommended_specialists(ml_results, urgency_score, patient_info):
    """Get recommended doctors based on ML findings"""
    recommended = []
    
    # Find relevant specialties
    findings = {k: v for k, v in ml_results.items() if v > 0.3}
    
    for doctor_id, doctor in DOCTORS_DATABASE.items():
        specialty = doctor["specialty"]
        
        # Match cardiologists for heart issues
        if "Cardiomegaly" in findings and "Cardiologist" in specialty:
            doctor["match_score"] = 0.9
            recommended.append(doctor)
        
        # Match pulmonologists for lung issues  
        elif any(lung in findings for lung in ["Pneumonia", "Edema", "Atelectasis"]) and "Pulmonologist" in specialty:
            doctor["match_score"] = 0.8
            recommended.append(doctor)
        
        # Emergency doctors for high urgency
        elif urgency_score >= 7 and "Emergency" in specialty:
            doctor["match_score"] = 0.85
            recommended.append(doctor)
    
    # Sort by match score and return top 3
    recommended.sort(key=lambda x: x["match_score"], reverse=True)
    return recommended[:3]

def get_doctor_info(doctor_id):
    """Get doctor information by ID"""
    return DOCTORS_DATABASE.get(doctor_id)

def get_available_slots(doctor_id, days_ahead=14):
    """Get mock available slots"""
    slots = []
    today = datetime.now()
    
    for i in range(1, 4):  # Next 3 days
        date = today + timedelta(days=i)
        slots.append({
            "date": date.strftime("%Y-%m-%d"),
            "time": "09:00",
            "datetime": f"{date.strftime('%Y-%m-%d')}T09:00:00"
        })
        slots.append({
            "date": date.strftime("%Y-%m-%d"),
            "time": "14:00", 
            "datetime": f"{date.strftime('%Y-%m-%d')}T14:00:00"
        })
    
    return slots

# State Management
class AgentState(TypedDict):
    """State shared across all agents in the workflow"""
    # Input data
    patient_info: Dict
    symptoms: str
    ml_results: Dict
    urgency_score: float
    session_id: str
    
    # Processing state
    case_classification: str
    recommended_doctors: List[Dict]
    selected_doctors: List[Dict]
    appointment_requests: List[Dict]
    doctor_responses: List[Dict]
    final_appointment: Optional[Dict]
    health_recommendations: Optional[Dict]
    
    # Messages and logs
    messages: Annotated[List[BaseMessage], operator.add]
    workflow_log: Annotated[List[str], operator.add]
    
    # Current step
    current_agent: str
    next_action: str

# Initialize LLM
def get_llm():
    """Get configured LLM instance"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=api_key,
        temperature=0.1
    )

class ProgressAwareAgent:
    """Base class for agents with progress tracking"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.progress_manager = None
    
    def set_progress_manager(self, manager):
        """Set the progress manager for this agent"""
        self.progress_manager = manager
    
    async def update_progress(self, session_id: str, status: str, message: str, data: Dict = None):
        """Update progress for this agent"""
        if self.progress_manager:
            await self.progress_manager.update_step_progress(
                session_id, self.agent_name, status, message, data
            )
        else:
            print(f"[{self.agent_name}] {status}: {message}")

class CaseTriageAgent(ProgressAwareAgent):
    """Agent responsible for triaging cases based on ML results and symptoms"""
    
    def __init__(self):
        super().__init__("triage")
        self.llm = get_llm()
        
    async def __call__(self, state: AgentState) -> AgentState:
        """Triage the case and classify urgency"""
        
        session_id = state.get('session_id', 'unknown')
        await self.update_progress(session_id, "running", "Analyzing case severity and classification...")
        
        # Analyze case using LLM
        triage_prompt = f"""
        You are an experienced emergency physician triaging a patient case.
        
        Patient Information:
        - Age: {state['patient_info'].get('age', 'Unknown')}
        - Symptoms: {state['symptoms']}
        
        ML Analysis Results:
        {json.dumps(state['ml_results'], indent=2)}
        
        Urgency Score (0-10): {state['urgency_score']}
        
        Based on this information, classify the case into one of these categories:
        - CRITICAL: Requires immediate senior doctor attention (urgency >= 8)
        - PRIORITY: Needs specialist consultation within 24-48 hours (urgency 5-7)
        - ROUTINE: Standard follow-up care needed (urgency 3-4)
        - LOW_RISK: Minimal intervention, lifestyle recommendations only (urgency < 3)
        
        Respond with JSON format:
        {{
            "classification": "CRITICAL|PRIORITY|ROUTINE|LOW_RISK",
            "reasoning": "Brief explanation of classification"
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=triage_prompt)])
            triage_result = json.loads(response.content)
            classification = triage_result["classification"]
            reasoning = triage_result.get("reasoning", "AI-based classification")
        except:
            # Fallback classification based on urgency score
            if state['urgency_score'] >= 8:
                classification = "CRITICAL"
            elif state['urgency_score'] >= 5:
                classification = "PRIORITY"
            elif state['urgency_score'] >= 3:
                classification = "ROUTINE"
            else:
                classification = "LOW_RISK"
            
            reasoning = f"Automated classification based on urgency score {state['urgency_score']}"
        
        # Update state
        state['case_classification'] = classification
        state['workflow_log'].append(f"Case classified as: {classification}")
        state['messages'].append(AIMessage(content=f"Case triaged as {classification}: {reasoning}"))
        
        # Determine next action based on classification - ONLY CRITICAL cases get appointments
        if classification == "CRITICAL":
            state['next_action'] = "doctor_matching"
            state['current_agent'] = "doctor_matcher"
        else:
            # All non-critical cases get health recommendations instead of appointments
            state['next_action'] = "health_recommendations"
            state['current_agent'] = "health_advisor"
        
        await self.update_progress(session_id, "completed", f"Case classified as {classification}", {
            "classification": classification,
            "reasoning": reasoning,
            "next_action": state['next_action']
        })
        
        return state

class DoctorMatchingAgent(ProgressAwareAgent):
    """Agent that finds and ranks suitable doctors based on case requirements"""
    
    def __init__(self):
        super().__init__("doctor_matching")
        self.llm = get_llm()
        
    async def __call__(self, state: AgentState) -> AgentState:
        """Find suitable doctors for the case"""
        
        session_id = state.get('session_id', 'unknown')
        await self.update_progress(session_id, "running", "Finding suitable specialists...")
        
        # Get doctor recommendations based on ML results
        recommended_doctors = get_recommended_specialists(
            state['ml_results'],
            state['urgency_score'],
            state['patient_info']
        )
        
        await self.update_progress(session_id, "running", f"Found {len(recommended_doctors)} potential specialists")
        
        # Filter doctors based on classification
        if state['case_classification'] == "CRITICAL":
            filtered_doctors = [
                doc for doc in recommended_doctors 
                if doc.get('experience_years', 0) >= 10 and doc.get('rating', 0) >= 4.7
            ]
        elif state['case_classification'] == "PRIORITY":
            filtered_doctors = [
                doc for doc in recommended_doctors 
                if doc.get('rating', 0) >= 4.5
            ]
        else:
            filtered_doctors = recommended_doctors
        
        # Get full doctor details with availability
        selected_doctors = []
        for doctor in filtered_doctors[:3]:  # Top 3
            doctor_info = get_doctor_info(doctor['id'])
            if doctor_info:
                available_slots = get_available_slots(doctor['id'], days_ahead=14)
                doctor_info['available_slots'] = available_slots[:5]
                selected_doctors.append(doctor_info)
        
        # Update state
        state['recommended_doctors'] = recommended_doctors
        state['selected_doctors'] = selected_doctors
        state['workflow_log'].append(f"Selected {len(selected_doctors)} doctors for outreach")
        state['messages'].append(AIMessage(content=f"Found {len(selected_doctors)} suitable doctors"))
        
        state['next_action'] = "appointment_coordination"
        state['current_agent'] = "appointment_coordinator"
        
        await self.update_progress(session_id, "completed", f"Selected {len(selected_doctors)} doctors for consultation", {
            "selected_doctors": [{"name": doc['name'], "specialty": doc['specialty']} for doc in selected_doctors]
        })
        
        return state

class AppointmentCoordinatorAgent(ProgressAwareAgent):
    """Agent that handles appointment scheduling and calendar management"""
    
    def __init__(self):
        super().__init__("appointment_coordination")
        self.storage = SchedulingStorage()
        
    async def __call__(self, state: AgentState) -> AgentState:
        """Coordinate appointments with selected doctors"""
        
        session_id = state.get('session_id', 'unknown')
        await self.update_progress(session_id, "running", "Sending appointment requests to doctors...")
        
        appointment_requests = []
        
        for i, doctor in enumerate(state['selected_doctors']):
            await self.update_progress(session_id, "running", f"Contacting Dr. {doctor['name']} ({i+1}/{len(state['selected_doctors'])})")
            
            # Generate personalized email content
            email_content = self._generate_appointment_email(
                doctor, state['patient_info'], state['symptoms'], 
                state['ml_results'], state['case_classification']
            )
            
            # Create appointment request
            request = {
                "request_id": str(uuid.uuid4())[:8],
                "doctor_id": doctor['id'],
                "doctor_name": doctor['name'],
                "doctor_email": doctor['email'],
                "patient_id": state['patient_info'].get('patient_id', 'unknown'),
                "urgency_level": state['case_classification'],
                "preferred_slots": doctor.get('available_slots', [])[:3],
                "email_content": email_content,
                "status": "sent",
                "sent_at": datetime.now().isoformat()
            }
            
            # Send actual email
            email_sent = await self._send_appointment_request(request, session_id)
            
            appointment_requests.append(request)
            
            # Save to persistent storage
            self.storage.save_pending_request(
                request, 
                state['patient_info'].get('patient_id', 'unknown')
            )
            
            # Brief delay for realistic timing
            await asyncio.sleep(0.5)
        
        # Update state
        state['appointment_requests'] = appointment_requests
        state['workflow_log'].append(f"Sent appointment requests to {len(appointment_requests)} doctors")
        state['messages'].append(AIMessage(content=f"Appointment requests sent to {len(appointment_requests)} doctors"))
        
        state['next_action'] = "doctor_response_simulation"
        state['current_agent'] = "doctor_simulator"
        
        await self.update_progress(session_id, "completed", f"Sent requests to {len(appointment_requests)} doctors", {
            "requests_sent": len(appointment_requests),
            "doctors_contacted": [req['doctor_name'] for req in appointment_requests]
        })
        
        return state

    def _generate_appointment_email(self, doctor: Dict, patient_info: Dict, 
                                  symptoms: str, ml_results: Dict, urgency: str) -> str:
        """Generate personalized appointment request email"""
        
        # Create a professional email template
        subject = f"🏥 JarvisMD Appointment Request - {urgency} Case"
        
        # Get key ML findings (those with confidence > 0.5)
        key_findings = [k for k, v in ml_results.items() if v > 0.5]
        findings_str = ", ".join(key_findings) if key_findings else "Pending analysis"
        
        # Format appointment slots
        slots_info = []
        preferred_slots = doctor.get('available_slots', doctor.get('available_dates', []))[:3]
        for slot in preferred_slots:
            date_str = slot.get('date', 'TBD')
            time_str = slot.get('time', 'TBD')
            slots_info.append(f"• {date_str} at {time_str}")
        
        slots_text = "\n".join(slots_info) if slots_info else "• Please suggest available times"
        
        body = f"""Subject: {subject}

Dear Dr. {doctor['name']},

I hope this message finds you well. We have an urgent medical case that requires your expertise in {doctor['specialty']}.

PATIENT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Patient: {patient_info.get('name', 'Patient')} 
• Age: {patient_info.get('age', 'Not specified')}
• Case Priority: {urgency}
• Primary Symptoms: {symptoms}
• Key ML Findings: {findings_str}

REQUESTED APPOINTMENT SLOTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{slots_text}

This case has been classified as {urgency} based on our AI-powered medical assessment. Your expertise in {doctor['specialty']} makes you an ideal specialist for this consultation.

Please confirm your availability for any of the suggested time slots, or propose alternative times that work better for your schedule.

CONTACT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Patient Contact: {patient_info.get('phone', 'Available upon request')}
• JarvisMD Coordination: automated-system@jarvismd.com
• Request ID: {uuid.uuid4().hex[:8].upper()}

Thank you for your dedication to patient care. We look forward to your prompt response.

Best regards,
JarvisMD Healthcare Coordination System
Automated Medical Scheduling Platform

---
This is an automated message from JarvisMD's AI-powered healthcare coordination system.
For technical issues, please contact: support@jarvismd.com
"""
        return body
    
    async def _send_appointment_request(self, request: Dict, session_id: str) -> bool:
        """Send appointment request email using SMTP"""
        try:
            import smtplib
            import os
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            await self.update_progress(session_id, "running", f"📤 Sending email to Dr. {request['doctor_name']}")
            
            # Email configuration
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME", "jarvismd@example.com")
            smtp_password = os.getenv("SMTP_PASSWORD", "your-app-password")
            
            # For testing: Send all emails to your Gmail address
            test_email = "sahil2023saxena@gmail.com"  # Your email for testing
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = test_email  # Send to your email instead of doctor's
            msg['Subject'] = f"🏥 JarvisMD Appointment Request - {request['urgency_level']} Case"
            
            # Email body
            body = request['email_content']
            msg.attach(MIMEText(body, 'plain'))
            
            try:
                # Attempt to send real email
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_username, smtp_password)
                
                text = msg.as_string()
                server.sendmail(smtp_username, test_email, text)
                server.quit()
                
                await self.update_progress(session_id, "running", f"✅ Email sent successfully to {test_email}")
                return True
                
            except Exception as smtp_error:
                await self.update_progress(session_id, "running", f"📧 Email simulation mode (SMTP unavailable)")
                
                # Fallback to detailed simulation logging
                await self.update_progress(session_id, "running", f"📤 SIMULATED EMAIL SEND:")
                await self.update_progress(session_id, "running", f"   To: {test_email}")
                await self.update_progress(session_id, "running", f"   Subject: Appointment Request - {request['urgency_level']} Case")
                await self.update_progress(session_id, "running", f"   Doctor: Dr. {request['doctor_name']}")
                await self.update_progress(session_id, "running", f"   Request ID: {request['request_id']}")
                
                # Log email content for verification
                preview = body[:200] + "..." if len(body) > 200 else body
                await self.update_progress(session_id, "running", f"   Preview: {preview}")
                
                return True
                
        except Exception as e:
            await self.update_progress(session_id, "running", f"❌ Email error: {str(e)}")
            return False

class DoctorResponseSimulatorAgent(ProgressAwareAgent):
    """Agent that simulates doctor responses for testing"""
    
    def __init__(self):
        super().__init__("doctor_simulation")
        
    async def __call__(self, state: AgentState) -> AgentState:
        """Simulate doctor responses to appointment requests"""
        
        session_id = state.get('session_id', 'unknown')
        await self.update_progress(session_id, "running", "Waiting for doctor responses...")
        
        doctor_responses = []
        confirmed_appointment = None
        
        for i, request in enumerate(state['appointment_requests']):
            doctor_name = request['doctor_name']
            
            await self.update_progress(session_id, "running", f"Processing response from Dr. {doctor_name}")
            
            # Simulate response time
            await asyncio.sleep(1)
            
            # Higher urgency cases get higher acceptance rate
            urgency_multiplier = {
                "CRITICAL": 0.95,
                "PRIORITY": 0.8,
                "ROUTINE": 0.6
            }.get(state['case_classification'], 0.7)
            
            import random
            will_accept = random.random() < urgency_multiplier
            
            if will_accept and not confirmed_appointment:
                # Accept with a specific slot
                available_slots = request.get('preferred_slots', [])
                if available_slots:
                    selected_slot = available_slots[0]
                    
                    response = {
                        "request_id": request['request_id'],
                        "doctor_id": request['doctor_id'],
                        "doctor_name": doctor_name,
                        "response": "ACCEPT",
                        "confirmed_slot": selected_slot,
                        "response_time": datetime.now().isoformat(),
                        "notes": f"Available for {state['case_classification']} case"
                    }
                    
                    # Create confirmed appointment
                    confirmed_appointment = {
                        "appointment_id": f"APPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "doctor_id": request['doctor_id'],
                        "doctor_name": doctor_name,
                        "patient_id": state['patient_info'].get('patient_id', 'unknown'),
                        "patient_name": state['patient_info'].get('name', 'Patient'),
                        "appointment_datetime": selected_slot.get('datetime'),
                        "case_urgency": state['case_classification'],
                        "status": "confirmed",
                        "created_at": datetime.now().isoformat()
                    }
                    
                    await self.update_progress(session_id, "running", f"✅ Dr. {doctor_name} ACCEPTED appointment!")
                else:
                    response = {
                        "request_id": request['request_id'],
                        "doctor_id": request['doctor_id'],
                        "response": "DECLINE",
                        "reason": "No suitable slots available",
                        "response_time": datetime.now().isoformat()
                    }
                    await self.update_progress(session_id, "running", f"❌ Dr. {doctor_name} declined - no slots available")
            else:
                response = {
                    "request_id": request['request_id'],
                    "doctor_id": request['doctor_id'],
                    "response": "DECLINE",
                    "reason": "Schedule conflict" if confirmed_appointment else "Not available for this case type",
                    "response_time": datetime.now().isoformat()
                }
                await self.update_progress(session_id, "running", f"❌ Dr. {doctor_name} declined")
            
            doctor_responses.append(response)
        
        # Update state
        state['doctor_responses'] = doctor_responses
        state['final_appointment'] = confirmed_appointment
        
        if confirmed_appointment:
            state['workflow_log'].append(f"Appointment confirmed with Dr. {confirmed_appointment['doctor_name']}")
            state['messages'].append(AIMessage(content=f"Appointment confirmed with Dr. {confirmed_appointment['doctor_name']}"))
            state['next_action'] = "calendar_integration"
            state['current_agent'] = "calendar_manager"
            
            await self.update_progress(session_id, "completed", f"Appointment confirmed with Dr. {confirmed_appointment['doctor_name']}", {
                "confirmed_appointment": confirmed_appointment
            })
        else:
            state['workflow_log'].append("No doctors accepted - need alternative action")
            state['messages'].append(AIMessage(content="No appointments confirmed - escalating case"))
            state['next_action'] = "escalation"
            state['current_agent'] = "case_escalator"
            
            await self.update_progress(session_id, "completed", "No appointments confirmed - case needs escalation")
        
        return state

class CalendarIntegrationAgent(ProgressAwareAgent):
    """Agent that handles calendar integration and appointment management"""
    
    def __init__(self):
        super().__init__("calendar_integration")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """Integrate appointment into calendar system"""
        
        session_id = state.get('session_id', 'unknown')
        await self.update_progress(session_id, "running", "Creating calendar entries...")
        
        appointment = state['final_appointment']
        if not appointment:
            state['next_action'] = "complete"
            return state
        
        # Simulate calendar integration
        await asyncio.sleep(1)
        
        # Create calendar event (simulated)
        calendar_event = {
            "event_id": f"EVT_{appointment['appointment_id']}",
            "title": f"Patient Consultation - {appointment['patient_name']}",
            "description": f"Case: {state['case_classification']}\nSymptoms: {state['symptoms']}",
            "start_time": appointment['appointment_datetime'],
            "duration_minutes": 30,
            "attendees": [
                appointment.get('doctor_email', f"{appointment['doctor_id']}@hospital.com"),
                state['patient_info'].get('email', 'patient@example.com')
            ],
            "location": "Hospital - Consultation Room",
            "created_at": datetime.now().isoformat()
        }
        
        # Save appointment to storage
        storage = SchedulingStorage()
        storage.save_confirmed_appointment(
            appointment, 
            state['patient_info'].get('patient_id', 'unknown')
        )
        
        state['workflow_log'].append(f"Calendar event created: {calendar_event['event_id']}")
        state['messages'].append(AIMessage(content="Calendar integration completed"))
        state['next_action'] = "complete"
        
        await self.update_progress(session_id, "completed", f"Calendar event created for {appointment['appointment_datetime']}", {
            "calendar_event": calendar_event
        })
        
        return state

class HealthAdvisorAgent(ProgressAwareAgent):
    """Agent that provides health recommendations for low-risk cases"""
    
    def __init__(self):
        super().__init__("health_recommendations")
        self.llm = get_llm()
        
    async def __call__(self, state: AgentState) -> AgentState:
        """Generate personalized health recommendations using AI"""
        
        session_id = state.get('session_id', 'unknown')
        classification = state.get('case_classification', 'ROUTINE')
        
        if classification == "PRIORITY":
            await self.update_progress(session_id, "running", "PRIORITY case - Generating specialist consultation recommendations...")
        elif classification == "ROUTINE":
            await self.update_progress(session_id, "running", "ROUTINE case - Generating preventive care recommendations...")
        else:
            await self.update_progress(session_id, "running", "LOW_RISK case - Generating lifestyle recommendations...")
        
        # Generate AI-powered health recommendations
        health_prompt = f"""
        You are a preventive health advisor providing personalized recommendations.
        
        Patient Information:
        - Age: {state['patient_info'].get('age', 'Unknown')}
        - Symptoms: {state['symptoms']}
        - Case Classification: {classification}
        - Urgency Score: {state['urgency_score']}/10
        
        ML Analysis Results:
        {json.dumps(state['ml_results'], indent=2)}
        
        Based on this {classification} case, provide:
        
        {"For PRIORITY cases: When to seek immediate medical attention, specialist referral recommendations, and monitoring guidelines." if classification == "PRIORITY" else ""}
        {"For ROUTINE cases: General wellness recommendations, preventive measures, and follow-up timeline." if classification == "ROUTINE" else ""}
        {"For LOW_RISK cases: Lifestyle modifications, self-care measures, and wellness tips." if classification == "LOW_RISK" else ""}
        
        Format as JSON:
        {{
            "classification_message": "Clear explanation of why this is a {classification} case",
            "immediate_actions": ["action1", "action2"],
            "lifestyle_recommendations": {{
                "diet": ["specific dietary advice"],
                "exercise": ["specific exercise recommendations"],  
                "sleep": ["sleep hygiene recommendations"]
            }},
            "monitoring_guidelines": ["what symptoms to monitor"],
            "when_to_seek_help": ["red flag symptoms requiring immediate attention"],
            "follow_up_timeline": "specific timeline for follow-up",
            "educational_resources": ["relevant health information sources"],
            "summary": "Concise summary of key recommendations"
        }}
        
        Keep recommendations evidence-based, age-appropriate, and specific to the symptoms presented.
        Do NOT provide specific medical diagnoses. Focus on preventive care and wellness.
        """
        
        try:
            # Simulate AI processing time
            await asyncio.sleep(2)
            
            await self.update_progress(session_id, "running", "Consulting AI health advisor...")
            
            response = self.llm.invoke([HumanMessage(content=health_prompt)])
            health_recommendations = json.loads(response.content)
            
            await self.update_progress(session_id, "running", "AI recommendations generated successfully!")
            
        except Exception as e:
            await self.update_progress(session_id, "running", f"AI generation failed, using fallback recommendations...")
            
            # Fallback recommendations based on classification
            if classification == "PRIORITY":
                health_recommendations = {
                    "classification_message": f"This is a PRIORITY case (urgency {state['urgency_score']}/10) requiring specialist consultation within 24-48 hours.",
                    "immediate_actions": ["Contact your GP within 24 hours", "Monitor symptoms closely", "Keep a symptom diary"],
                    "lifestyle_recommendations": {
                        "diet": ["Maintain current diet, avoid any known triggers", "Stay well hydrated"],
                        "exercise": ["Light activity only until medical consultation", "Avoid strenuous exercise"],
                        "sleep": ["Ensure adequate rest", "Sleep with head elevated if respiratory symptoms"]
                    },
                    "monitoring_guidelines": ["Watch for worsening symptoms", "Monitor vital signs if possible", "Note any new symptoms"],
                    "when_to_seek_help": ["If symptoms worsen significantly", "New chest pain or breathing difficulties", "Persistent high fever"],
                    "follow_up_timeline": "Specialist consultation recommended within 24-48 hours",
                    "educational_resources": ["NHS 111 for urgent advice", "Local GP practice", "Hospital emergency services if critical"],
                    "summary": "Monitor closely and seek specialist medical attention within 1-2 days due to concerning findings."
                }
            elif classification == "ROUTINE":
                health_recommendations = {
                    "classification_message": f"This is a ROUTINE case (urgency {state['urgency_score']}/10) requiring standard follow-up care.",
                    "immediate_actions": ["Schedule routine GP appointment", "Continue current medications", "Monitor symptoms"],
                    "lifestyle_recommendations": {
                        "diet": ["Balanced diet rich in fruits and vegetables", "Limit processed foods and excess salt"],
                        "exercise": ["Regular moderate exercise 150 min/week", "Include both cardio and strength training"],
                        "sleep": ["7-9 hours of quality sleep nightly", "Consistent sleep schedule"]
                    },
                    "monitoring_guidelines": ["Track symptoms weekly", "Note any changes or patterns"],
                    "when_to_seek_help": ["If symptoms persist beyond 2 weeks", "Any sudden worsening", "New concerning symptoms"],
                    "follow_up_timeline": "Routine GP appointment within 2-4 weeks",
                    "educational_resources": ["NHS health information", "Patient.info", "Local health centers"],
                    "summary": "Maintain healthy lifestyle and schedule routine follow-up with your GP."
                }
            else:  # LOW_RISK
                health_recommendations = {
                    "classification_message": f"This is a LOW_RISK case (urgency {state['urgency_score']}/10) with minimal concern. Focus on wellness and prevention.",
                    "immediate_actions": ["No immediate medical action needed", "Continue healthy lifestyle habits", "Self-monitor symptoms"],
                    "lifestyle_recommendations": {
                        "diet": ["Mediterranean-style diet with plenty of fruits and vegetables", "Stay well hydrated with water"],
                        "exercise": ["Regular physical activity - aim for 30 minutes daily", "Mix of cardio, strength, and flexibility exercises"],
                        "sleep": ["Prioritize 7-9 hours of quality sleep", "Create a relaxing bedtime routine"]
                    },
                    "monitoring_guidelines": ["Self-monitor symptoms as needed", "General wellness check-ins"],
                    "when_to_seek_help": ["Only if symptoms worsen significantly", "Development of new concerning symptoms"],
                    "follow_up_timeline": "Routine health screening as per age guidelines",
                    "educational_resources": ["NHS Choices", "Wellness apps", "Local fitness and nutrition resources"],
                    "summary": "Focus on maintaining healthy lifestyle habits. No immediate medical intervention required."
                }
        
        # Add case-specific information
        health_recommendations['case_details'] = {
            "classification": classification,
            "urgency_score": state['urgency_score'],
            "primary_concerns": [k for k, v in state['ml_results'].items() if v > 0.3],
            "patient_age": state['patient_info'].get('age', 'Unknown')
        }
        
        state['health_recommendations'] = health_recommendations
        state['workflow_log'].append(f"Health recommendations generated for {classification} case")
        state['messages'].append(AIMessage(content=f"Personalized health recommendations provided for {classification} case"))
        state['next_action'] = "complete"
        
        # Different completion messages based on classification
        if classification == "PRIORITY":
            completion_msg = "PRIORITY case: Specialist consultation recommended within 24-48 hours"
        elif classification == "ROUTINE": 
            completion_msg = "ROUTINE case: Schedule follow-up with your GP within 2-4 weeks"
        else:
            completion_msg = "LOW_RISK case: Focus on healthy lifestyle, no immediate medical intervention needed"
        
        await self.update_progress(session_id, "completed", completion_msg, {
            "recommendations": health_recommendations,
            "classification": classification,
            "next_steps": health_recommendations.get('immediate_actions', [])
        })
        
        return state

class EnhancedMultiAgentWorkflow:
    """Enhanced Multi-Agent workflow with real-time progress tracking"""
    
    def __init__(self, progress_manager=None):
        self.progress_manager = progress_manager
        self.graph = self._create_workflow_graph()
        
    def _create_workflow_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        
        # Initialize agents
        triage_agent = CaseTriageAgent()
        doctor_matcher = DoctorMatchingAgent()
        appointment_coordinator = AppointmentCoordinatorAgent()
        doctor_simulator = DoctorResponseSimulatorAgent()
        calendar_manager = CalendarIntegrationAgent()
        health_advisor = HealthAdvisorAgent()
        
        # Set progress manager for all agents
        if self.progress_manager:
            for agent in [triage_agent, doctor_matcher, appointment_coordinator, 
                         doctor_simulator, calendar_manager, health_advisor]:
                agent.set_progress_manager(self.progress_manager)
        
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("case_triage", triage_agent)
        workflow.add_node("doctor_matching", doctor_matcher)
        workflow.add_node("appointment_coordination", appointment_coordinator)
        workflow.add_node("doctor_simulation", doctor_simulator)
        workflow.add_node("calendar_integration", calendar_manager)
        workflow.add_node("health_recommendations", health_advisor)
        
        # Define workflow edges
        workflow.set_entry_point("case_triage")
        
        # Conditional routing from triage
        workflow.add_conditional_edges(
            "case_triage",
            self._route_after_triage,
            {
                "doctor_matching": "doctor_matching",
                "health_recommendations": "health_recommendations"
            }
        )
        
        # Medical pathway edges
        workflow.add_edge("doctor_matching", "appointment_coordination")
        workflow.add_edge("appointment_coordination", "doctor_simulation")
        
        # Conditional routing after doctor responses
        workflow.add_conditional_edges(
            "doctor_simulation",
            self._route_after_responses,
            {
                "calendar_integration": "calendar_integration",
                "escalation": END
            }
        )
        
        # End nodes
        workflow.add_edge("calendar_integration", END)
        workflow.add_edge("health_recommendations", END)
        
        return workflow.compile()
    
    def _route_after_triage(self, state: AgentState) -> str:
        """Route based on triage classification"""
        classification = state.get('case_classification', 'ROUTINE')
        if classification in ["CRITICAL", "PRIORITY", "ROUTINE"]:
            return "doctor_matching"
        else:
            return "health_recommendations"
    
    def _route_after_responses(self, state: AgentState) -> str:
        """Route based on doctor responses"""
        if state.get('final_appointment'):
            return "calendar_integration"
        else:
            return "escalation"
    
    async def process_case_with_progress(self, patient_info: Dict, symptoms: str, 
                                       ml_results: Dict, urgency_score: float, session_id: str) -> Dict:
        """Process a complete case through the multi-agent workflow with progress tracking"""
        
        if self.progress_manager:
            # Initialize workflow session
            self.progress_manager.start_workflow(session_id, patient_info)
            await self.progress_manager.update_step_progress(
                session_id, "initializing", "running", "Starting multi-agent workflow..."
            )
        
        try:
            # Initialize state
            initial_state = {
                "patient_info": patient_info,
                "symptoms": symptoms,
                "ml_results": ml_results,
                "urgency_score": urgency_score,
                "session_id": session_id,
                "case_classification": "",
                "recommended_doctors": [],
                "selected_doctors": [],
                "appointment_requests": [],
                "doctor_responses": [],
                "final_appointment": None,
                "health_recommendations": None,
                "messages": [],
                "workflow_log": [],
                "current_agent": "case_triage",
                "next_action": "triage"
            }
            
            # Run workflow
            result = await self.graph.ainvoke(initial_state)
            
            if self.progress_manager:
                await self.progress_manager.complete_workflow(session_id, result)
            
            return result
            
        except Exception as e:
            if self.progress_manager:
                await self.progress_manager.workflow_error(session_id, str(e))
            raise e
