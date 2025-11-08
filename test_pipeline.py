#!/usr/bin/env python3
"""
Test script for JarvisMD AI Analysis Pipeline
Demonstrates the complete workflow with a sample chest X-ray
"""

import os
import sys
import json
import requests
from PIL import Image

def test_ai_pipeline():
    """Test the complete AI analysis pipeline"""
    
    print("🔬 JarvisMD AI Pipeline Test")
    print("=" * 40)
    
    # Check if sample image exists
    sample_image = "sample_cxr.jpg"
    if not os.path.exists(sample_image):
        print(f"❌ Sample image '{sample_image}' not found!")
        print("Please ensure the sample chest X-ray image is in the current directory.")
        return False
    
    # Test server health
    try:
        print("🏥 Checking AI server health...")
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Server Status: {health_data['status']}")
            print(f"✅ Model Loaded: {health_data['model_loaded']}")
        else:
            print(f"❌ Server health check failed: {health_response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to AI server: {e}")
        print("Please ensure the backend server is running on http://localhost:8000")
        return False
    
    # Prepare test patient data
    print("\n🩺 Preparing test patient data...")
    patient_data = {
        'patient_name': 'Test Patient',
        'patient_age': 45,
        'patient_gender': 'Male',
        'symptoms': 'Chest pain and shortness of breath for emergency testing',
        'medical_history': 'Previous hypertension, no known allergies',
        'emergency_contact': 'Emergency Contact: (555) 123-4567'
    }
    
    print(f"   📋 Patient: {patient_data['patient_name']}, Age {patient_data['patient_age']}")
    print(f"   🩺 Symptoms: {patient_data['symptoms']}")
    
    # Prepare image file
    print(f"\n📸 Loading medical scan: {sample_image}")
    try:
        with open(sample_image, 'rb') as f:
            files = {'scan': (sample_image, f, 'image/jpeg')}
            
            print("🤖 Sending to AI analysis pipeline...")
            print("   ⏳ This may take 30-60 seconds for complete analysis...")
            
            # Send analysis request
            response = requests.post(
                "http://localhost:8000/analyze",
                data=patient_data,
                files=files,
                timeout=120  # Allow time for AI processing
            )
            
            if response.status_code == 200:
                analysis_result = response.json()
                print_analysis_results(analysis_result)
                return True
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except FileNotFoundError:
        print(f"❌ Could not open image file: {sample_image}")
        return False
    except requests.exceptions.Timeout:
        print("❌ Analysis timed out - this may indicate server issues")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during analysis: {e}")
        return False

def print_analysis_results(result):
    """Print formatted analysis results"""
    
    print("\n🎉 AI Analysis Complete!")
    print("=" * 50)
    
    # Patient Info
    patient = result['patient_info']
    print(f"👤 Patient: {patient['name']} (Age {patient['age']})")
    print(f"📋 Patient ID: {result['patient_id']}")
    print(f"⏰ Analysis Time: {result['timestamp']}")
    
    # Urgency Assessment
    print(f"\n🚦 Urgency Score: {result['urgency_score']:.1f}/10")
    
    # AI Findings
    print(f"\n🔬 AI Pathology Detection:")
    findings = result['ai_findings']
    sorted_findings = sorted(findings.items(), key=lambda x: x[1], reverse=True)
    
    for pathology, probability in sorted_findings[:5]:  # Top 5 findings
        if pathology and probability > 0.1:  # Only show significant findings
            percentage = probability * 100
            risk_level = "🔴 HIGH" if probability > 0.5 else "🟡 MED" if probability > 0.3 else "🟢 LOW"
            print(f"   {pathology:20s}: {percentage:5.1f}% {risk_level}")
    
    # Structured Report
    print(f"\n📝 Clinical Report:")
    try:
        # Try to parse JSON from the structured report
        report_text = result['structured_report']
        json_match = report_text.find('{')
        if json_match != -1:
            json_end = report_text.rfind('}') + 1
            report_json = json.loads(report_text[json_match:json_end])
            
            print(f"   🔍 Findings: {report_json.get('findings_summary', 'N/A')}")
            print(f"   🏥 Diagnosis: {report_json.get('preliminary_diagnosis', 'N/A')}")
            print(f"   💡 Recommendations: {report_json.get('recommendations', 'N/A')}")
    except:
        print(f"   📄 Raw Report: {result['structured_report'][:200]}...")
    
    # Urgency Assessment
    print(f"\n⚡ Triage Assessment:")
    try:
        urgency_text = result['urgency_level']
        json_match = urgency_text.find('{')
        if json_match != -1:
            json_end = urgency_text.rfind('}') + 1
            urgency_json = json.loads(urgency_text[json_match:json_end])
            
            level = urgency_json.get('urgency_level', 'UNKNOWN')
            priority = urgency_json.get('triage_priority', '?')
            reasoning = urgency_json.get('reasoning', 'N/A')
            
            print(f"   🏷️  Priority Level: {level}")
            print(f"   🔢 Triage Priority: {priority}/5") 
            print(f"   🧠 Reasoning: {reasoning}")
    except:
        print(f"   📄 Raw Assessment: {result['urgency_level'][:200]}...")
    
    print(f"\n✅ Analysis stored and ready for dashboard viewing!")
    print(f"🌐 View in browser: http://localhost:5174/")
    print(f"📊 Dashboard: http://localhost:5174/dashboard")

if __name__ == "__main__":
    print("Starting JarvisMD AI Pipeline Test...")
    success = test_ai_pipeline()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"Your JarvisMD system is fully operational!")
    else:
        print(f"\n❌ Test failed. Please check the error messages above.")
        sys.exit(1)
