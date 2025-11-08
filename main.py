"""
FastAPI Backend Server for JarvisMD
Integrates the AI pipeline with the React frontend
"""

import os
import json
import base64
from io import BytesIO
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
import torchxrayvision as xrv
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY is None:
    raise ValueError("Please set GOOGLE_API_KEY in your .env file")

os.environ["GOOGLE_API_KEY"] = API_KEY

# Initialize FastAPI app
app = FastAPI(title="JarvisMD API", description="AI-Powered Medical Diagnosis API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI model (load once at startup)
print("🤖 Loading CheXpert model...")
chexpert_model = xrv.models.DenseNet(weights="chex")
chexpert_model.eval()
print("✅ CheXpert model loaded successfully!")

# Pydantic models for request/response
class PatientInfo(BaseModel):
    name: str
    age: int
    gender: str
    symptoms: str
    medical_history: str = ""
    emergency_contact: str = ""

class AnalysisResult(BaseModel):
    patient_id: str
    timestamp: str
    patient_info: PatientInfo
    ai_findings: Dict[str, float]
    structured_report: str
    urgency_score: float
    urgency_level: str
    recommendations: str

# Helper functions from legacy_main.py
def preprocess_image(img: Image.Image) -> torch.Tensor:
    """Normalize and convert PIL image to tensor [1,1,224,224]."""
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

def generate_llm_report(findings_input: dict, patient_info: dict) -> str:
    """Use Gemini LLM to produce structured findings report."""
    try:
        client = genai.Client()
        prompt = f"""
        You are an experienced radiologist reviewing a chest X-ray for emergency triage.
        
        Patient Information:
        - Name: {patient_info.get('name', 'Unknown')}
        - Age: {patient_info.get('age', 'Unknown')}
        - Gender: {patient_info.get('gender', 'Unknown')}
        - Symptoms: {patient_info.get('symptoms', 'None provided')}
        - Medical History: {patient_info.get('medical_history', 'None provided')}
        
        AI Model Predictions (probability scores 0-1):
        {json.dumps(findings_input, indent=2)}
        
        Please provide a structured JSON response with these exact fields:
        {{
            "findings_summary": "Brief clinical summary of abnormal findings",
            "preliminary_diagnosis": "Most likely diagnosis based on findings and symptoms",
            "clinical_correlation": "How findings relate to patient symptoms",
            "recommendations": "Immediate actions or follow-up needed"
        }}
        
        Focus on clinically significant findings (>0.5 probability) and provide actionable medical guidance.
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return json.dumps({
            "findings_summary": "AI analysis completed with technical limitations",
            "preliminary_diagnosis": "Manual review recommended",
            "clinical_correlation": f"Error in LLM processing: {str(e)}",
            "recommendations": "Proceed with standard clinical evaluation"
        })

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
        "Lung Opacity": 3,
        "Fracture": 8,
    }
    
    score = 0
    for i, pathology in enumerate(pathologies):
        if pathology in severity_weights and i < len(preds):
            score += severity_weights[pathology] * preds[i].item()
    
    return min(10, score / 2)  # normalize to 0–10 scale

def generate_urgency_label(findings_input: dict, urgency_score: float, patient_info: dict) -> str:
    """Use Gemini LLM to generate urgency assessment."""
    try:
        client = genai.Client()
        prompt = f"""
        Emergency triage assessment for patient:
        Age: {patient_info.get('age')}, Symptoms: {patient_info.get('symptoms')}
        
        AI Findings: {json.dumps(findings_input, indent=2)}
        Calculated urgency score: {urgency_score:.1f}/10
        
        Provide triage classification as JSON:
        {{
            "urgency_level": "ROUTINE|URGENT|CRITICAL",
            "triage_priority": 1-5,
            "reasoning": "Clinical justification",
            "immediate_actions": "Required interventions"
        }}
        
        Guidelines:
        - ROUTINE (1-2): Stable, can wait
        - URGENT (3-4): Needs prompt attention  
        - CRITICAL (5): Immediate intervention required
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        # Fallback urgency assessment
        if urgency_score >= 7:
            level = "CRITICAL"
        elif urgency_score >= 4:
            level = "URGENT" 
        else:
            level = "ROUTINE"
            
        return json.dumps({
            "urgency_level": level,
            "triage_priority": min(5, max(1, int(urgency_score / 2) + 1)),
            "reasoning": f"Automated assessment based on urgency score {urgency_score:.1f}",
            "immediate_actions": "Standard clinical evaluation recommended"
        })

# API Endpoints
@app.get("/")
async def root():
    return {"message": "JarvisMD API Server", "status": "running", "version": "1.0"}

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_medical_scan(
    scan: UploadFile = File(...),
    patient_name: str = Form(...),
    patient_age: int = Form(...),
    patient_gender: str = Form(...),
    symptoms: str = Form(...),
    medical_history: str = Form(""),
    emergency_contact: str = Form("")
):
    """
    Analyze medical scan and return comprehensive AI diagnosis
    """
    try:
        # Validate file type
        if not scan.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Process uploaded image
        image_data = await scan.read()
        img = Image.open(BytesIO(image_data)).convert("L")
        
        # Create patient info
        patient_info = PatientInfo(
            name=patient_name,
            age=patient_age,
            gender=patient_gender,
            symptoms=symptoms,
            medical_history=medical_history,
            emergency_contact=emergency_contact
        )
        
        # Run AI analysis pipeline
        print(f"🔬 Analyzing scan for patient: {patient_name}")
        
        # Step 1: Preprocess image
        img_tensor = preprocess_image(img)
        
        # Step 2: CheXpert inference
        pathologies, preds = run_chexpert_inference(img_tensor)
        
        # Step 3: Create findings dictionary
        findings_input = {
            pathology: float(prob.item()) 
            for pathology, prob in zip(pathologies, preds) 
            if pathology  # Filter out empty pathology names
        }
        
        # Step 4: Generate LLM report
        patient_dict = patient_info.dict()
        structured_report = generate_llm_report(findings_input, patient_dict)
        
        # Step 5: Compute urgency
        urgency_score = compute_urgency_score(pathologies, preds)
        urgency_assessment = generate_urgency_label(findings_input, urgency_score, patient_dict)
        
        # Create analysis result
        patient_id = f"JMD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{patient_name.replace(' ', '')[:5]}"
        
        result = AnalysisResult(
            patient_id=patient_id,
            timestamp=datetime.now().isoformat(),
            patient_info=patient_info,
            ai_findings=findings_input,
            structured_report=structured_report,
            urgency_score=urgency_score,
            urgency_level=urgency_assessment,
            recommendations=structured_report  # Will be parsed from LLM response
        )
        
        print(f"✅ Analysis complete for {patient_name} - Urgency: {urgency_score:.1f}/10")
        return result
        
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": chexpert_model is not None,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
