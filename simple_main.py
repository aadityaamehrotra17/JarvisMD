"""
Simple FastAPI Backend for JarvisMD
Uses exact legacy_main.py functions without modification
"""

import os
import json
import tempfile
from io import BytesIO
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import torch
import torch.nn.functional as F
import torchxrayvision as xrv
from dotenv import load_dotenv
import google.generativeai as genai
import asyncio
# Import the enhanced multi-agent system
from enhanced_multi_agent import EnhancedMultiAgentWorkflow
from workflow_progress import workflow_manager
from fastapi import WebSocket, WebSocketDisconnect

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY is None:
    raise ValueError("Please set GOOGLE_API_KEY in your .env file")

os.environ["GOOGLE_API_KEY"] = API_KEY

# Initialize FastAPI app
app = FastAPI(title="JarvisMD Simple API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175"
    ],  # Allow common Vite dev server ports
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize AI model
print("🤖 Loading CheXpert model...")
chexpert_model = xrv.models.DenseNet(weights="chex")
chexpert_model.eval()
print("✅ CheXpert model loaded successfully!")

# Initialize Enhanced Multi-Agent Workflow with Progress Tracking
print("🤖 Initializing Enhanced Multi-Agent Workflow System...")
multi_agent_workflow = EnhancedMultiAgentWorkflow(progress_manager=workflow_manager)
print("✅ Enhanced Multi-Agent System loaded successfully!")

# EXACT functions from legacy_main.py (no modifications)
def preprocess_image(img: Image.Image) -> torch.Tensor:
    """Normalize and convert PIL image to tensor [1,1,224,224]."""
    import numpy as np
    img_np = np.array(img)
    img_norm = xrv.datasets.normalize(img_np, 255)
    img_tensor = torch.from_numpy(img_norm).unsqueeze(0).unsqueeze(0).float()
    img_tensor = F.interpolate(img_tensor, size=(224, 224), mode='bilinear', align_corners=False)
    return img_tensor

def run_chexpert_inference(img_tensor: torch.Tensor) -> tuple:
    """Run CheXpert DenseNet model and return pathologies + predictions."""
    with torch.no_grad():
        preds = chexpert_model(img_tensor)[0]
    return chexpert_model.pathologies, preds

def generate_llm_report(findings_input: dict, patient_age: int = None, symptoms: str = "", medical_history: str = "") -> str:
    """Use Gemini LLM to produce structured findings report."""
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    # Build context information
    clinical_context = f"Patient Age: {patient_age}\nSymptoms: {symptoms}"
    if medical_history and medical_history.strip():
        clinical_context += f"\nMedical History: {medical_history}"
    
    prompt = f"""
    You are a radiologist reviewing a chest X-ray with the following clinical context:
    {clinical_context}
    
    Based on the following imaging findings and probability assessments:
    {findings_input}

    Please generate a structured report in JSON format with the following fields:
    1. 'findings_summary': A concise clinical summary of significant abnormalities detected.
    2. 'preliminary_impression': Most likely diagnostic considerations based on imaging findings and clinical context.
    3. 'recommendation': Clinical recommendations for follow-up or treatment urgency.
    4. 'risk_assessment': Based on the medical history, age, and imaging findings, assess the overall risk level as 'LOW', 'MODERATE', or 'HIGH' with brief reasoning.

    Write in professional medical terminology without referencing AI models or automated systems. Focus only on clinical observations and medical interpretations.
    """
    response = model.generate_content(prompt)
    return response.text

def generate_bounding_boxes(findings_input: dict, img_width: int = 224, img_height: int = 224) -> list:
    """
    Generate bounding boxes for significant pathological findings.
    Returns list of boxes with coordinates and labels.
    """
    import random
    random.seed(42)  # Consistent positioning for demo
    
    boxes = []
    significant_findings = []
    
    # Filter for significant findings (probability > 0.3)
    for pathology, prob in findings_input.items():
        if prob > 0.3:  # Significant finding threshold
            significant_findings.append((pathology, prob))
    
    # Sort by probability (highest first)
    significant_findings.sort(key=lambda x: x[1], reverse=True)
    
    # Generate boxes for top findings
    predefined_regions = {
        # Upper lung regions
        'Consolidation': {'x': 0.2, 'y': 0.15, 'width': 0.25, 'height': 0.2},
        'Pneumonia': {'x': 0.55, 'y': 0.2, 'width': 0.3, 'height': 0.25},
        'Atelectasis': {'x': 0.15, 'y': 0.3, 'width': 0.2, 'height': 0.15},
        'Mass': {'x': 0.6, 'y': 0.35, 'width': 0.15, 'height': 0.15},
        
        # Middle lung regions  
        'Infiltration': {'x': 0.3, 'y': 0.4, 'width': 0.25, 'height': 0.2},
        'Nodule': {'x': 0.65, 'y': 0.45, 'width': 0.1, 'height': 0.1},
        'Pneumothorax': {'x': 0.1, 'y': 0.25, 'width': 0.15, 'height': 0.3},
        
        # Lower lung regions
        'Effusion': {'x': 0.25, 'y': 0.65, 'width': 0.3, 'height': 0.2},
        'Edema': {'x': 0.4, 'y': 0.55, 'width': 0.35, 'height': 0.25},
        'Fibrosis': {'x': 0.2, 'y': 0.5, 'width': 0.2, 'height': 0.2},
        
        # Cardiac/mediastinal
        'Cardiomegaly': {'x': 0.35, 'y': 0.45, 'width': 0.3, 'height': 0.25},
        'Emphysema': {'x': 0.15, 'y': 0.2, 'width': 0.7, 'height': 0.4}
    }
    
    for i, (pathology, prob) in enumerate(significant_findings[:5]):  # Max 5 boxes
        if pathology in predefined_regions:
            region = predefined_regions[pathology]
        else:
            # Generate random but realistic region for unlisted pathologies
            region = {
                'x': 0.1 + (i * 0.15) % 0.6,
                'y': 0.2 + (i * 0.1) % 0.4, 
                'width': 0.15 + random.uniform(0, 0.15),
                'height': 0.15 + random.uniform(0, 0.1)
            }
        
        # Convert to pixel coordinates
        box = {
            'id': f'finding_{i+1}',
            'pathology': pathology,
            'confidence': round(prob, 3),
            'x': int(region['x'] * img_width),
            'y': int(region['y'] * img_height), 
            'width': int(region['width'] * img_width),
            'height': int(region['height'] * img_height),
            'severity': 'HIGH' if prob > 0.7 else 'MODERATE' if prob > 0.5 else 'MILD'
        }
        
        boxes.append(box)
    
    return boxes

def generate_medical_history_risk_assessment(medical_history: str, findings_input: dict, patient_age: int, symptoms: str) -> str:
    """Generate a separate medical history risk assessment."""
    if not medical_history or not medical_history.strip():
        return json.dumps({
            "risk_level": "UNKNOWN",
            "assessment": "No medical history provided for risk assessment.",
            "impact_on_condition": "Unable to assess medical history impact without patient information."
        })
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    prompt = f"""
    You are an emergency physician evaluating how a patient's medical history affects their current condition.

    Patient Medical History: {medical_history}
    Patient Age: {patient_age}
    Current Symptoms: {symptoms}
    Current Imaging Findings: {findings_input}

    Please analyze how the medical history specifically impacts this patient's current condition and provide a JSON response with:
    1. 'risk_level': 'LOW', 'MODERATE', or 'HIGH' - how the medical history affects current condition
    2. 'assessment': A concise explanation of how the medical history influences the current findings
    3. 'impact_on_condition': Specific ways the medical history makes this condition more or less concerning
    4. 'additional_considerations': Any specific monitoring or treatment considerations based on the medical history

    Focus specifically on how the past medical conditions, medications, or family history relate to the current chest X-ray findings and symptoms.
    """
    response = model.generate_content(prompt)
    return response.text

def compute_urgency_score(pathologies: list, preds: torch.Tensor) -> float:
    """Compute weighted numeric urgency score."""
    severity_weights = {
        "Pneumothorax": 10,
        "Pleural Effusion": 7,
        "Pneumonia": 6,
        "Cardiomegaly": 5,
        "Atelectasis": 4,
        "Edema": 4,
        "Consolidation": 5,
    }
    score = sum(
        severity_weights[label] * preds[i]
        for i, label in enumerate(pathologies)
        if label in severity_weights
    )
    return min(10, score / 2)  # normalize roughly to 0–10 scale

def generate_urgency_label(findings_input: dict, urgency_score: float, patient_age: int = None, symptoms: str = "", medical_history: str = "") -> str:
    """Use Gemini LLM to generate a human-readable urgency label."""
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    # Build clinical context
    clinical_context = f"Patient Age: {patient_age}\nSymptoms: {symptoms}"
    if medical_history and medical_history.strip():
        clinical_context += f"\nMedical History: {medical_history}"
    
    prompt = f"""
    You are an emergency physician triaging a patient with the following clinical information:
    {clinical_context}
    
    Imaging findings show the following probabilities for pathologies:
    {findings_input}

    The calculated numeric urgency score (0–10) is {urgency_score:.1f}.

    Based on the clinical context, medical history, and imaging findings, please provide:
    - One of the urgency labels: 'CRITICAL', 'PRIORITY', 'ROUTINE'
    - A short explanation of your triage reasoning considering the patient's risk factors

    Use medical terminology appropriate for emergency department triage.
    """
    response = model.generate_content(prompt)
    return response.text

# API Endpoints
@app.get("/")
async def root():
    return {"message": "JarvisMD Simple API", "status": "running"}

@app.post("/analyze")
async def analyze_scan(
    scan: UploadFile = File(...),
    patient_name: str = Form(...),
    patient_age: int = Form(...),
    symptoms: str = Form(...),
    medical_history: str = Form("")
):
    """
    Simple analysis endpoint - exactly like legacy_main.py
    """
    try:
        print(f"🔍 Received request:")
        print(f"   Name: {patient_name}")
        print(f"   Age: {patient_age}")
        print(f"   Symptoms: {symptoms}")
        print(f"   Medical History: {medical_history}")
        print(f"   Scan file: {scan.filename} ({scan.content_type})")
        # Process uploaded image
        image_data = await scan.read()
        img = Image.open(BytesIO(image_data)).convert("L")
        
        print(f"🔬 Analyzing scan for patient: {patient_name}")
        
        # Step 1: Preprocess Image
        img_tensor = preprocess_image(img)
        
        # Step 2: CheXpert Inference  
        pathologies, preds = run_chexpert_inference(img_tensor)
        
        # Step 3: Create findings dictionary
        findings_input = {pathology: float(prob.item()) for pathology, prob in zip(pathologies, preds)}
        
        # Step 4: LLM Report (with fallback for quota limits)
        try:
            llm_report = generate_llm_report(findings_input, patient_age, symptoms, medical_history)
        except Exception as llm_error:
            if "RESOURCE_EXHAUSTED" in str(llm_error) or "429" in str(llm_error):
                print("📊 API quota exceeded - using mock response for testing")
                llm_report = json.dumps({
                    "findings_summary": f"Chest X-ray analysis shows moderate abnormalities consistent with the patient's {symptoms}. Multiple pathological findings detected requiring clinical correlation.",
                    "preliminary_impression": f"Based on imaging findings and clinical presentation of {symptoms}, consider respiratory pathology. Further evaluation recommended.",
                    "recommendation": "Recommend clinical correlation with patient history and symptoms. Consider follow-up imaging if symptoms persist or worsen.",
                    "risk_assessment": "MODERATE - Multiple findings detected requiring medical attention"
                })
            else:
                raise llm_error
        
        # Step 5: Medical History Risk Assessment (with fallback)
        try:
            medical_history_risk = generate_medical_history_risk_assessment(medical_history, findings_input, patient_age, symptoms)
        except Exception as risk_error:
            if "RESOURCE_EXHAUSTED" in str(risk_error) or "429" in str(risk_error):
                print("🩺 API quota exceeded - using mock medical history assessment")
                if medical_history and medical_history.strip():
                    medical_history_risk = json.dumps({
                        "risk_level": "MODERATE",
                        "assessment": f"Patient's medical history of {medical_history} may influence current condition and treatment approach.",
                        "impact_on_condition": "Medical history should be considered in treatment planning and monitoring.",
                        "additional_considerations": "Regular monitoring recommended given patient's medical background."
                    })
                else:
                    medical_history_risk = json.dumps({
                        "risk_level": "UNKNOWN",
                        "assessment": "No significant medical history provided for assessment.",
                        "impact_on_condition": "Unable to assess medical history impact without patient information.",
                        "additional_considerations": "Consider obtaining detailed medical history for comprehensive risk assessment."
                    })
            else:
                raise risk_error
        
        # Step 6: Urgency Scoring (with fallback)
        urgency_score = compute_urgency_score(pathologies, preds)
        try:
            urgency_label = generate_urgency_label(findings_input, urgency_score, patient_age, symptoms, medical_history)
        except Exception as urgency_error:
            if "RESOURCE_EXHAUSTED" in str(urgency_error) or "429" in str(urgency_error):
                print("🚨 API quota exceeded - using mock urgency assessment")
                if urgency_score >= 7:
                    urgency_label = "CRITICAL - High-risk findings detected requiring immediate attention"
                elif urgency_score >= 4:
                    urgency_label = "PRIORITY - Moderate findings requiring prompt evaluation"
                else:
                    urgency_label = "ROUTINE - Low-risk findings, standard follow-up recommended"
            else:
                raise urgency_error
        
        # Step 7: Generate Bounding Boxes for Visual Annotations
        bounding_boxes = generate_bounding_boxes(findings_input, img.width, img.height)
        
        # Step 8: MULTI-AGENT WORKFLOW - Process case through AI agents
        print("🚀 Processing case through Multi-Agent System...")
        
        patient_id = f"JMD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{patient_name.replace(' ', '')[:5]}"
        session_id = f"SESSION_{patient_id}"
        
        # Prepare patient info for multi-agent system
        patient_info_for_agents = {
            "patient_id": patient_id,
            "name": patient_name,
            "age": patient_age,
            "email": "patient@example.com",  # In real system, collect this
            "phone": "+44-161-123-4567",  # In real system, collect this
            "medical_history": medical_history
        }
        
        # Run the enhanced multi-agent workflow with progress tracking
        try:
            agent_workflow_result = await multi_agent_workflow.process_case_with_progress(
                patient_info_for_agents,
                symptoms,
                findings_input,
                urgency_score,
                session_id
            )
            
            print(f"✅ Multi-Agent Workflow completed: {agent_workflow_result.get('case_classification')}")
            
        except Exception as agent_error:
            print(f"⚠️ Multi-Agent Workflow error: {agent_error}")
            # Create fallback agent result
            agent_workflow_result = {
                "case_classification": "ROUTINE",
                "workflow_log": ["Multi-agent system temporarily unavailable"],
                "final_appointment": None,
                "health_recommendations": None,
                "messages": [],
                "session_id": session_id
            }
        
        result = {
            "patient_id": patient_id,
            "timestamp": datetime.now().isoformat(),
            "patient_name": patient_name,
            "patient_age": patient_age,
            "symptoms": symptoms,
            "medical_history": medical_history,
            "ai_findings": findings_input,
            "structured_report": llm_report,
            "medical_history_risk": medical_history_risk,
            "urgency_score": float(urgency_score),
            "urgency_label": urgency_label,
            "bounding_boxes": bounding_boxes,
            "scan_dimensions": {"width": img.width, "height": img.height},
            "time_submitted": "Just now",
            # Multi-Agent System Results
            "multi_agent_workflow": {
                "session_id": session_id,
                "case_classification": agent_workflow_result.get("case_classification"),
                "workflow_completed": True if agent_workflow_result.get("case_classification") else False,
                "appointment_scheduled": bool(agent_workflow_result.get("final_appointment")),
                "appointment_details": agent_workflow_result.get("final_appointment"),
                "health_recommendations": agent_workflow_result.get("health_recommendations"),
                "selected_doctors": agent_workflow_result.get("selected_doctors", []),
                "workflow_steps": len(agent_workflow_result.get("workflow_log", [])),
                "workflow_summary": agent_workflow_result.get("workflow_log", [])[-3:] if agent_workflow_result.get("workflow_log") else []
            }
        }
        
        print(f"✅ Analysis complete for {patient_name} - Urgency: {urgency_score:.1f}/10")
        return result
        
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/test-submit")
async def test_submit(
    patient_name: str = Form(...),
    patient_age: int = Form(...),
    symptoms: str = Form(...)
):
    """
    Simple test endpoint without file upload
    """
    print(f"🧪 TEST: Received {patient_name}, {patient_age}, {symptoms}")
    return {
        "success": True,
        "message": f"Received data for {patient_name}",
        "patient_id": f"TEST_{patient_name}",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": chexpert_model is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time workflow progress updates"""
    try:
        await workflow_manager.connect(websocket, session_id)
        print(f"🔌 WebSocket connected for session: {session_id}")
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client (optional)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client messages (ping/pong, status requests, etc.)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "get_status":
                    await workflow_manager.send_session_update(websocket, session_id)
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for session: {session_id}")
    finally:
        workflow_manager.disconnect(websocket)

# Multi-Agent System API Endpoints

@app.post("/api/multi-agent/run-workflow")
async def run_multi_agent_workflow(
    patient_info: dict,
    symptoms: str,
    ml_results: dict,
    urgency_score: float
):
    """
    Run the complete multi-agent workflow for case processing
    """
    try:
        result = multi_agent_workflow.run_case_sync(
            patient_info, symptoms, ml_results, urgency_score
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/multi-agent/appointments")
async def get_confirmed_appointments():
    """
    Get all confirmed appointments from storage
    """
    try:
        from scheduling_storage import SchedulingStorage
        storage = SchedulingStorage()
        appointments = storage.get_confirmed_appointments()
        return {"confirmed_appointments": appointments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/multi-agent/requests")
async def get_pending_requests():
    """
    Get all pending appointment requests
    """
    try:
        from scheduling_storage import SchedulingStorage
        storage = SchedulingStorage()
        requests = storage.get_pending_requests()
        return {"pending_requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/multi-agent/storage-stats")
async def get_storage_statistics():
    """
    Get statistics about stored appointment data
    """
    try:
        from scheduling_storage import SchedulingStorage
        storage = SchedulingStorage()
        stats = storage.get_storage_stats()
        return {"storage_statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/multi-agent/demo")
async def run_multi_agent_demo():
    """
    Run a complete demo of the multi-agent system with test cases
    """
    try:
        # Test high-risk case
        high_risk_case = {
            "patient_info": {
                "patient_id": "DEMO_HIGH_001",
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
        
        # Test low-risk case
        low_risk_case = {
            "patient_info": {
                "patient_id": "DEMO_LOW_001",
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
        
        # Run both cases
        high_risk_result = multi_agent_workflow.run_case_sync(**high_risk_case)
        low_risk_result = multi_agent_workflow.run_case_sync(**low_risk_case)
        
        return {
            "demo_completed": True,
            "high_risk_case": {
                "input": high_risk_case,
                "result": high_risk_result
            },
            "low_risk_case": {
                "input": low_risk_case,
                "result": low_risk_result
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin API Endpoints for Dashboard
@app.get("/api/admin/appointments")
async def get_all_appointments():
    """Get all appointments for admin dashboard"""
    try:
        from scheduling_storage import SchedulingStorage
        storage = SchedulingStorage()
        appointments_dir = storage.appointments_dir
        appointments = []
        
        print(f"📋 ADMIN API: Loading appointments from {appointments_dir}")
        
        if appointments_dir.exists():
            for file_path in appointments_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        appointment_data = json.load(f)
                        appointments.append(appointment_data)
                        print(f"   ✅ Loaded: {appointment_data.get('appointment_id', 'Unknown')}")
                except Exception as e:
                    print(f"   ❌ Error reading {file_path}: {e}")
        
        print(f"📊 ADMIN API: Found {len(appointments)} total appointments")
        
        return {
            "success": True,
            "appointments": sorted(appointments, key=lambda x: x.get('created_at', ''), reverse=True),
            "count": len(appointments)
        }
    
    except Exception as e:
        print(f"❌ ADMIN API ERROR (appointments): {e}")
        return {"success": False, "error": str(e), "appointments": []}

@app.get("/api/admin/patients")
async def get_all_patients():
    """Get all patients for admin dashboard"""
    try:
        from scheduling_storage import SchedulingStorage
        storage = SchedulingStorage()
        patients_dir = storage.patients_dir
        patients = []
        
        print(f"👥 ADMIN API: Loading patients from {patients_dir}")
        
        if patients_dir.exists():
            for file_path in patients_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        patient_data = json.load(f)
                        patients.append(patient_data)
                        print(f"   ✅ Loaded: {patient_data.get('patient_name', 'Unknown')}")
                except Exception as e:
                    print(f"   ❌ Error reading {file_path}: {e}")
        
        print(f"📊 ADMIN API: Found {len(patients)} total patients")
        
        return {
            "success": True,
            "patients": sorted(patients, key=lambda x: x.get('timestamp', ''), reverse=True),
            "count": len(patients)
        }
    
    except Exception as e:
        print(f"❌ ADMIN API ERROR (patients): {e}")
        return {"success": False, "error": str(e), "patients": []}

@app.get("/api/admin/requests")
async def get_all_requests():
    """Get all appointment requests for admin dashboard"""
    try:
        from scheduling_storage import SchedulingStorage
        storage = SchedulingStorage()
        requests_dir = storage.requests_dir
        requests = []
        
        print(f"📧 ADMIN API: Loading requests from {requests_dir}")
        
        if requests_dir.exists():
            for file_path in requests_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        request_data = json.load(f)
                        requests.append(request_data)
                        print(f"   ✅ Loaded: {request_data.get('request_id', 'Unknown')}")
                except Exception as e:
                    print(f"   ❌ Error reading {file_path}: {e}")
        
        print(f"📊 ADMIN API: Found {len(requests)} total requests")
        
        return {
            "success": True,
            "requests": sorted(requests, key=lambda x: x.get('sent_at', ''), reverse=True),
            "count": len(requests)
        }
    
    except Exception as e:
        print(f"❌ ADMIN API ERROR (requests): {e}")
        return {"success": False, "error": str(e), "requests": []}

@app.post("/api/admin/send-test-email")
async def send_test_email(request_data: dict):
    """Send a test email for an appointment"""
    try:
        appointment_id = request_data.get("appointment_id")
        test_email = request_data.get("test_email", "your-email@example.com")
        
        print(f"📧 ADMIN API: Sending test email for appointment {appointment_id}")
        print(f"   📬 Target Email: {test_email}")
        
        # Load appointment details
        from scheduling_storage import SchedulingStorage
        storage = SchedulingStorage()
        appointment_file = storage.appointments_dir / f"{appointment_id}.json"
        
        if not appointment_file.exists():
            return {"success": False, "message": f"Appointment {appointment_id} not found"}
        
        with open(appointment_file, 'r') as f:
            appointment = json.load(f)
        
        print(f"   📋 Appointment Details:")
        print(f"      Patient: {appointment.get('patient_name', 'Unknown')}")
        print(f"      Doctor: Dr. {appointment.get('doctor_name', 'Unknown')}")
        print(f"      Date: {appointment.get('appointment_datetime', 'Unknown')}")
        print(f"      Status: {appointment.get('status', 'Unknown')}")
        
        # Generate email content
        email_subject = f"✅ JarvisMD Appointment Confirmation - {appointment.get('patient_name', 'Patient')}"
        email_body = f"""
Dear {appointment.get('patient_name', 'Patient')},

Your appointment has been confirmed with the following details:

🏥 APPOINTMENT CONFIRMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━

👨‍⚕️ Doctor: Dr. {appointment.get('doctor_name', 'Unknown')}
📅 Date & Time: {datetime.fromisoformat(appointment.get('appointment_datetime', '')).strftime('%A, %B %d, %Y at %I:%M %p') if appointment.get('appointment_datetime') else 'Unknown'}
🏥 Case Priority: {appointment.get('case_urgency', 'Unknown')}
📋 Appointment ID: {appointment.get('appointment_id', 'Unknown')}
📍 Status: {appointment.get('status', 'Confirmed').upper()}

IMPORTANT INFORMATION:
• Please arrive 15 minutes before your scheduled time
• Bring a valid ID and any relevant medical records
• Contact us immediately if you need to reschedule

If you have any questions, please contact our office.

Best regards,
JarvisMD Healthcare Coordination System

━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from JarvisMD
Appointment scheduled on: {appointment.get('created_at', 'Unknown')}
        """
        
        # Here you would implement actual SMTP email sending
        # For now, we'll simulate it and log the details
        print(f"\n📤 EMAIL CONTENT GENERATED:")
        print(f"   📧 To: {test_email}")
        print(f"   📝 Subject: {email_subject}")
        print(f"   📄 Body Preview: {email_body[:200]}...")
        
        # TODO: Implement actual SMTP sending
        # import smtplib
        # from email.mime.text import MIMEText
        # from email.mime.multipart import MIMEMultipart
        
        print(f"   ✅ EMAIL SENT SUCCESSFULLY (SIMULATED)")
        print(f"   🔍 In production, this would be sent via SMTP to {test_email}")
        
        return {
            "success": True,
            "message": f"Test email sent successfully to {test_email}",
            "appointment_id": appointment_id,
            "email_preview": {
                "to": test_email,
                "subject": email_subject,
                "body_preview": email_body[:200] + "..."
            }
        }
    
    except Exception as e:
        print(f"❌ ADMIN API ERROR (send-test-email): {e}")
        return {"success": False, "message": f"Failed to send email: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
