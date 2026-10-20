# Watermark: Living_Sin (intricos777-dot) + AI agents (Hermes, Lia, opencode) - collaborative work
"""Core chatbot interface for the dental AI receptionist."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .config import PracticeConfig
from .llm_client import SimpleLLMClient, get_llm_client
from .intake import IntakeForm, IntakeScreener


@dataclass
class Appointment:
    """Represents a dental appointment."""
    patient_name: str
    date: str
    time: str
    service: str
    doctor: str | None = None
    confirmed: bool = False
    appointment_id: str = ""

    def __post_init__(self):
        if not self.appointment_id:
            import hashlib
            raw = f"{self.patient_name}{self.date}{self.time}"
            self.appointment_id = hashlib.md5(raw.encode()).hexdigest()[:8]


@dataclass
class ConversationState:
    """Tracks the state of a patient conversation."""
    session_id: str = ""
    patient_name: str | None = None
    patient_phone: str | None = None
    is_new_patient: bool | None = None
    current_intent: str = "greeting"
    pending_appointment: Appointment | None = None
    intake_form: IntakeForm | None = None
    turn_count: int = 0
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class DentalChatbot:
    """AI Dental Receptionist chatbot.

    Handles:
    - Appointment confirmations
    - Rescheduling
    - New patient intake screening
    - FAQ answering
    - General inquiries
    """

    def __init__(self, config: PracticeConfig | None = None):
        self.config = config or PracticeConfig()
        self.llm = get_llm_client(config) if config else SimpleLLMClient(self.config)
        self.intake_screener = IntakeScreener()
        self._sessions: dict[str, ConversationState] = {}
        self._appointments: dict[str, Appointment] = {}

    def get_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        doctors_text = "\n".join(
            f"- {d.name} ({d.specialty})" for d in self.config.doctors
        )
        services_text = "\n".join(f"- {s}" for s in self.config.services)
        insurance_text = ", ".join(self.config.insurance_plans)

        return f"""You are a friendly, professional AI receptionist at {self.config.name}.

## Your Role
You help patients with:
1. Scheduling new appointments
2. Confirming existing appointments
3. Rescheduling or canceling appointments
4. New patient intake screening
5. Answering questions about services, hours, insurance, and policies

## Practice Information
- Phone: {self.config.phone}
- Email: {self.config.email}
- Address: {self.config.address}

## Office Hours
{self.config.format_hours()}

## Our Services
{services_text}

## Our Doctors
{doctors_text}

## Insurance Plans We Accept
{insurance_text}

## Guidelines
- Be warm, empathetic, and professional
- Always confirm appointment details before finalizing
- For new patients, collect: full name, DOB, phone, insurance info
- For emergencies, always direct to call the office or go to ER
- If you can't help with something, offer to transfer to a human
- Keep responses concise but helpful
- Use the patient's name when you know it
"""

    def chat(self, message: str, session_id: str = "default") -> dict[str, Any]:
        """Process a message and return a response.

        Args:
            message: The patient's message
            session_id: Unique session identifier for conversation tracking

        Returns:
            Dict with response text, detected intent, and any actions
        """
        state = self._get_or_create_session(session_id)
        state.turn_count += 1

        # Detect intent
        intent = self._detect_intent(message, state)
        state.current_intent = intent

        # Handle specific intents with logic
        response, actions = self._handle_intent(message, intent, state)

        # Update conversation history
        state.conversation_history.append({"role": "user", "content": message})
        state.conversation_history.append({"role": "assistant", "content": response})

        return {
            "response": response,
            "intent": intent,
            "session_id": session_id,
            "turn": state.turn_count,
            "actions": actions,
            "patient_name": state.patient_name,
        }

    def _get_or_create_session(self, session_id: str) -> ConversationState:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationState(session_id=session_id)
        return self._sessions[session_id]

    def _detect_intent(self, message: str, state: ConversationState) -> str:
        """Detect the patient's intent from their message."""
        msg = message.lower().strip()

        # Check for intake form completion
        if state.intake_form and not state.intake_form.is_complete():
            return "intake_continuation"

        # Emergency detection (highest priority)
        if any(w in msg for w in ["emergency", "severe pain", "swelling", "bleeding", "knocked out", "broken tooth"]):
            return "emergency"

        # Confirmation patterns
        if any(w in msg for w in ["confirm", "yes, i'll", "i'll be there", "confirmed", "see you then"]):
            return "confirmation"

        # Cancellation patterns
        if any(w in msg for w in ["cancel", "can't make it", "won't be able", "need to cancel"]):
            return "cancellation"

        # Rescheduling patterns
        if any(w in msg for w in ["reschedule", "change my appointment", "different time", "move my appointment", "new time"]):
            return "rescheduling"

        # New appointment patterns
        if any(w in msg for w in ["book", "schedule", "make an appointment", "new appointment", "set up"]):
            return "new_appointment"

        # New patient intake
        if any(w in msg for w in ["new patient", "intake", "first time", "new client", "registration"]):
            return "intake"

        # Insurance questions
        if any(w in msg for w in ["insurance", "coverage", "plan", "delta", "cigna", "aetna"]):
            return "insurance"

        # Pricing questions
        if any(w in msg for w in ["cost", "price", "how much", "fee", "charge"]):
            return "pricing"

        # Services questions
        if any(w in msg for w in ["service", "treatment", "do you offer", "whitening", "implant", "braces"]):
            return "services"

        # Doctor questions
        if any(w in msg for w in ["doctor", "dr.", "who is", "which dentist"]):
            return "doctors"

        # Hours questions
        if any(w in msg for w in ["hour", "open", "when are you", "what time"]):
            return "hours"

        # Greeting
        if any(w in msg for w in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            return "greeting"

        # Goodbye
        if any(w in msg for w in ["bye", "goodbye", "thank you", "thanks", "that's all"]):
            return "goodbye"

        # Name extraction (if we don't have it yet)
        if not state.patient_name:
            name_match = re.search(r"(?:my name is|i'm|i am|this is)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", message, re.IGNORECASE)
            if name_match:
                state.patient_name = name_match.group(1).strip()
                return "name_provided"

        return "general"

    def _handle_intent(self, message: str, intent: str, state: ConversationState) -> tuple[str, list[dict]]:
        """Handle the detected intent and return response + actions."""
        actions = []

        if intent == "emergency":
            response = (
                f"I'm sorry you're experiencing this! For dental emergencies, please call us "
                f"immediately at {self.config.phone}. If it's after hours and you have severe "
                "pain, swelling, or a knocked-out tooth, please go to your nearest emergency "
                "room or urgent care. Don't wait — dental emergencies need prompt attention."
            )
            actions.append({"type": "emergency_redirect", "phone": self.config.phone})

        elif intent == "confirmation":
            response = self._handle_confirmation(state)
            actions.append({"type": "appointment_confirmed"})

        elif intent == "cancellation":
            response = (
                "I'm sorry you can't make it. I can help you reschedule right now. "
                "What new day and time would work for you? We're open:\n"
                f"{self.config.format_hours()}"
            )
            actions.append({"type": "awaiting_reschedule"})

        elif intent == "rescheduling":
            response = self._handle_rescheduling(message, state)
            actions.append({"type": "reschedule_initiated"})

        elif intent == "new_appointment":
            response = self._handle_new_appointment(message, state)
            actions.append({"type": "appointment_scheduling"})

        elif intent == "intake":
            response, intake_actions = self._handle_intake(state)
            actions.extend(intake_actions)

        elif intent == "intake_continuation":
            response, intake_actions = self._continue_intake(message, state)
            actions.extend(intake_actions)

        elif intent == "insurance":
            plans = ", ".join(self.config.insurance_plans[:5])
            response = (
                f"We accept most major insurance plans including {plans}. "
                f"If you have a specific plan, I can note it in your file. "
                f"For detailed coverage questions, our team can help at {self.config.phone}."
            )

        elif intent == "pricing":
            response = (
                "Treatment costs vary based on your specific needs. Here are some general ranges:\n"
                "- Checkup & Cleaning: $100-$300\n"
                "- Fillings: $150-$400\n"
                "- Crowns: $800-$1,500\n"
                "- Root Canal: $700-$1,200\n"
                "- Teeth Whitening: $300-$600\n\n"
                "With insurance, your out-of-pocket is typically 20-50% less. "
                "Would you like to schedule a consultation for an exact quote?"
            )

        elif intent == "services":
            services = "\n".join(f"- {s}" for s in self.config.services)
            response = (
                f"We offer comprehensive dental services:\n{services}\n\n"
                "Is there a specific service you'd like to know more about?"
            )

        elif intent == "doctors":
            docs = "\n".join(f"- {d.name} ({d.specialty})" for d in self.config.doctors)
            response = (
                f"Our dental team:\n{docs}\n\n"
                "Would you like to schedule with a specific doctor?"
            )

        elif intent == "hours":
            response = (
                f"Our office hours are:\n{self.config.format_hours()}\n\n"
                "Would you like to book an appointment?"
            )

        elif intent == "greeting":
            greeting = f"Hello! Welcome to {self.config.name}. "
            if state.patient_name:
                response = (
                    f"Hi {state.patient_name}! How can I help you today? "
                    "I can assist with appointments, rescheduling, or answer any questions."
                )
            else:
                response = (
                    greeting + "I'm your AI receptionist. I can help with scheduling, "
                    "rescheduling, answer questions about our services, or help with "
                    "new patient intake. How can I help you today?"
                )

        elif intent == "goodbye":
            response = (
                f"Thank you for choosing {self.config.name}! Have a wonderful day. "
                "If you need anything else, we're here for you. 😊"
            )

        elif intent == "name_provided":
            response = (
                f"Nice to meet you, {state.patient_name}! How can I help you today? "
                "I can assist with appointments, rescheduling, or answer questions."
            )

        else:
            # Use LLM for general queries
            response = self.llm.generate(
                self.get_system_prompt(),
                message,
                state.conversation_history,
            )

        return response, actions

    def _handle_confirmation(self, state: ConversationState) -> str:
        """Handle appointment confirmation."""
        if state.pending_appointment:
            state.pending_appointment.confirmed = True
            appt = state.pending_appointment
            self._appointments[appt.appointment_id] = appt
            state.pending_appointment = None
            return (
                f"Perfect! Your appointment is confirmed:\n"
                f"📅 {appt.date} at {appt.time}\n"
                f"🦷 {appt.service}\n"
                f"{'👨‍⚕️ ' + appt.doctor if appt.doctor else ''}\n\n"
                f"We'll send a reminder 24 hours before. If you need to make any changes, "
                f"just let us know. See you then!"
            )
        return (
            "Great! I've noted your confirmation. If you need to make any changes "
            "to your appointment, just let us know. We look forward to seeing you!"
        )

    def _handle_rescheduling(self, message: str, state: ConversationState) -> str:
        """Handle appointment rescheduling."""
        # Try to extract date/time from message
        date_match = re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sun)", message.lower())
        time_match = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", message.lower())

        if date_match or time_match:
            parts = ["I've noted your preferred time:"]
            if date_match:
                parts.append(f"📅 Day: {date_match.group(1).title()}")
            if time_match:
                parts.append(f"⏰ Time: {time_match.group(1)}")
            parts.append("\nLet me check availability and confirm. Is that correct?")
            return "\n".join(parts)

        return (
            "I'd be happy to reschedule your appointment. What new day and time would work for you? "
            f"Our hours are:\n{self.config.format_hours()}"
        )

    def _handle_new_appointment(self, message: str, state: ConversationState) -> str:
        """Handle new appointment booking."""
        # Try to extract details
        service_match = re.search(
            r"(cleaning|checkup|whitening|filling|extraction|root canal|crown|implant|braces|invisalign)",
            message.lower()
        )
        date_match = re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sun)", message.lower())
        time_match = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", message.lower())

        service = service_match.group(1).title() if service_match else "Checkup"
        date = date_match.group(1).title() if date_match else "TBD"
        time = time_match.group(1) if time_match else "TBD"

        # Create pending appointment
        state.pending_appointment = Appointment(
            patient_name=state.patient_name or "Patient",
            date=date,
            time=time,
            service=service,
        )

        return (
            f"I can help you schedule a {service} appointment. Here's what I have so far:\n"
            f"📅 Day: {date}\n"
            f"⏰ Time: {time}\n"
            f"🦷 Service: {service}\n\n"
            f"Shall I go ahead and book this for you?"
        )

    def _handle_intake(self, state: ConversationState) -> tuple[str, list[dict]]:
        """Start new patient intake process."""
        state.intake_form = IntakeForm()
        state.is_new_patient = True
        response = (
            "Welcome! We're excited to have you as a new patient. I'll help get you set up. "
            "This only takes a couple of minutes.\n\n"
            "First, could you tell me your full name?"
        )
        return response, [{"type": "intake_started"}]

    def _continue_intake(self, message: str, state: ConversationState) -> tuple[str, list[dict]]:
        """Continue the intake process."""
        if not state.intake_form:
            return self._handle_intake(state)

        form = state.intake_form
        next_question = form.process_answer(message)

        if next_question:
            return next_question, [{"type": "intake_in_progress", "field": form.current_field}]
        else:
            # Intake complete
            summary = form.get_summary()
            state.patient_name = form.data.get("full_name", state.patient_name)
            response = (
                f"Thank you, {state.patient_name}! Your intake form is complete. ✅\n\n"
                f"I've noted your information. Our team will review it before your first visit. "
                f"Would you like to schedule your first appointment now?"
            )
            return response, [{"type": "intake_complete", "data": summary}]

    def get_session_state(self, session_id: str) -> ConversationState | None:
        """Get the current state of a conversation session."""
        return self._sessions.get(session_id)

    def reset_session(self, session_id: str) -> None:
        """Reset a conversation session."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_appointments(self) -> dict[str, Appointment]:
        """Get all confirmed appointments."""
        return self._appointments.copy()
