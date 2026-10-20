# Watermark: Living_Sin (intricos777-dot) + AI agents (Hermes, Lia, opencode) - collaborative work
"""HTTP API for the dental AI agent.

Provides REST endpoints for:
- Chat interactions
- Appointment management
- Patient intake
- Health checks
"""
from __future__ import annotations

import argparse
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .chatbot import DentalChatbot
from .config import PracticeConfig, load_config


# --- Request/Response Models ---

class ChatRequest(BaseModel):
    message: str = Field(..., description="Patient message")
    session_id: str | None = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    response: str
    intent: str
    session_id: str
    turn: int
    actions: list[dict[str, Any]]
    patient_name: str | None = None


class AppointmentRequest(BaseModel):
    patient_name: str
    date: str
    time: str
    service: str
    doctor: str | None = None


class IntakeSubmission(BaseModel):
    session_id: str
    field: str
    value: str


class HealthResponse(BaseModel):
    status: str
    version: str
    practice_name: str
    llm_backend: str


# --- App Factory ---

def create_app(config: PracticeConfig | None = None) -> FastAPI:
    """Create the FastAPI application."""
    if config is None:
        config = load_config()

    app = FastAPI(
        title="AI Dental Receptionist API",
        description="Automated appointment confirmations, rescheduling, and patient intake",
        version="0.1.0",
    )

    chatbot = DentalChatbot(config)

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            practice_name=config.name,
            llm_backend=config.llm_backend,
        )

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """Send a message to the AI receptionist."""
        session_id = request.session_id or str(uuid.uuid4())
        result = chatbot.chat(request.message, session_id)
        return ChatResponse(**result)

    @app.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get the current state of a conversation session."""
        state = chatbot.get_session_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "session_id": state.session_id,
            "patient_name": state.patient_name,
            "current_intent": state.current_intent,
            "turn_count": state.turn_count,
            "is_new_patient": state.is_new_patient,
        }

    @app.delete("/sessions/{session_id}")
    async def reset_session(session_id: str):
        """Reset a conversation session."""
        chatbot.reset_session(session_id)
        return {"status": "reset", "session_id": session_id}

    @app.get("/appointments")
    async def list_appointments():
        """List all confirmed appointments."""
        appointments = chatbot.get_appointments()
        return {
            "appointments": [
                {
                    "id": a.appointment_id,
                    "patient": a.patient_name,
                    "date": a.date,
                    "time": a.time,
                    "service": a.service,
                    "doctor": a.doctor,
                    "confirmed": a.confirmed,
                }
                for a in appointments.values()
            ]
        }

    @app.get("/practice")
    async def get_practice_info():
        """Get practice information."""
        return {
            "name": config.name,
            "phone": config.phone,
            "email": config.email,
            "address": config.address,
            "hours": {k: list(v) for k, v in config.hours.items()},
            "services": config.services,
            "doctors": [
                {"name": d.name, "specialty": d.specialty}
                for d in config.doctors
            ],
            "insurance_plans": config.insurance_plans,
        }

    return app


def main():
    """Run the API server."""
    parser = argparse.ArgumentParser(description="Dental AI Agent API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--config", type=str, help="Path to config YAML file")
    args = parser.parse_args()

    config = load_config(args.config)
    app = create_app(config)

    import uvicorn
    print(f"\n🦷 AI Dental Receptionist API")
    print(f"   Practice: {config.name}")
    print(f"   LLM Backend: {config.llm_backend}")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   Docs: http://{args.host}:{args.port}/docs\n")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
