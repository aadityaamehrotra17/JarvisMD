"""
JarvisMD Multi-Agent System using LangGraph
Healthcare Workflow Automation with ML + AI Agents
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict, Annotated
from dataclasses import dataclass
import operator

# LangGraph imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Local imports
from scheduling_storage import SchedulingStorage
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    from datetime import datetime, timedelta
    
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
    
    # Processing state
    case_classification: str  # CRITICAL, PRIORITY, ROUTINE, LOW_RISK
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

@dataclass
class MockDoctor:
    """Mock doctor for testing responses"""
    id: str
    name: str
    specialty: str
    email: str
    response_likelihood: float  # 0.0 to 1.0
    response_delay_hours: int

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

class CaseTriageAgent:
    """Agent responsible for triaging cases based on ML results and symptoms"""
    
    def __init__(self):
        self.llm = get_llm()
        
    def __call__(self, state: AgentState) -> AgentState:
        """Triage the case and classify urgency"""
        
        print("\n" + "="*60)
        print("🏥 CASE TRIAGE AGENT: Starting case analysis...")
        print("="*60)
        
        # Print input data for verification
        print(f"📋 INPUT DATA:")
        print(f"   Patient: {state['patient_info'].get('name', 'Unknown')} (Age: {state['patient_info'].get('age', 'Unknown')})")
        print(f"   Symptoms: {state['symptoms']}")
        print(f"   Urgency Score: {state['urgency_score']}/10")
        print(f"   ML Findings: {list(state['ml_results'].keys())}")
        
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
            "reasoning": "Brief explanation of classification",
            "required_specialties": ["specialty1", "specialty2"],
            "estimated_consultation_time": 30,
            "follow_up_needed": true|false
        }}
        """
        
        print(f"🤖 CALLING AI MODEL...")
        response = self.llm.invoke([HumanMessage(content=triage_prompt)])
        print(f"✅ AI RESPONSE RECEIVED!")
        
        try:
            triage_result = json.loads(response.content)
            classification = triage_result["classification"]
            print(f"📊 AI ANALYSIS SUCCESS:")
            print(f"   Raw Response: {response.content[:200]}...")
            print(f"   Classification: {classification}")
            print(f"   Reasoning: {triage_result.get('reasoning', 'N/A')}")
        except Exception as e:
            print(f"❌ AI RESPONSE PARSING FAILED: {e}")
            print(f"   Raw Response: {response.content}")
            
            # Fallback classification based on urgency score
            if state['urgency_score'] >= 8:
                classification = "CRITICAL"
            elif state['urgency_score'] >= 5:
                classification = "PRIORITY"
            elif state['urgency_score'] >= 3:
                classification = "ROUTINE"
            else:
                classification = "LOW_RISK"
            
            triage_result = {
                "classification": classification,
                "reasoning": f"Automated classification based on urgency score {state['urgency_score']}",
                "required_specialties": ["General Medicine"],
                "estimated_consultation_time": 30,
                "follow_up_needed": True
            }
            print(f"🔄 FALLBACK CLASSIFICATION: {classification}")
        
        # Update state
        state['case_classification'] = classification
        state['workflow_log'].append(f"Case classified as: {classification}")
        state['messages'].append(AIMessage(content=f"Case triaged as {classification}: {triage_result['reasoning']}"))
        
        # Determine next action based on classification
        if classification in ["CRITICAL", "PRIORITY", "ROUTINE"]:
            state['next_action'] = "doctor_matching"
            state['current_agent'] = "doctor_matcher"
        else:
            state['next_action'] = "health_recommendations"
            state['current_agent'] = "health_advisor"
            
        print(f"\n🎯 TRIAGE RESULTS:")
        print(f"   ✅ Final Classification: {classification}")
        print(f"   📋 Next Action: {state['next_action']}")
        print(f"   🤖 Next Agent: {state['current_agent']}")
        print("="*60)
        
        return state

class DoctorMatchingAgent:
    """Agent that finds and ranks suitable doctors based on case requirements"""
    
    def __init__(self):
        self.llm = get_llm()
        
    def __call__(self, state: AgentState) -> AgentState:
        """Find suitable doctors for the case"""
        
        print("\n" + "="*60)
        print("👨‍⚕️ DOCTOR MATCHING AGENT: Finding suitable specialists...")
        print("="*60)
        
        print(f"🔍 SEARCHING CRITERIA:")
        print(f"   Case Type: {state['case_classification']}")
        print(f"   ML Findings: {[k for k, v in state['ml_results'].items() if v > 0.3]}")
        print(f"   Urgency Level: {state['urgency_score']}/10")
        
        # Get doctor recommendations based on ML results
        print(f"🏥 SCANNING DOCTOR DATABASE...")
        recommended_doctors = get_recommended_specialists(
            state['ml_results'],
            state['urgency_score'],
            state['patient_info']
        )
        print(f"   Found {len(recommended_doctors)} potential specialists")
        for doc in recommended_doctors:
            print(f"     - Dr. {doc['name']} ({doc['specialty']}) - Match Score: {doc.get('match_score', 'N/A')}")
        
        # Filter doctors based on classification
        print(f"\n🔧 APPLYING FILTERS FOR {state['case_classification']} CASE...")
        if state['case_classification'] == "CRITICAL":
            # For critical cases, prefer senior doctors and immediate availability
            filtered_doctors = [
                doc for doc in recommended_doctors 
                if doc.get('experience_years', 0) >= 10 and doc.get('rating', 0) >= 4.7
            ]
            print(f"   Critical case filters: Experience ≥10 years, Rating ≥4.7")
        elif state['case_classification'] == "PRIORITY":
            # For priority cases, need good availability within 48 hours
            filtered_doctors = [
                doc for doc in recommended_doctors 
                if doc.get('rating', 0) >= 4.5
            ]
            print(f"   Priority case filters: Rating ≥4.5")
        else:
            # Routine cases can use any qualified doctor
            filtered_doctors = recommended_doctors
            print(f"   Routine case: All qualified doctors eligible")
        
        print(f"   ✅ {len(filtered_doctors)} doctors passed filters")
        
        # Rank doctors using AI
        print(f"\n🤖 AI RANKING DOCTORS...")
        ranking_prompt = f"""
        You are a medical coordinator ranking doctors for a {state['case_classification']} case.
        
        Case Details:
        - Patient Age: {state['patient_info'].get('age', 'Unknown')}
        - Symptoms: {state['symptoms']}
        - ML Findings: {list(state['ml_results'].keys())}
        - Urgency: {state['urgency_score']}/10
        
        Available Doctors:
        {json.dumps([{
            'id': doc['id'],
            'name': doc['name'],
            'specialty': doc['specialty'],
            'experience': doc.get('experience_years', 0),
            'rating': doc.get('rating', 0),
            'expertise': doc.get('expertise', [])
        } for doc in filtered_doctors[:6]], indent=2)}
        
        Rank the top 3 doctors best suited for this case. Consider:
        1. Specialty match with symptoms/ML findings
        2. Experience level appropriate for urgency
        3. Expertise in relevant areas
        
        Return JSON with ranked list:
        {{
            "selected_doctors": [
                {{"doctor_id": "dr_id", "match_score": 0.95, "reasoning": "why selected"}},
                {{"doctor_id": "dr_id", "match_score": 0.87, "reasoning": "why selected"}},
                {{"doctor_id": "dr_id", "match_score": 0.82, "reasoning": "why selected"}}
            ]
        }}
        """
        
        response = self.llm.invoke([HumanMessage(content=ranking_prompt)])
        
        try:
            ranking_result = json.loads(response.content)
            selected_doctor_ids = [doc["doctor_id"] for doc in ranking_result["selected_doctors"]]
            print(f"   ✅ AI ranking successful!")
            for i, doc_info in enumerate(ranking_result["selected_doctors"]):
                print(f"     {i+1}. {doc_info['doctor_id']} - Score: {doc_info['match_score']} - {doc_info['reasoning']}")
        except Exception as e:
            print(f"   ❌ AI ranking failed: {e}")
            print(f"   🔄 Using fallback ranking by rating + experience...")
            # Fallback: select top 3 by rating and experience
            sorted_docs = sorted(filtered_doctors, 
                               key=lambda x: (x.get('rating', 0) + x.get('experience_years', 0)/20), 
                               reverse=True)
            selected_doctor_ids = [doc['id'] for doc in sorted_docs[:3]]
            for i, doc in enumerate(sorted_docs[:3]):
                print(f"     {i+1}. Dr. {doc['name']} - Rating: {doc.get('rating', 'N/A')} - Experience: {doc.get('experience_years', 'N/A')} years")
        
        # Get full doctor details
        print(f"\n📋 PREPARING DOCTOR PROFILES...")
        selected_doctors = []
        for doc_id in selected_doctor_ids:
            doctor_info = get_doctor_info(doc_id)
            if doctor_info:
                # Add availability information
                available_slots = get_available_slots(doc_id, days_ahead=14)
                doctor_info['available_slots'] = available_slots[:5]  # Next 5 slots
                selected_doctors.append(doctor_info)
                print(f"   ✅ Dr. {doctor_info['name']} - {len(available_slots)} available slots")
        
        # Update state
        state['recommended_doctors'] = filtered_doctors
        state['selected_doctors'] = selected_doctors
        state['workflow_log'].append(f"Selected {len(selected_doctors)} doctors for outreach")
        state['messages'].append(AIMessage(content=f"Found {len(selected_doctors)} suitable doctors"))
        
        state['next_action'] = "appointment_coordination"
        state['current_agent'] = "appointment_coordinator"
        
        print(f"\n🎯 DOCTOR MATCHING RESULTS:")
        print(f"   ✅ Selected {len(selected_doctors)} top doctors for contact:")
        for i, doc in enumerate(selected_doctors):
            print(f"     {i+1}. Dr. {doc['name']} ({doc['specialty']}) - {doc['hospital']}")
            print(f"        Rating: {doc.get('rating', 'N/A')} | Experience: {doc.get('experience_years', 'N/A')} years")
        print(f"   📋 Next Action: {state['next_action']}")
        print("="*60)
        
        return state

class AppointmentCoordinatorAgent:
    """Agent that handles appointment scheduling and calendar management"""
    
    def __init__(self):
        self.llm = get_llm()
        self.storage = SchedulingStorage()
        
    def __call__(self, state: AgentState) -> AgentState:
        """Coordinate appointments with selected doctors"""
        
        print("\n" + "="*60)
        print("📅 APPOINTMENT COORDINATOR: Sending appointment requests...")
        print("="*60)
        
        print(f"📧 PREPARING EMAIL REQUESTS:")
        print(f"   Patient: {state['patient_info'].get('name', 'Unknown')}")
        print(f"   Urgency: {state['case_classification']}")
        print(f"   Target Doctors: {len(state['selected_doctors'])}")
        
        appointment_requests = []
        
        for i, doctor in enumerate(state['selected_doctors'], 1):
            print(f"\n🔄 PROCESSING DOCTOR {i}/{len(state['selected_doctors'])}: Dr. {doctor['name']}")
            
            # Generate personalized email request
            print(f"   📝 Generating personalized email...")
            email_content = self._generate_appointment_email(
                doctor, state['patient_info'], state['symptoms'], 
                state['ml_results'], state['case_classification']
            )
            print(f"   ✅ Email generated ({len(email_content)} characters)")
            
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
            
            print(f"   📋 Request ID: {request['request_id']}")
            print(f"   📧 Target Email: {doctor['email']}")
            print(f"   📅 Preferred Slots: {len(request['preferred_slots'])}")
            for slot in request['preferred_slots']:
                print(f"      - {slot.get('date', 'N/A')} at {slot.get('time', 'N/A')}")
            
            # Simulate sending email
            print(f"   🚀 Sending email...")
            email_sent = self._send_appointment_request(request)
            if email_sent:
                print(f"   ✅ Email sent successfully to Dr. {doctor['name']}")
            else:
                print(f"   ❌ Failed to send email to Dr. {doctor['name']}")
            
            appointment_requests.append(request)
            
            # Save to persistent storage
            print(f"   💾 Saving to persistent storage...")
            try:
                file_path = self.storage.save_pending_request(
                    request, 
                    state['patient_info'].get('patient_id', 'unknown')
                )
                print(f"   ✅ Saved to: {file_path}")
            except Exception as e:
                print(f"   ❌ Storage failed: {e}")
        
        # Update state
        state['appointment_requests'] = appointment_requests
        state['workflow_log'].append(f"Sent appointment requests to {len(appointment_requests)} doctors")
        state['messages'].append(AIMessage(content=f"Appointment requests sent to {len(appointment_requests)} doctors"))
        
        state['next_action'] = "doctor_response_simulation"
        state['current_agent'] = "doctor_simulator"
        
        print(f"\n🎯 APPOINTMENT COORDINATION RESULTS:")
        print(f"   ✅ Total Requests Sent: {len(appointment_requests)}")
        print(f"   📁 Data Storage Location: /Users/arnav/Documents/JarvisMD/scheduling_data/requests/")
        print(f"   📋 Next Action: {state['next_action']}")
        print("="*60)
        
        return state
    
    def _generate_appointment_email(self, doctor: Dict, patient_info: Dict, 
                                  symptoms: str, ml_results: Dict, urgency: str) -> str:
        """Generate personalized appointment request email"""
        
        email_prompt = f"""
        Generate a professional appointment request email from a medical coordination system.
        
        Doctor: Dr. {doctor['name']} ({doctor['specialty']})
        Patient: {patient_info.get('name', 'Patient')} (Age: {patient_info.get('age', 'Unknown')})
        Case Urgency: {urgency}
        Symptoms: {symptoms}
        Key ML Findings: {', '.join([k for k, v in ml_results.items() if v > 0.5])}
        
        The email should:
        1. Be professional and concise
        2. Include relevant clinical information
        3. Indicate urgency level appropriately
        4. Request available appointment slots
        5. Include patient contact information
        
        Format as a proper email with subject and body.
        """
        
        try:
            print(f"      🤖 Calling AI for email generation...")
            response = self.llm.invoke([HumanMessage(content=email_prompt)])
            print(f"      ✅ AI email generation successful!")
            
            # Show preview of generated email
            email_preview = response.content[:150] + "..." if len(response.content) > 150 else response.content
            print(f"      📧 Email Preview: {email_preview}")
            
            return response.content
        except Exception as e:
            print(f"      ❌ AI email generation failed: {e}")
            # Fallback email
            fallback_email = f"""
Subject: Urgent Appointment Request - {patient_info.get('name', 'Patient')} ({urgency} Case)

Dear Dr. {doctor['name']},

We have a {urgency} case requiring your expertise in {doctor['specialty']}.

Patient: {patient_info.get('name', 'Patient')} (Age: {patient_info.get('age', 'Unknown')})
Symptoms: {symptoms}
ML Findings: {', '.join([k for k, v in ml_results.items() if v > 0.5])}

Please confirm your earliest available appointment slot.

Best regards,
JarvisMD Healthcare Coordination System
            """
            print(f"      🔄 Using fallback email template")
            return fallback_email
    
    def _send_appointment_request(self, request: Dict) -> bool:
        """Send appointment request email using SMTP"""
        try:
            import smtplib
            import os
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            print(f"      📤 REAL SMTP EMAIL SENDING:")
            print(f"         To: {request['doctor_email']}")
            print(f"         Subject: Appointment Request - {request['urgency_level']} Case")
            print(f"         Request ID: {request['request_id']}")
            
            # Email configuration (you can set these in environment variables)
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME", "your-email@gmail.com")  # Set your email
            smtp_password = os.getenv("SMTP_PASSWORD", "your-app-password")      # Set your app password
            
            print(f"         📡 SMTP Server: {smtp_server}:{smtp_port}")
            print(f"         👤 From: {smtp_username}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = request['doctor_email']
            msg['Subject'] = f"🏥 JarvisMD Appointment Request - {request['urgency_level']} Case"
            
            # Email body (use the generated content)
            body = request['email_content']
            msg.attach(MIMEText(body, 'plain'))
            
            # FOR TESTING: Send to your own email instead of doctor's email
            test_email = os.getenv("TEST_EMAIL", "arnav@yourtest.com")  # Replace with your email
            print(f"         🧪 TEST MODE: Sending to {test_email} instead of {request['doctor_email']}")
            msg['To'] = test_email
            
            try:
                # Connect and send email
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_username, smtp_password)
                
                text = msg.as_string()
                server.sendmail(smtp_username, test_email, text)
                server.quit()
                
                print(f"         ✅ REAL EMAIL SENT SUCCESSFULLY!")
                print(f"         📧 Delivered to: {test_email}")
                return True
                
            except Exception as smtp_error:
                print(f"         ❌ SMTP ERROR: {smtp_error}")
                print(f"         🔄 Falling back to simulation mode...")
                
                # Fallback to simulation
                print(f"         📤 SIMULATED EMAIL SEND:")
                print(f"            To: {test_email}")
                print(f"            Subject: Appointment Request - {request['urgency_level']} Case")
                print(f"            Body Preview: {body[:100]}...")
                print(f"         ✅ SIMULATED SEND SUCCESSFUL")
                return True
                
        except Exception as e:
            print(f"      ❌ Email sending failed: {e}")
            print(f"      🔄 Using fallback simulation...")
            
            # Complete fallback
            print(f"      📤 FALLBACK SIMULATION:")
            print(f"         To: {request['doctor_email']}")
            print(f"         Subject: Appointment Request - {request['urgency_level']} Case")
            print(f"         Request ID: {request['request_id']}")
            print(f"         Status: SIMULATED SENT ✅")
            return True

class DoctorResponseSimulatorAgent:
    """Agent that simulates doctor responses for testing"""
    
    def __init__(self):
        self.llm = get_llm()
        # Mock doctor response behaviors
        self.doctor_behaviors = {
            "dr_david_thompson": {"response_rate": 0.9, "response_time_hours": 2},
            "dr_sarah_chen": {"response_rate": 0.8, "response_time_hours": 4},
            "dr_lisa_patel": {"response_rate": 0.7, "response_time_hours": 6},
            "dr_robert_kim": {"response_rate": 0.85, "response_time_hours": 3},
            "dr_maria_rodriguez": {"response_rate": 0.9, "response_time_hours": 1},
        }
        
    def __call__(self, state: AgentState) -> AgentState:
        """Simulate doctor responses to appointment requests"""
        
        print("🤖 DOCTOR SIMULATOR: Simulating doctor responses...")
        
        doctor_responses = []
        confirmed_appointment = None
        
        for request in state['appointment_requests']:
            doctor_id = request['doctor_id']
            behavior = self.doctor_behaviors.get(doctor_id, {"response_rate": 0.8, "response_time_hours": 3})
            
            # Simulate response decision
            import random
            will_respond = random.random() < behavior["response_rate"]
            
            if will_respond:
                # Higher urgency cases get higher acceptance rate
                urgency_multiplier = {
                    "CRITICAL": 0.95,
                    "PRIORITY": 0.8,
                    "ROUTINE": 0.6
                }.get(state['case_classification'], 0.7)
                
                will_accept = random.random() < urgency_multiplier
                
                if will_accept and not confirmed_appointment:
                    # Accept with a specific slot
                    available_slots = request.get('preferred_slots', [])
                    if available_slots:
                        selected_slot = available_slots[0]
                        
                        response = {
                            "request_id": request['request_id'],
                            "doctor_id": doctor_id,
                            "doctor_name": request['doctor_name'],
                            "response": "ACCEPT",
                            "confirmed_slot": selected_slot,
                            "response_time": datetime.now().isoformat(),
                            "notes": f"Available for {state['case_classification']} case"
                        }
                        
                        # Create confirmed appointment
                        confirmed_appointment = {
                            "appointment_id": f"APPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            "doctor_id": doctor_id,
                            "doctor_name": request['doctor_name'],
                            "patient_id": state['patient_info'].get('patient_id', 'unknown'),
                            "patient_name": state['patient_info'].get('name', 'Patient'),
                            "appointment_datetime": selected_slot.get('datetime'),
                            "case_urgency": state['case_classification'],
                            "status": "confirmed",
                            "created_at": datetime.now().isoformat()
                        }
                        
                        print(f"   ✅ Dr. {request['doctor_name']} ACCEPTED appointment")
                        
                    else:
                        response = {
                            "request_id": request['request_id'],
                            "doctor_id": doctor_id,
                            "response": "DECLINE",
                            "reason": "No suitable slots available",
                            "response_time": datetime.now().isoformat()
                        }
                else:
                    response = {
                        "request_id": request['request_id'],
                        "doctor_id": doctor_id,
                        "response": "DECLINE",
                        "reason": "Schedule conflict" if confirmed_appointment else "Not available for this case type",
                        "response_time": datetime.now().isoformat()
                    }
                    print(f"   ❌ Dr. {request['doctor_name']} declined")
                
                doctor_responses.append(response)
            else:
                print(f"   ⏳ Dr. {request['doctor_name']} has not responded yet")
        
        # Update state
        state['doctor_responses'] = doctor_responses
        state['final_appointment'] = confirmed_appointment
        
        if confirmed_appointment:
            state['workflow_log'].append(f"Appointment confirmed with Dr. {confirmed_appointment['doctor_name']}")
            state['messages'].append(AIMessage(content=f"Appointment confirmed with Dr. {confirmed_appointment['doctor_name']}"))
            state['next_action'] = "calendar_integration"
            state['current_agent'] = "calendar_manager"
        else:
            state['workflow_log'].append("No doctors accepted - need alternative action")
            state['messages'].append(AIMessage(content="No appointments confirmed - escalating case"))
            state['next_action'] = "escalation"
            state['current_agent'] = "case_escalator"
        
        return state

class CalendarIntegrationAgent:
    """Agent that handles calendar integration and appointment management"""
    
    def __call__(self, state: AgentState) -> AgentState:
        """Integrate appointment into calendar system"""
        
        print("📅 CALENDAR MANAGER: Creating calendar entries...")
        
        appointment = state['final_appointment']
        if not appointment:
            state['next_action'] = "complete"
            return state
        
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
        
        print(f"   ✅ Calendar event created for {appointment['appointment_datetime']}")
        
        return state

class HealthAdvisorAgent:
    """Agent that provides health recommendations for low-risk cases"""
    
    def __init__(self):
        self.llm = get_llm()
        
    def __call__(self, state: AgentState) -> AgentState:
        """Generate health recommendations for low-risk cases"""
        
        print("🏃‍♂️ HEALTH ADVISOR: Generating lifestyle recommendations...")
        
        health_prompt = f"""
        You are a preventive health advisor providing recommendations for a low-risk patient.
        
        Patient Information:
        - Age: {state['patient_info'].get('age', 'Unknown')}
        - Symptoms: {state['symptoms']}
        
        ML Analysis Results:
        {json.dumps(state['ml_results'], indent=2)}
        
        Since this is a LOW_RISK case (urgency score: {state['urgency_score']}), provide:
        
        1. Lifestyle recommendations (diet, exercise, sleep)
        2. Preventive measures
        3. When to seek medical attention
        4. Follow-up timeline
        5. Resources for health monitoring
        
        Format as JSON:
        {{
            "lifestyle_recommendations": {{
                "diet": ["recommendation1", "recommendation2"],
                "exercise": ["recommendation1", "recommendation2"],
                "sleep": ["recommendation1", "recommendation2"]
            }},
            "preventive_measures": ["measure1", "measure2"],
            "warning_signs": ["sign1", "sign2"],
            "follow_up_timeline": "timeframe",
            "resources": ["resource1", "resource2"],
            "summary": "Brief summary of key points"
        }}
        
        Keep recommendations practical, evidence-based, and appropriate for the age group.
        Do NOT provide specific medical diagnoses or treatments.
        """
        
        response = self.llm.invoke([HumanMessage(content=health_prompt)])
        
        try:
            health_recommendations = json.loads(response.content)
        except:
            # Fallback recommendations
            health_recommendations = {
                "lifestyle_recommendations": {
                    "diet": ["Maintain a balanced diet with plenty of fruits and vegetables",
                           "Stay hydrated with adequate water intake"],
                    "exercise": ["Engage in regular moderate exercise (30 min, 5 days/week)",
                               "Include both cardio and strength training"],
                    "sleep": ["Aim for 7-9 hours of quality sleep per night",
                            "Maintain consistent sleep schedule"]
                },
                "preventive_measures": ["Regular health check-ups", "Stay up to date with vaccinations"],
                "warning_signs": ["Persistent or worsening symptoms", "New concerning symptoms"],
                "follow_up_timeline": "Monitor symptoms for 1-2 weeks",
                "resources": ["NHS health information", "Local health centers"],
                "summary": "Focus on healthy lifestyle habits and monitor symptoms"
            }
        
        state['health_recommendations'] = health_recommendations
        state['workflow_log'].append("Health recommendations generated")
        state['messages'].append(AIMessage(content="Health recommendations provided"))
        state['next_action'] = "complete"
        
        print("   ✅ Health recommendations generated")
        
        return state

class MultiAgentWorkflow:
    """Main workflow orchestrator using LangGraph"""
    
    def __init__(self):
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
                "escalation": END  # For now, end if no appointments
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
    
    async def process_case(self, patient_info: Dict, symptoms: str, 
                          ml_results: Dict, urgency_score: float) -> Dict:
        """Process a complete case through the multi-agent workflow"""
        
        print("🚀 STARTING MULTI-AGENT WORKFLOW")
        print("=" * 50)
        
        # Initialize state
        initial_state = {
            "patient_info": patient_info,
            "symptoms": symptoms,
            "ml_results": ml_results,
            "urgency_score": urgency_score,
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
        
        print("\n✅ WORKFLOW COMPLETED")
        print("=" * 50)
        
        # Print summary
        print(f"Case Classification: {result.get('case_classification')}")
        if result.get('final_appointment'):
            appt = result['final_appointment']
            print(f"Appointment Confirmed: Dr. {appt['doctor_name']} at {appt['appointment_datetime']}")
        elif result.get('health_recommendations'):
            print("Health recommendations provided for low-risk case")
        
        print(f"Total workflow steps: {len(result['workflow_log'])}")
        
        return result
    
    def run_case_sync(self, patient_info: Dict, symptoms: str, 
                     ml_results: Dict, urgency_score: float) -> Dict:
        """Synchronous version of process_case"""
        import asyncio
        
        # Create new event loop if none exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.process_case(patient_info, symptoms, ml_results, urgency_score)
        )

# Example usage and testing
def create_test_case() -> Dict:
    """Create a test case for the multi-agent system"""
    
    return {
        "patient_info": {
            "patient_id": "JMD_20251109_TEST_001",
            "name": "John Smith",
            "age": 65,
            "email": "john.smith@example.com",
            "phone": "+44-161-123-4567",
            "medical_history": "Hypertension, Type 2 Diabetes"
        },
        "symptoms": "Chest pain, shortness of breath, fatigue",
        "ml_results": {
            "Cardiomegaly": 0.85,
            "Pneumonia": 0.12,
            "Edema": 0.67,
            "Consolidation": 0.23,
            "Atelectasis": 0.34
        },
        "urgency_score": 7.5
    }

def create_low_risk_test_case() -> Dict:
    """Create a low-risk test case"""
    
    return {
        "patient_info": {
            "patient_id": "JMD_20251109_TEST_002", 
            "name": "Sarah Johnson",
            "age": 28,
            "email": "sarah.j@example.com",
            "phone": "+44-161-987-6543"
        },
        "symptoms": "Mild cough, no fever",
        "ml_results": {
            "No Finding": 0.89,
            "Pneumonia": 0.05,
            "Cardiomegaly": 0.02
        },
        "urgency_score": 1.2
    }

if __name__ == "__main__":
    # Test the multi-agent system
    print("🧪 TESTING MULTI-AGENT WORKFLOW SYSTEM")
    print("=" * 50)
    
    # Initialize workflow
    workflow = MultiAgentWorkflow()
    
    # Test high-risk case
    print("\n🚨 Testing HIGH-RISK case...")
    high_risk_case = create_test_case()
    result_high = workflow.run_case_sync(
        high_risk_case["patient_info"],
        high_risk_case["symptoms"],
        high_risk_case["ml_results"],
        high_risk_case["urgency_score"]
    )
    
    # Test low-risk case  
    print("\n🟢 Testing LOW-RISK case...")
    low_risk_case = create_low_risk_test_case()
    result_low = workflow.run_case_sync(
        low_risk_case["patient_info"],
        low_risk_case["symptoms"],
        low_risk_case["ml_results"],
        low_risk_case["urgency_score"]
    )
    
    print("\n🎉 ALL TESTS COMPLETED!")
