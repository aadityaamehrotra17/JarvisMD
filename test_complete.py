#!/usr/bin/env python3
"""
Test the complete JarvisMD pipeline
"""

import requests
import json

def test_analyze_endpoint():
    print("🧪 Testing JarvisMD Analysis Pipeline")
    print("=" * 50)
    
    # Test data
    url = "http://localhost:8000/analyze"
    
    data = {
        'patient_name': 'Sarah Connor',
        'patient_age': 35,
        'symptoms': 'Severe chest pain and difficulty breathing'
    }
    
    # Upload file
    with open('image.jpeg', 'rb') as f:
        files = {'scan': f}
        
        print(f"📤 Sending analysis request for {data['patient_name']}")
        print(f"   Age: {data['patient_age']}")
        print(f"   Symptoms: {data['symptoms']}")
        print()
        
        try:
            response = requests.post(url, data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Analysis completed successfully!")
                print(f"   Patient ID: {result['patient_id']}")
                print(f"   Urgency Score: {result['urgency_score']}/10")
                print(f"   Time: {result['timestamp']}")
                print()
                
                print("🔬 AI Findings (Top 5):")
                findings = result['ai_findings']
                top_findings = sorted(findings.items(), key=lambda x: x[1], reverse=True)[:5]
                
                for pathology, probability in top_findings:
                    if pathology:  # Skip empty pathology names
                        print(f"   {pathology}: {probability:.3f} ({probability*100:.1f}%)")
                print()
                
                print("🏥 Clinical Assessment:")
                try:
                    # Try to parse structured report
                    report_text = result['structured_report']
                    if '```json' in report_text:
                        json_text = report_text.split('```json')[1].split('```')[0]
                        report = json.loads(json_text)
                        print(f"   Findings: {report.get('findings_summary', 'N/A')[:100]}...")
                        print(f"   Diagnosis: {report.get('preliminary_impression', 'N/A')[:100]}...")
                    else:
                        print(f"   Raw Report: {report_text[:150]}...")
                except:
                    print("   Report parsing failed")
                
                print()
                print("🚨 Urgency Assessment:")
                urgency_text = result['urgency_label']
                if 'CRITICAL' in urgency_text:
                    print("   Level: 🔴 CRITICAL - Immediate intervention required!")
                elif 'MODERATE' in urgency_text:
                    print("   Level: 🟡 MODERATE - Prompt attention needed")
                else:
                    print("   Level: 🟢 ROUTINE - Standard care")
                
                return True
                
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False

if __name__ == "__main__":
    test_analyze_endpoint()
