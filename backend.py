"""
FastAPI backend for AI Junior-Doctor
Accepts chest X-ray uploads, runs CheXpert + Gemini LLM, returns structured JSON
"""

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

# Import modular AI pipeline
from main import preprocess_image, run_chexpert_inference, generate_llm_report, compute_urgency_score, generate_urgency_label

app = FastAPI(title="AI Junior Doctor API")

# Enable CORS for React frontend (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"] for React dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    # Read uploaded file into PIL
    img_bytes = await file.read()
    img = Image.open(io.BytesIO(img_bytes)).convert("L")

    # Preprocess
    img_tensor = preprocess_image(img)

    # CheXpert inference
    pathologies, preds = run_chexpert_inference(img_tensor)

    # LLM report
    findings_input = {pathology: float(prob.item()) for pathology, prob in zip(pathologies, preds)}
    llm_report = generate_llm_report(findings_input)

    # Urgency scoring
    urgency_score = compute_urgency_score(pathologies, preds)
    urgency_label = generate_urgency_label(findings_input, urgency_score)

    # Return JSON
    return JSONResponse({
        "chexpert_findings": findings_input,
        "llm_report": llm_report,
        "urgency_score": urgency_score,
        "urgency_label": urgency_label
    })

# Run with: uvicorn backend:app --reload --port 8000
