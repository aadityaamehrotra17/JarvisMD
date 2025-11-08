"""
AI Junior-Doctor Pipeline: Chest X-ray Analysis using CheXpert + Gemini LLM
End-to-end CPU pipeline
"""

# ------------------------------
# Imports
# ------------------------------
import os
from dotenv import load_dotenv
from urllib.request import urlretrieve

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

import torch
import torch.nn.functional as F
import torchxrayvision as xrv

from google import genai

# ------------------------------
# Load API Key
# ------------------------------
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY is None:
    raise ValueError("Please set GOOGLE_API_KEY in your .env file")

os.environ["GOOGLE_API_KEY"] = API_KEY

# ------------------------------
# Functions
# ------------------------------
def download_image(url: str, save_path: str) -> Image.Image:
    """Download an image if not already present and return PIL image."""
    if not os.path.exists(save_path):
        print(f"Downloading image from {url}...")
        urlretrieve(url, save_path)
    else:
        print(f"Image already exists at {save_path}.")
    return Image.open(save_path).convert("L")


def preprocess_image(img: Image.Image) -> torch.Tensor:
    """Normalize and convert PIL image to tensor [1,1,224,224]."""
    img_np = np.array(img)
    img_norm = xrv.datasets.normalize(img_np, 255)
    img_tensor = torch.from_numpy(img_norm).unsqueeze(0).unsqueeze(0).float()
    img_tensor = F.interpolate(img_tensor, size=(224, 224), mode='bilinear', align_corners=False)
    return img_tensor


def run_chexpert_inference(img_tensor: torch.Tensor) -> tuple:
    """Run CheXpert DenseNet model and return pathologies + predictions."""
    model = xrv.models.DenseNet(weights="chex")
    model.eval()
    with torch.no_grad():
        preds = model(img_tensor)[0]
    return model.pathologies, preds


def generate_llm_report(findings_input: dict) -> str:
    """Use Gemini LLM to produce structured findings report."""
    client = genai.Client()
    prompt = f"""
    You are a junior radiologist reviewing a chest X-ray. The AI model produced the following predicted probabilities for pathologies:
    {findings_input}

    Please generate a structured report in JSON format with the following fields:
    1. 'findings_summary': A short natural-language summary of abnormalities.
    2. 'preliminary_impression': Likely conditions or clinical interpretation.
    3. 'recommendation': Suggested urgency or follow-up.

    Use clear, clinical language, and prioritize significant findings.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
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


def generate_urgency_label(findings_input: dict, urgency_score: float) -> str:
    """Use Gemini LLM to generate a human-readable urgency label."""
    client = genai.Client()
    prompt = f"""
    You are a junior radiologist triaging a patient. The AI model predicted the following probabilities for pathologies:
    {findings_input}

    The calculated numeric urgency score (0–10) is {urgency_score:.1f}.

    Please provide a human-readable urgency assessment:
    - One of the labels: 'ROUTINE', 'MODERATE', 'CRITICAL'
    - A short explanation of your reasoning
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


# ------------------------------
# Main Execution
# ------------------------------
def main():
    # Step 1: Load Image
    sample_url = "https://raw.githubusercontent.com/ieee8023/covid-chestxray-dataset/master/images/1-s2.0-S0140673620303706-fx1_lrg.jpg"
    img_path = "sample_cxr.jpg"
    img = download_image(sample_url, img_path)

    # Optional: Display the image
    plt.imshow(np.array(img), cmap="gray")
    plt.axis("off")
    plt.title("Sample Chest X-ray Input")
    plt.show()

    # Step 2: Preprocess Image
    img_tensor = preprocess_image(img)

    # Step 3: CheXpert Inference
    pathologies, preds = run_chexpert_inference(img_tensor)
    print("🩺 Predicted CheXpert findings:")
    for pathology, prob in zip(pathologies, preds):
        print(f"{pathology:20s}: {prob.item():.3f}")

    # Step 4: LLM Reasoning
    findings_input = {pathology: float(prob.item()) for pathology, prob in zip(pathologies, preds)}
    llm_report = generate_llm_report(findings_input)
    print("\n📝 LLM-Based Structured Report:\n", llm_report)

    # Step 5: Urgency Scoring
    urgency_score = compute_urgency_score(pathologies, preds)
    print(f"\n🔢 Raw Urgency Score (0–10): {urgency_score:.1f}")

    urgency_label = generate_urgency_label(findings_input, urgency_score)
    print("\n🚦 Final Urgency Assessment (via Gemini LLM):")
    print(urgency_label)


if __name__ == "__main__":
    main()
