"""
Extended Manchester Hospital Doctor Database
30+ Doctors across multiple specialties with realistic schedules
"""

from datetime import datetime, timedelta
import random

# Expanded Manchester Doctors Database
MANCHESTER_DOCTORS_DATABASE = {
    # CARDIOLOGY - 5 doctors
    "dr_james_hartwell": {
        "id": "dr_james_hartwell",
        "name": "Dr. James Hartwell",
        "specialty": "Cardiologist", 
        "email": "j.hartwell@manchesterheart.nhs.uk",
        "phone": "+44-161-276-1234",
        "hospital": "Manchester Royal Infirmary",
        "department": "Cardiology",
        "expertise": ["Heart Failure", "Cardiomegaly", "Arrhythmia", "Coronary Disease"],
        "experience_years": 18,
        "rating": 4.9,
        "seniority": "Consultant",
        "availability": {
            "monday": ["09:00", "10:00", "11:00", "14:00", "15:00"],
            "tuesday": ["08:00", "09:00", "10:00", "15:00", "16:00"],
            "wednesday": ["09:00", "10:00", "14:00", "15:00"],
            "thursday": ["08:00", "09:00", "11:00", "14:00", "16:00"],
            "friday": ["09:00", "10:00", "11:00", "14:00"]
        }
    },
    
    "dr_sarah_mitchell": {
        "id": "dr_sarah_mitchell", 
        "name": "Dr. Sarah Mitchell",
        "specialty": "Cardiologist",
        "email": "s.mitchell@wythenshawe.nhs.uk",
        "phone": "+44-161-291-2345",
        "hospital": "Wythenshawe Hospital",
        "department": "Cardiac Surgery",
        "expertise": ["Interventional Cardiology", "Cardiomegaly", "Valve Disease"],
        "experience_years": 22,
        "rating": 4.8,
        "seniority": "Senior Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "13:00", "14:00"],
            "tuesday": ["09:00", "10:00", "11:00", "15:00"],
            "wednesday": ["08:00", "09:00", "14:00", "15:00"],
            "thursday": ["09:00", "10:00", "13:00", "14:00"],
            "friday": ["08:00", "09:00", "10:00"]
        }
    },
    
    "dr_michael_chen": {
        "id": "dr_michael_chen",
        "name": "Dr. Michael Chen", 
        "specialty": "Cardiologist",
        "email": "m.chen@salford.nhs.uk",
        "phone": "+44-161-206-3456",
        "hospital": "Salford Royal Hospital",
        "department": "Cardiology",
        "expertise": ["Echocardiography", "Heart Failure", "Preventive Cardiology"],
        "experience_years": 12,
        "rating": 4.7,
        "seniority": "Consultant",
        "availability": {
            "monday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
            "tuesday": ["09:00", "10:00", "11:00", "14:00"],
            "wednesday": ["10:00", "11:00", "15:00", "16:00"],
            "thursday": ["08:00", "09:00", "14:00", "15:00"],
            "friday": ["09:00", "10:00", "11:00", "14:00", "15:00"]
        }
    },
    
    "dr_emma_rodriguez": {
        "id": "dr_emma_rodriguez",
        "name": "Dr. Emma Rodriguez",
        "specialty": "Cardiologist",
        "email": "e.rodriguez@christie.nhs.uk", 
        "phone": "+44-161-446-4567",
        "hospital": "The Christie NHS Foundation Trust",
        "department": "Cardio-Oncology",
        "expertise": ["Cardio-Oncology", "Chemotherapy-Related Heart Disease"],
        "experience_years": 14,
        "rating": 4.8,
        "seniority": "Consultant",
        "availability": {
            "monday": ["09:00", "10:00", "14:00", "15:00"],
            "tuesday": ["08:00", "09:00", "10:00", "16:00"],
            "wednesday": ["09:00", "11:00", "14:00", "15:00"],
            "thursday": ["08:00", "09:00", "15:00", "16:00"],
            "friday": ["09:00", "10:00", "11:00"]
        }
    },
    
    "dr_robert_thompson": {
        "id": "dr_robert_thompson",
        "name": "Dr. Robert Thompson",
        "specialty": "Cardiologist",
        "email": "r.thompson@cmft.nhs.uk",
        "phone": "+44-161-276-5678",
        "hospital": "Manchester Royal Infirmary", 
        "department": "Cardiology",
        "expertise": ["Electrophysiology", "Pacemaker", "Arrhythmia"],
        "experience_years": 16,
        "rating": 4.6,
        "seniority": "Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "11:00", "15:00"],
            "tuesday": ["09:00", "10:00", "14:00", "15:00", "16:00"],
            "wednesday": ["08:00", "10:00", "11:00", "14:00"],
            "thursday": ["09:00", "10:00", "11:00", "16:00"],
            "friday": ["08:00", "09:00", "14:00", "15:00"]
        }
    },

    # PULMONOLOGY - 4 doctors
    "dr_lisa_patel": {
        "id": "dr_lisa_patel",
        "name": "Dr. Lisa Patel",
        "specialty": "Pulmonologist",
        "email": "l.patel@cmft.nhs.uk", 
        "phone": "+44-161-276-6789",
        "hospital": "Manchester Royal Infirmary",
        "department": "Respiratory Medicine",
        "expertise": ["Pneumonia", "COPD", "Lung Cancer", "Pulmonary Fibrosis"],
        "experience_years": 15,
        "rating": 4.8,
        "seniority": "Consultant",
        "availability": {
            "monday": ["09:00", "10:00", "11:00", "14:00", "15:00"],
            "tuesday": ["08:00", "09:00", "10:00", "15:00", "16:00"],
            "wednesday": ["09:00", "11:00", "14:00", "15:00"],
            "thursday": ["08:00", "09:00", "10:00", "14:00"],
            "friday": ["09:00", "10:00", "11:00", "15:00"]
        }
    },
    
    "dr_david_wilson": {
        "id": "dr_david_wilson",
        "name": "Dr. David Wilson", 
        "specialty": "Pulmonologist",
        "email": "d.wilson@wythenshawe.nhs.uk",
        "phone": "+44-161-291-7890",
        "hospital": "Wythenshawe Hospital",
        "department": "Thoracic Medicine", 
        "expertise": ["Lung Transplant", "Interstitial Lung Disease", "Pneumonia"],
        "experience_years": 20,
        "rating": 4.9,
        "seniority": "Senior Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "14:00", "15:00"],
            "tuesday": ["09:00", "10:00", "11:00", "16:00"],
            "wednesday": ["08:00", "10:00", "14:00", "15:00"],
            "thursday": ["09:00", "10:00", "11:00", "14:00"],
            "friday": ["08:00", "09:00", "10:00"]
        }
    },
    
    "dr_amanda_jones": {
        "id": "dr_amanda_jones",
        "name": "Dr. Amanda Jones",
        "specialty": "Pulmonologist",
        "email": "a.jones@salford.nhs.uk",
        "phone": "+44-161-206-8901",
        "hospital": "Salford Royal Hospital",
        "department": "Respiratory Medicine",
        "expertise": ["Asthma", "Sleep Medicine", "Pneumothorax"],
        "experience_years": 11,
        "rating": 4.7,
        "seniority": "Consultant",
        "availability": {
            "monday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
            "tuesday": ["09:00", "10:00", "15:00", "16:00"],
            "wednesday": ["09:00", "10:00", "11:00", "14:00"],
            "thursday": ["08:00", "10:00", "15:00", "16:00"],
            "friday": ["09:00", "10:00", "11:00", "14:00"]
        }
    },
    
    "dr_peter_clark": {
        "id": "dr_peter_clark",
        "name": "Dr. Peter Clark",
        "specialty": "Pulmonologist", 
        "email": "p.clark@pennine.nhs.uk",
        "phone": "+44-161-624-9012",
        "hospital": "Royal Oldham Hospital",
        "department": "Respiratory Medicine",
        "expertise": ["Critical Care", "ARDS", "Pneumonia", "Ventilation"],
        "experience_years": 13,
        "rating": 4.6,
        "seniority": "Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "15:00", "16:00"],
            "tuesday": ["09:00", "10:00", "11:00", "14:00"],
            "wednesday": ["08:00", "09:00", "10:00", "15:00"],
            "thursday": ["10:00", "11:00", "14:00", "15:00"],
            "friday": ["08:00", "09:00", "14:00", "15:00", "16:00"]
        }
    },

    # EMERGENCY MEDICINE - 6 doctors
    "dr_karen_white": {
        "id": "dr_karen_white",
        "name": "Dr. Karen White",
        "specialty": "Emergency Medicine",
        "email": "k.white@cmft.nhs.uk",
        "phone": "+44-161-276-0123", 
        "hospital": "Manchester Royal Infirmary",
        "department": "Emergency Department",
        "expertise": ["Trauma", "Critical Care", "Emergency Procedures"],
        "experience_years": 17,
        "rating": 4.8,
        "seniority": "Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "10:00", "20:00", "21:00"],
            "tuesday": ["08:00", "09:00", "20:00", "21:00", "22:00"],
            "wednesday": ["09:00", "10:00", "11:00", "20:00"],
            "thursday": ["08:00", "09:00", "21:00", "22:00"],
            "friday": ["09:00", "10:00", "20:00", "21:00"]
        }
    },
    
    "dr_mark_davis": {
        "id": "dr_mark_davis",
        "name": "Dr. Mark Davis",
        "specialty": "Emergency Medicine",
        "email": "m.davis@wythenshawe.nhs.uk",
        "phone": "+44-161-291-1234",
        "hospital": "Wythenshawe Hospital", 
        "department": "Emergency Department",
        "expertise": ["Emergency Surgery", "Polytrauma", "Critical Care"],
        "experience_years": 19,
        "rating": 4.9,
        "seniority": "Senior Consultant",
        "availability": {
            "monday": ["07:00", "08:00", "19:00", "20:00"],
            "tuesday": ["08:00", "09:00", "19:00", "20:00", "21:00"],
            "wednesday": ["07:00", "08:00", "20:00", "21:00"],
            "thursday": ["08:00", "09:00", "19:00", "20:00"],
            "friday": ["07:00", "08:00", "09:00"]
        }
    },
    
    "dr_rachel_brown": {
        "id": "dr_rachel_brown",
        "name": "Dr. Rachel Brown",
        "specialty": "Emergency Medicine",
        "email": "r.brown@salford.nhs.uk",
        "phone": "+44-161-206-2345",
        "hospital": "Salford Royal Hospital",
        "department": "Emergency Department",
        "expertise": ["Pediatric Emergency", "Toxicology", "Emergency Medicine"],
        "experience_years": 9,
        "rating": 4.6,
        "seniority": "Registrar",
        "availability": {
            "monday": ["12:00", "13:00", "14:00", "18:00", "19:00"],
            "tuesday": ["12:00", "13:00", "18:00", "19:00", "20:00"],
            "wednesday": ["13:00", "14:00", "15:00", "18:00"],
            "thursday": ["12:00", "13:00", "19:00", "20:00"],
            "friday": ["13:00", "14:00", "18:00", "19:00"]
        }
    },
    
    "dr_anthony_taylor": {
        "id": "dr_anthony_taylor",
        "name": "Dr. Anthony Taylor",
        "specialty": "Emergency Medicine",
        "email": "a.taylor@stockport.nhs.uk",
        "phone": "+44-161-419-3456",
        "hospital": "Stepping Hill Hospital",
        "department": "Emergency Department",
        "expertise": ["Acute Medicine", "Resuscitation", "Emergency Procedures"],
        "experience_years": 14,
        "rating": 4.7,
        "seniority": "Consultant",
        "availability": {
            "monday": ["06:00", "07:00", "18:00", "19:00", "20:00"],
            "tuesday": ["07:00", "08:00", "18:00", "19:00"],
            "wednesday": ["06:00", "07:00", "08:00", "19:00"],
            "thursday": ["07:00", "08:00", "18:00", "19:00"],
            "friday": ["06:00", "07:00", "18:00", "19:00", "20:00"]
        }
    },
    
    "dr_sophie_williams": {
        "id": "dr_sophie_williams", 
        "name": "Dr. Sophie Williams",
        "specialty": "Emergency Medicine",
        "email": "s.williams@pennine.nhs.uk",
        "phone": "+44-161-624-4567",
        "hospital": "North Manchester General Hospital",
        "department": "Emergency Department",
        "expertise": ["Emergency Medicine", "Minor Surgery", "Wound Care"],
        "experience_years": 7,
        "rating": 4.5,
        "seniority": "Registrar",
        "availability": {
            "monday": ["14:00", "15:00", "16:00", "22:00", "23:00"],
            "tuesday": ["14:00", "15:00", "22:00", "23:00"],
            "wednesday": ["15:00", "16:00", "17:00", "22:00"],
            "thursday": ["14:00", "15:00", "23:00"],
            "friday": ["15:00", "16:00", "22:00", "23:00"]
        }
    },
    
    "dr_daniel_johnson": {
        "id": "dr_daniel_johnson",
        "name": "Dr. Daniel Johnson",
        "specialty": "Emergency Medicine", 
        "email": "d.johnson@tameside.nhs.uk",
        "phone": "+44-161-331-5678",
        "hospital": "Tameside General Hospital",
        "department": "Emergency Department",
        "expertise": ["Emergency Medicine", "Cardiac Arrest", "Trauma"],
        "experience_years": 12,
        "rating": 4.7,
        "seniority": "Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "10:00", "20:00"],
            "tuesday": ["09:00", "10:00", "20:00", "21:00"],
            "wednesday": ["08:00", "09:00", "21:00", "22:00"],
            "thursday": ["09:00", "10:00", "11:00", "20:00"],
            "friday": ["08:00", "09:00", "20:00", "21:00", "22:00"]
        }
    },

    # RADIOLOGY - 4 doctors
    "dr_helen_garcia": {
        "id": "dr_helen_garcia",
        "name": "Dr. Helen Garcia",
        "specialty": "Radiologist",
        "email": "h.garcia@cmft.nhs.uk",
        "phone": "+44-161-276-6789",
        "hospital": "Manchester Royal Infirmary",
        "department": "Medical Imaging",
        "expertise": ["Chest Imaging", "CT", "MRI", "Lung Opacity"],
        "experience_years": 16,
        "rating": 4.9,
        "seniority": "Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "10:00", "14:00", "15:00"],
            "tuesday": ["08:00", "09:00", "15:00", "16:00"],
            "wednesday": ["09:00", "10:00", "11:00", "14:00"],
            "thursday": ["08:00", "09:00", "14:00", "15:00", "16:00"],
            "friday": ["09:00", "10:00", "11:00"]
        }
    },
    
    "dr_christopher_lee": {
        "id": "dr_christopher_lee",
        "name": "Dr. Christopher Lee",
        "specialty": "Radiologist",
        "email": "c.lee@wythenshawe.nhs.uk",
        "phone": "+44-161-291-7890",
        "hospital": "Wythenshawe Hospital",
        "department": "Radiology",
        "expertise": ["Interventional Radiology", "Chest X-Ray", "Emergency Imaging"],
        "experience_years": 21,
        "rating": 4.8,
        "seniority": "Senior Consultant",
        "availability": {
            "monday": ["07:00", "08:00", "13:00", "14:00"],
            "tuesday": ["08:00", "09:00", "13:00", "14:00", "15:00"],
            "wednesday": ["07:00", "08:00", "14:00", "15:00"],
            "thursday": ["08:00", "09:00", "13:00", "14:00"],
            "friday": ["07:00", "08:00", "09:00"]
        }
    },
    
    "dr_nicole_anderson": {
        "id": "dr_nicole_anderson",
        "name": "Dr. Nicole Anderson", 
        "specialty": "Radiologist",
        "email": "n.anderson@salford.nhs.uk",
        "phone": "+44-161-206-8901",
        "hospital": "Salford Royal Hospital",
        "department": "Imaging",
        "expertise": ["Thoracic Imaging", "Lung Nodules", "Screening"],
        "experience_years": 13,
        "rating": 4.7,
        "seniority": "Consultant",
        "availability": {
            "monday": ["09:00", "10:00", "11:00", "15:00", "16:00"],
            "tuesday": ["09:00", "10:00", "15:00", "16:00"],
            "wednesday": ["08:00", "09:00", "10:00", "14:00"],
            "thursday": ["10:00", "11:00", "15:00", "16:00"],
            "friday": ["09:00", "10:00", "11:00", "14:00", "15:00"]
        }
    },
    
    "dr_james_martinez": {
        "id": "dr_james_martinez",
        "name": "Dr. James Martinez",
        "specialty": "Radiologist",
        "email": "j.martinez@christie.nhs.uk",
        "phone": "+44-161-446-9012",
        "hospital": "The Christie NHS Foundation Trust", 
        "department": "Oncology Imaging",
        "expertise": ["Oncology Imaging", "PET-CT", "Lung Cancer"],
        "experience_years": 18,
        "rating": 4.8,
        "seniority": "Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "14:00", "15:00"],
            "tuesday": ["09:00", "10:00", "14:00", "15:00", "16:00"],
            "wednesday": ["08:00", "10:00", "11:00", "15:00"],
            "thursday": ["09:00", "10:00", "14:00", "15:00"],
            "friday": ["08:00", "09:00", "10:00"]
        }
    },

    # INTERNAL MEDICINE / GP - 8 doctors
    "dr_patricia_moore": {
        "id": "dr_patricia_moore",
        "name": "Dr. Patricia Moore",
        "specialty": "Internal Medicine",
        "email": "p.moore@cmft.nhs.uk",
        "phone": "+44-161-276-0123",
        "hospital": "Manchester Royal Infirmary",
        "department": "Internal Medicine",
        "expertise": ["General Medicine", "Chronic Disease", "Diabetes"],
        "experience_years": 14,
        "rating": 4.6,
        "seniority": "Consultant",
        "availability": {
            "monday": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
            "tuesday": ["08:00", "09:00", "10:00", "14:00", "15:00"],
            "wednesday": ["09:00", "10:00", "11:00", "15:00", "16:00"],
            "thursday": ["08:00", "09:00", "10:00", "11:00", "14:00"],
            "friday": ["09:00", "10:00", "11:00", "14:00", "15:00"]
        }
    },
    
    "dr_steven_hall": {
        "id": "dr_steven_hall",
        "name": "Dr. Steven Hall",
        "specialty": "General Practice",
        "email": "s.hall@manchester.gp.nhs.uk",
        "phone": "+44-161-234-1234",
        "hospital": "Manchester Central Medical Centre",
        "department": "Primary Care", 
        "expertise": ["Family Medicine", "Preventive Care", "Health Screening"],
        "experience_years": 11,
        "rating": 4.5,
        "seniority": "GP Partner",
        "availability": {
            "monday": ["08:30", "09:30", "10:30", "14:30", "15:30", "16:30"],
            "tuesday": ["08:30", "09:30", "10:30", "11:30", "14:30", "15:30"],
            "wednesday": ["09:30", "10:30", "11:30", "14:30", "15:30"],
            "thursday": ["08:30", "09:30", "14:30", "15:30", "16:30"],
            "friday": ["08:30", "09:30", "10:30", "11:30"]
        }
    },
    
    "dr_jennifer_lewis": {
        "id": "dr_jennifer_lewis", 
        "name": "Dr. Jennifer Lewis",
        "specialty": "Internal Medicine",
        "email": "j.lewis@salford.nhs.uk",
        "phone": "+44-161-206-2345",
        "hospital": "Salford Royal Hospital",
        "department": "General Medicine",
        "expertise": ["Geriatric Medicine", "Chronic Care", "Palliative Care"],
        "experience_years": 19,
        "rating": 4.7,
        "seniority": "Senior Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "10:00", "15:00"],
            "tuesday": ["09:00", "10:00", "11:00", "14:00", "15:00"],
            "wednesday": ["08:00", "09:00", "14:00", "15:00", "16:00"],
            "thursday": ["09:00", "10:00", "11:00", "15:00"],
            "friday": ["08:00", "09:00", "10:00", "14:00"]
        }
    },
    
    "dr_thomas_walker": {
        "id": "dr_thomas_walker",
        "name": "Dr. Thomas Walker", 
        "specialty": "General Practice",
        "email": "t.walker@oldham.gp.nhs.uk",
        "phone": "+44-161-624-3456",
        "hospital": "Oldham Family Practice",
        "department": "Primary Care",
        "expertise": ["Family Medicine", "Minor Surgery", "Travel Health"],
        "experience_years": 8,
        "rating": 4.4,
        "seniority": "GP",
        "availability": {
            "monday": ["09:00", "10:00", "11:00", "15:00", "16:00"],
            "tuesday": ["08:00", "09:00", "15:00", "16:00", "17:00"],
            "wednesday": ["09:00", "10:00", "11:00", "16:00", "17:00"],
            "thursday": ["08:00", "09:00", "10:00", "15:00"],
            "friday": ["09:00", "10:00", "15:00", "16:00"]
        }
    },
    
    "dr_maria_rodriguez": {
        "id": "dr_maria_rodriguez",
        "name": "Dr. Maria Rodriguez",
        "specialty": "Internal Medicine",
        "email": "m.rodriguez@wythenshawe.nhs.uk", 
        "phone": "+44-161-291-4567",
        "hospital": "Wythenshawe Hospital",
        "department": "General Medicine",
        "expertise": ["Infectious Disease", "Travel Medicine", "Tropical Medicine"],
        "experience_years": 16,
        "rating": 4.8,
        "seniority": "Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "14:00", "15:00"],
            "tuesday": ["09:00", "10:00", "11:00", "15:00", "16:00"],
            "wednesday": ["08:00", "09:00", "10:00", "14:00"],
            "thursday": ["09:00", "10:00", "15:00", "16:00"],
            "friday": ["08:00", "09:00", "10:00", "11:00"]
        }
    },
    
    "dr_kevin_clark": {
        "id": "dr_kevin_clark",
        "name": "Dr. Kevin Clark",
        "specialty": "General Practice",
        "email": "k.clark@stockport.gp.nhs.uk",
        "phone": "+44-161-419-5678",
        "hospital": "Stockport Community Health Centre",
        "department": "Primary Care",
        "expertise": ["Chronic Disease Management", "Mental Health", "Elderly Care"], 
        "experience_years": 12,
        "rating": 4.6,
        "seniority": "GP Partner",
        "availability": {
            "monday": ["08:30", "09:30", "10:30", "15:30", "16:30"],
            "tuesday": ["08:30", "09:30", "14:30", "15:30", "16:30"],
            "wednesday": ["09:30", "10:30", "11:30", "15:30"],
            "thursday": ["08:30", "09:30", "10:30", "14:30", "15:30"],
            "friday": ["08:30", "09:30", "10:30", "11:30", "14:30"]
        }
    },
    
    "dr_linda_young": {
        "id": "dr_linda_young",
        "name": "Dr. Linda Young",
        "specialty": "Internal Medicine",
        "email": "l.young@tameside.nhs.uk",
        "phone": "+44-161-331-6789",
        "hospital": "Tameside General Hospital",
        "department": "Acute Medicine",
        "expertise": ["Acute Medicine", "Hospital Medicine", "Medical Assessment"],
        "experience_years": 10,
        "rating": 4.5,
        "seniority": "Consultant",
        "availability": {
            "monday": ["07:00", "08:00", "18:00", "19:00"],
            "tuesday": ["08:00", "09:00", "18:00", "19:00", "20:00"],
            "wednesday": ["07:00", "08:00", "09:00", "19:00"],
            "thursday": ["08:00", "09:00", "18:00", "19:00"],
            "friday": ["07:00", "08:00", "18:00", "19:00", "20:00"]
        }
    },
    
    "dr_william_scott": {
        "id": "dr_william_scott",
        "name": "Dr. William Scott", 
        "specialty": "General Practice",
        "email": "w.scott@bury.gp.nhs.uk",
        "phone": "+44-161-764-7890",
        "hospital": "Bury Health Centre",
        "department": "Primary Care",
        "expertise": ["Family Medicine", "Women's Health", "Child Health"],
        "experience_years": 15,
        "rating": 4.7,
        "seniority": "GP Partner",
        "availability": {
            "monday": ["08:00", "09:00", "10:00", "14:00", "15:00"],
            "tuesday": ["08:00", "09:00", "14:00", "15:00", "16:00"],
            "wednesday": ["09:00", "10:00", "11:00", "14:00", "15:00"],
            "thursday": ["08:00", "09:00", "10:00", "15:00", "16:00"],
            "friday": ["08:00", "09:00", "10:00", "11:00"]
        }
    },

    # NEUROLOGY - 3 doctors
    "dr_catherine_green": {
        "id": "dr_catherine_green",
        "name": "Dr. Catherine Green",
        "specialty": "Neurologist",
        "email": "c.green@cmft.nhs.uk",
        "phone": "+44-161-276-8901",
        "hospital": "Manchester Royal Infirmary",
        "department": "Neurology",
        "expertise": ["Stroke", "Epilepsy", "Multiple Sclerosis"],
        "experience_years": 17,
        "rating": 4.8,
        "seniority": "Consultant", 
        "availability": {
            "monday": ["09:00", "10:00", "11:00", "15:00"],
            "tuesday": ["08:00", "09:00", "14:00", "15:00"],
            "wednesday": ["09:00", "10:00", "14:00", "15:00", "16:00"],
            "thursday": ["08:00", "09:00", "10:00", "15:00"],
            "friday": ["09:00", "10:00", "11:00"]
        }
    },
    
    "dr_richard_adams": {
        "id": "dr_richard_adams",
        "name": "Dr. Richard Adams",
        "specialty": "Neurologist",
        "email": "r.adams@salford.nhs.uk",
        "phone": "+44-161-206-9012",
        "hospital": "Salford Royal Hospital", 
        "department": "Neurosciences",
        "expertise": ["Movement Disorders", "Parkinson's Disease", "Dementia"],
        "experience_years": 22,
        "rating": 4.9,
        "seniority": "Senior Consultant",
        "availability": {
            "monday": ["08:00", "09:00", "14:00"],
            "tuesday": ["09:00", "10:00", "14:00", "15:00"],
            "wednesday": ["08:00", "09:00", "15:00", "16:00"],
            "thursday": ["09:00", "10:00", "11:00", "14:00"],
            "friday": ["08:00", "09:00", "10:00"]
        }
    },
    
    "dr_barbara_nelson": {
        "id": "dr_barbara_nelson",
        "name": "Dr. Barbara Nelson",
        "specialty": "Neurologist",
        "email": "b.nelson@pennine.nhs.uk",
        "phone": "+44-161-624-0123",
        "hospital": "North Manchester General Hospital",
        "department": "Neurology",
        "expertise": ["Headache", "Migraine", "Neuroimaging"],
        "experience_years": 9,
        "rating": 4.6,
        "seniority": "Consultant",
        "availability": {
            "monday": ["10:00", "11:00", "15:00", "16:00"],
            "tuesday": ["09:00", "10:00", "11:00", "15:00"],
            "wednesday": ["10:00", "11:00", "14:00", "15:00"],
            "thursday": ["09:00", "10:00", "15:00", "16:00"],
            "friday": ["10:00", "11:00", "14:00", "15:00", "16:00"]
        }
    }
}

def get_manchester_doctor_info(doctor_id: str) -> dict:
    """Get information for a specific Manchester doctor"""
    return MANCHESTER_DOCTORS_DATABASE.get(doctor_id)

def get_all_manchester_doctors() -> list:
    """Get all Manchester doctors"""
    return list(MANCHESTER_DOCTORS_DATABASE.values())

def get_doctors_by_specialty(specialty: str) -> list:
    """Get all doctors of a specific specialty"""
    return [doc for doc in MANCHESTER_DOCTORS_DATABASE.values() 
            if doc['specialty'] == specialty]

def get_senior_doctors() -> list:
    """Get senior doctors (Consultants with 15+ years experience)"""
    return [doc for doc in MANCHESTER_DOCTORS_DATABASE.values() 
            if doc['seniority'] in ['Senior Consultant', 'Consultant'] and 
            doc['experience_years'] >= 15]

def get_available_manchester_doctors(day: str, time_slot: str) -> list:
    """Get doctors available at specific day and time"""
    available = []
    for doc in MANCHESTER_DOCTORS_DATABASE.values():
        day_schedule = doc['availability'].get(day.lower(), [])
        if time_slot in day_schedule:
            available.append(doc)
    return available

if __name__ == "__main__":
    print(f"Manchester Doctors Database: {len(MANCHESTER_DOCTORS_DATABASE)} doctors")
    
    # Print summary by specialty
    specialties = {}
    for doc in MANCHESTER_DOCTORS_DATABASE.values():
        specialty = doc['specialty']
        specialties[specialty] = specialties.get(specialty, 0) + 1
    
    print("\nDoctors by Specialty:")
    for specialty, count in specialties.items():
        print(f"  {specialty}: {count} doctors")
    
    print(f"\nSenior Doctors: {len(get_senior_doctors())} doctors")
    print(f"Emergency Medicine Doctors: {len(get_doctors_by_specialty('Emergency Medicine'))} doctors")
