"""
WebSocket Manager for Real-time Multi-Agent Workflow Updates
"""

import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

class WorkflowProgressManager:
    def __init__(self):
        # Store active WebSocket connections
        self.active_connections: Set[WebSocket] = set()
        # Store workflow progress for each session
        self.workflow_sessions: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Initialize session if it doesn't exist
        if session_id not in self.workflow_sessions:
            self.workflow_sessions[session_id] = {
                "status": "idle",
                "current_step": None,
                "completed_steps": [],
                "progress_percentage": 0,
                "messages": [],
                "start_time": None,
                "end_time": None
            }
        
        # Send current session state to newly connected client
        await self.send_session_update(websocket, session_id)
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        self.active_connections.discard(websocket)
    
    async def send_session_update(self, websocket: WebSocket, session_id: str):
        """Send current session state to a specific client"""
        try:
            session_data = self.workflow_sessions.get(session_id, {})
            await websocket.send_text(json.dumps({
                "type": "session_update",
                "session_id": session_id,
                "data": session_data
            }))
        except Exception as e:
            print(f"Error sending session update: {e}")
    
    async def broadcast_progress_update(self, session_id: str, update_data: Dict):
        """Broadcast progress update to all connected clients"""
        if session_id in self.workflow_sessions:
            # Update session data
            session = self.workflow_sessions[session_id]
            session.update(update_data)
            session["last_updated"] = datetime.now().isoformat()
            
            # Broadcast to all connected clients
            message = json.dumps({
                "type": "progress_update",
                "session_id": session_id,
                "data": update_data
            })
            
            disconnected = set()
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Error broadcasting to client: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected clients
            self.active_connections -= disconnected
    
    def start_workflow(self, session_id: str, patient_info: Dict):
        """Initialize a new workflow session"""
        self.workflow_sessions[session_id] = {
            "status": "running",
            "current_step": "initializing",
            "completed_steps": [],
            "progress_percentage": 0,
            "messages": [f"Starting workflow for patient: {patient_info.get('name', 'Unknown')}"],
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "patient_info": patient_info,
            "workflow_steps": [
                {"id": "triage", "name": "Case Triage", "status": "pending"},
                {"id": "doctor_matching", "name": "Doctor Matching", "status": "pending"},
                {"id": "appointment_coordination", "name": "Appointment Coordination", "status": "pending"},
                {"id": "doctor_simulation", "name": "Doctor Response Simulation", "status": "pending"},
                {"id": "calendar_integration", "name": "Calendar Integration", "status": "pending"}
            ]
        }
    
    async def update_step_progress(self, session_id: str, step_name: str, status: str, message: str = None, data: Dict = None):
        """Update progress for a specific workflow step"""
        if session_id not in self.workflow_sessions:
            return
        
        session = self.workflow_sessions[session_id]
        
        # Update current step
        session["current_step"] = step_name
        
        # Update workflow steps
        for step in session["workflow_steps"]:
            if step["id"] == step_name:
                step["status"] = status
                if data:
                    step["data"] = data
                break
        
        # Calculate progress percentage
        total_steps = len(session["workflow_steps"])
        completed_steps = len([s for s in session["workflow_steps"] if s["status"] == "completed"])
        session["progress_percentage"] = int((completed_steps / total_steps) * 100)
        
        # Add message
        if message:
            session["messages"].append(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
        
        # Mark step as completed if it's done
        if status == "completed" and step_name not in session["completed_steps"]:
            session["completed_steps"].append(step_name)
        
        # Broadcast update
        await self.broadcast_progress_update(session_id, {
            "current_step": step_name,
            "step_status": status,
            "progress_percentage": session["progress_percentage"],
            "message": message,
            "workflow_steps": session["workflow_steps"]
        })
    
    async def complete_workflow(self, session_id: str, final_result: Dict):
        """Mark workflow as completed"""
        if session_id not in self.workflow_sessions:
            return
        
        session = self.workflow_sessions[session_id]
        session["status"] = "completed"
        session["end_time"] = datetime.now().isoformat()
        session["final_result"] = final_result
        
        # Mark all steps as completed
        for step in session["workflow_steps"]:
            if step["status"] != "completed":
                step["status"] = "completed"
        
        session["progress_percentage"] = 100
        
        completion_message = "Workflow completed successfully"
        if final_result.get("final_appointment"):
            appointment = final_result["final_appointment"]
            completion_message = f"Appointment scheduled with Dr. {appointment['doctor_name']}"
        elif final_result.get("health_recommendations"):
            completion_message = "Health recommendations provided for low-risk case"
        
        session["messages"].append(f"{datetime.now().strftime('%H:%M:%S')} - {completion_message}")
        
        await self.broadcast_progress_update(session_id, {
            "status": "completed",
            "progress_percentage": 100,
            "message": completion_message,
            "final_result": final_result
        })
    
    async def workflow_error(self, session_id: str, error_message: str):
        """Handle workflow errors"""
        if session_id not in self.workflow_sessions:
            return
        
        session = self.workflow_sessions[session_id]
        session["status"] = "error"
        session["end_time"] = datetime.now().isoformat()
        session["messages"].append(f"{datetime.now().strftime('%H:%M:%S')} - ERROR: {error_message}")
        
        await self.broadcast_progress_update(session_id, {
            "status": "error",
            "message": f"Workflow failed: {error_message}"
        })

# Global instance
workflow_manager = WorkflowProgressManager()
