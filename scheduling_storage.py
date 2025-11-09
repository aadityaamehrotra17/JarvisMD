"""
Scheduling Storage Module
Handles persistent storage of appointment requests and confirmations
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class AppointmentRequest:
    """Data class for appointment requests"""
    request_id: str
    patient_id: str
    doctor_id: str
    doctor_name: str
    urgency_level: str
    preferred_slots: List[Dict]
    email_content: str
    status: str
    sent_at: str
    response_received_at: Optional[str] = None
    doctor_response: Optional[str] = None

@dataclass
class ConfirmedAppointment:
    """Data class for confirmed appointments"""
    appointment_id: str
    request_id: str
    patient_id: str
    patient_name: str
    doctor_id: str
    doctor_name: str
    doctor_email: str
    appointment_datetime: str
    case_urgency: str
    status: str
    created_at: str
    calendar_event_id: Optional[str] = None
    notes: Optional[str] = None

class SchedulingStorage:
    """Handles storage and retrieval of scheduling data"""
    
    def __init__(self, base_path: str = "scheduling_data"):
        """
        Initialize storage with base directory path
        
        Args:
            base_path: Base directory for storing scheduling data
        """
        self.base_path = base_path
        self.requests_dir = os.path.join(base_path, "requests")
        self.appointments_dir = os.path.join(base_path, "appointments")
        self.patient_dir = os.path.join(base_path, "patients")
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create storage directories if they don't exist"""
        for directory in [self.base_path, self.requests_dir, 
                         self.appointments_dir, self.patient_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def save_pending_request(self, request_data: Dict, patient_id: str):
        """
        Save a pending appointment request
        
        Args:
            request_data: Dictionary containing request information
            patient_id: Patient identifier
        """
        request_id = request_data["request_id"]
        
        # Convert to AppointmentRequest object for validation
        appointment_request = AppointmentRequest(
            request_id=request_id,
            patient_id=patient_id,
            doctor_id=request_data["doctor_id"],
            doctor_name=request_data["doctor_name"],
            urgency_level=request_data["urgency_level"],
            preferred_slots=request_data.get("preferred_slots", []),
            email_content=request_data["email_content"],
            status=request_data.get("status", "sent"),
            sent_at=request_data.get("sent_at", datetime.now().isoformat())
        )
        
        # Save to requests directory
        request_file = os.path.join(self.requests_dir, f"{request_id}.json")
        with open(request_file, 'w') as f:
            json.dump(asdict(appointment_request), f, indent=2)
        
        # Update patient's request history
        self._update_patient_requests(patient_id, request_id)
        
        print(f"📁 Saved appointment request: {request_id}")
    
    def save_confirmed_appointment(self, appointment_data: Dict, patient_id: str):
        """
        Save a confirmed appointment
        
        Args:
            appointment_data: Dictionary containing appointment information
            patient_id: Patient identifier
        """
        appointment_id = appointment_data["appointment_id"]
        
        # Convert to ConfirmedAppointment object
        confirmed_appointment = ConfirmedAppointment(
            appointment_id=appointment_id,
            request_id=appointment_data.get("request_id", ""),
            patient_id=patient_id,
            patient_name=appointment_data["patient_name"],
            doctor_id=appointment_data["doctor_id"],
            doctor_name=appointment_data["doctor_name"],
            doctor_email=appointment_data.get("doctor_email", ""),
            appointment_datetime=appointment_data["appointment_datetime"],
            case_urgency=appointment_data["case_urgency"],
            status=appointment_data.get("status", "confirmed"),
            created_at=appointment_data.get("created_at", datetime.now().isoformat()),
            calendar_event_id=appointment_data.get("calendar_event_id"),
            notes=appointment_data.get("notes")
        )
        
        # Save to appointments directory
        appointment_file = os.path.join(self.appointments_dir, f"{appointment_id}.json")
        with open(appointment_file, 'w') as f:
            json.dump(asdict(confirmed_appointment), f, indent=2)
        
        # Update patient's appointment history
        self._update_patient_appointments(patient_id, appointment_id)
        
        print(f"📁 Saved confirmed appointment: {appointment_id}")
    
    def get_pending_requests(self, patient_id: Optional[str] = None) -> List[Dict]:
        """
        Get pending appointment requests
        
        Args:
            patient_id: Optional patient ID to filter by
            
        Returns:
            List of pending appointment requests
        """
        pending_requests = []
        
        if not os.path.exists(self.requests_dir):
            return pending_requests
        
        for filename in os.listdir(self.requests_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.requests_dir, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        request_data = json.load(f)
                    
                    # Filter by patient if specified
                    if patient_id and request_data.get("patient_id") != patient_id:
                        continue
                    
                    # Only include pending/sent requests
                    if request_data.get("status") in ["sent", "pending"]:
                        pending_requests.append(request_data)
                
                except (json.JSONDecodeError, IOError) as e:
                    print(f"⚠️ Error reading request file {filename}: {e}")
        
        # Sort by sent date (newest first)
        pending_requests.sort(key=lambda x: x.get("sent_at", ""), reverse=True)
        return pending_requests
    
    def get_confirmed_appointments(self, patient_id: Optional[str] = None) -> List[Dict]:
        """
        Get confirmed appointments
        
        Args:
            patient_id: Optional patient ID to filter by
            
        Returns:
            List of confirmed appointments
        """
        appointments = []
        
        if not os.path.exists(self.appointments_dir):
            return appointments
        
        for filename in os.listdir(self.appointments_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.appointments_dir, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        appointment_data = json.load(f)
                    
                    # Filter by patient if specified
                    if patient_id and appointment_data.get("patient_id") != patient_id:
                        continue
                    
                    appointments.append(appointment_data)
                
                except (json.JSONDecodeError, IOError) as e:
                    print(f"⚠️ Error reading appointment file {filename}: {e}")
        
        # Sort by appointment datetime
        appointments.sort(key=lambda x: x.get("appointment_datetime", ""))
        return appointments
    
    def update_request_status(self, request_id: str, status: str, 
                            doctor_response: Optional[str] = None):
        """
        Update the status of an appointment request
        
        Args:
            request_id: Request identifier
            status: New status (e.g., 'accepted', 'declined', 'pending')
            doctor_response: Optional doctor response message
        """
        request_file = os.path.join(self.requests_dir, f"{request_id}.json")
        
        if os.path.exists(request_file):
            try:
                with open(request_file, 'r') as f:
                    request_data = json.load(f)
                
                request_data["status"] = status
                request_data["response_received_at"] = datetime.now().isoformat()
                
                if doctor_response:
                    request_data["doctor_response"] = doctor_response
                
                with open(request_file, 'w') as f:
                    json.dump(request_data, f, indent=2)
                
                print(f"📝 Updated request {request_id} status to: {status}")
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Error updating request {request_id}: {e}")
        else:
            print(f"⚠️ Request file not found: {request_id}")
    
    def get_patient_history(self, patient_id: str) -> Dict:
        """
        Get complete appointment history for a patient
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Dictionary containing patient's appointment history
        """
        patient_file = os.path.join(self.patient_dir, f"{patient_id}.json")
        
        if os.path.exists(patient_file):
            try:
                with open(patient_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Return empty history if file doesn't exist or can't be read
        return {
            "patient_id": patient_id,
            "appointment_requests": [],
            "confirmed_appointments": [],
            "created_at": datetime.now().isoformat()
        }
    
    def _update_patient_requests(self, patient_id: str, request_id: str):
        """Update patient's request history"""
        patient_history = self.get_patient_history(patient_id)
        
        if request_id not in patient_history["appointment_requests"]:
            patient_history["appointment_requests"].append(request_id)
            patient_history["updated_at"] = datetime.now().isoformat()
            
            patient_file = os.path.join(self.patient_dir, f"{patient_id}.json")
            with open(patient_file, 'w') as f:
                json.dump(patient_history, f, indent=2)
    
    def _update_patient_appointments(self, patient_id: str, appointment_id: str):
        """Update patient's appointment history"""
        patient_history = self.get_patient_history(patient_id)
        
        if appointment_id not in patient_history["confirmed_appointments"]:
            patient_history["confirmed_appointments"].append(appointment_id)
            patient_history["updated_at"] = datetime.now().isoformat()
            
            patient_file = os.path.join(self.patient_dir, f"{patient_id}.json")
            with open(patient_file, 'w') as f:
                json.dump(patient_history, f, indent=2)
    
    def get_storage_stats(self) -> Dict:
        """Get statistics about stored data"""
        stats = {
            "total_requests": 0,
            "pending_requests": 0,
            "confirmed_appointments": 0,
            "unique_patients": 0
        }
        
        # Count requests
        if os.path.exists(self.requests_dir):
            request_files = [f for f in os.listdir(self.requests_dir) if f.endswith('.json')]
            stats["total_requests"] = len(request_files)
            
            # Count pending requests
            pending = self.get_pending_requests()
            stats["pending_requests"] = len(pending)
        
        # Count appointments
        if os.path.exists(self.appointments_dir):
            appointment_files = [f for f in os.listdir(self.appointments_dir) if f.endswith('.json')]
            stats["confirmed_appointments"] = len(appointment_files)
        
        # Count patients
        if os.path.exists(self.patient_dir):
            patient_files = [f for f in os.listdir(self.patient_dir) if f.endswith('.json')]
            stats["unique_patients"] = len(patient_files)
        
        return stats
    
    def cleanup_old_data(self, days_old: int = 30):
        """
        Clean up old appointment data
        
        Args:
            days_old: Remove data older than this many days
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cutoff_iso = cutoff_date.isoformat()
        
        cleaned_files = 0
        
        # Clean old requests
        if os.path.exists(self.requests_dir):
            for filename in os.listdir(self.requests_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.requests_dir, filename)
                    
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        if data.get("sent_at", "") < cutoff_iso:
                            os.remove(file_path)
                            cleaned_files += 1
                    
                    except (json.JSONDecodeError, IOError):
                        continue
        
        print(f"🧹 Cleaned up {cleaned_files} old data files")


# Test functions
if __name__ == "__main__":
    print("🧪 Testing Scheduling Storage Module")
    print("=" * 40)
    
    # Initialize storage
    storage = SchedulingStorage("test_scheduling_data")
    
    # Test saving a request
    test_request = {
        "request_id": "REQ_TEST_001",
        "doctor_id": "dr_james_hartwell",
        "doctor_name": "Dr. James Hartwell",
        "urgency_level": "PRIORITY",
        "preferred_slots": [{"datetime": "2024-11-10T09:00:00", "time": "09:00"}],
        "email_content": "Test appointment request",
        "status": "sent"
    }
    
    storage.save_pending_request(test_request, "patient_test_001")
    
    # Test saving an appointment
    test_appointment = {
        "appointment_id": "APPT_TEST_001",
        "patient_name": "Test Patient",
        "doctor_id": "dr_james_hartwell", 
        "doctor_name": "Dr. James Hartwell",
        "appointment_datetime": "2024-11-10T09:00:00",
        "case_urgency": "PRIORITY"
    }
    
    storage.save_confirmed_appointment(test_appointment, "patient_test_001")
    
    # Test retrieval
    print("\n📊 Storage Statistics:")
    stats = storage.get_storage_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Scheduling Storage tests completed!")
