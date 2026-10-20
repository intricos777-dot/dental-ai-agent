# Watermark: Living_Sin (intricos777-dot) + AI agents (Hermes, Lia, opencode) - collaborative work
# Copyright (c) 2026 Living Sin (intricos777-dot) + AI agents (Hermes, Lia, opencode) - collaborative work
# Licensed under Living Sin Proprietary License (LSPL-1.0)
# See LICENSE file for details.
"""LLM client for the dental AI agent."""
from __future__ import annotations

import json
from typing import Any

import httpx

from .config import PracticeConfig


class SimpleLLMClient:
    """Rule-based fallback LLM client.

    Used when Ollama is unavailable. Provides canned responses
    based on intent detection — good for demos without GPU.
    """

    def __init__(self, config: PracticeConfig):
        self.config = config

    def generate(self, system_prompt: str, user_message: str, history: list[dict]) -> str:
        """Generate a simple rule-based response."""
        msg = user_message.lower().strip()

        # Appointment booking intent
        if any(w in msg for w in ["book", "schedule", "make an appointment", "new appointment"]):
            return self._appointment_response()

        # Confirmation intent
        if any(w in msg for w in ["confirm", "yes, i'll be there", "confirming"]):
            return (
                f"Perfect! Your appointment is confirmed. We look forward to seeing you at "
                f"{self.config.name}. If you need to reschedule, just let us know. Have a great day!"
            )

        # Cancellation intent
        if any(w in msg for w in ["cancel", "can't make it", "need to cancel"]):
            return (
                "I'm sorry to hear you can't make it. I can help you reschedule. "
                "What day and time works better for you? We're open:\n"
                + self.config.format_hours()
            )

        # Rescheduling intent
        if any(w in msg for w in ["reschedule", "change", "different time", "move"]):
            return (
                "No problem at all! I'd be happy to find a new time for you. "
                "What day and time would work better? Here are our hours:\n"
                + self.config.format_hours()
            )

        # Insurance intent
        if any(w in msg for w in ["insurance", "coverage", "plan"]):
            plans = ", ".join(self.config.insurance_plans[:4])
            return (
                f"We accept most major insurance plans including {plans}, and more. "
                f"Do you have a specific plan you'd like me to check? "
                f"You can also call us at {self.config.phone} for detailed coverage questions."
            )

        # Cost/pricing intent
        if any(w in msg for w in ["cost", "price", "how much", "fee"]):
            return (
                "Costs vary depending on the treatment needed. A typical checkup and "
                "cleaning ranges from $100-$300 without insurance. For specific pricing, "
                f"I'd recommend scheduling a consultation. Would you like to book one?"
            )

        # Services intent
        if any(w in msg for w in ["service", "treatment", "do you offer", "specialty"]):
            services = "\n".join(f"- {s}" for s in self.config.services[:6])
            return (
                f"At {self.config.name}, we offer a full range of dental services:\n{services}\n"
                "Is there a specific service you're interested in?"
            )

        # Doctor intent
        if any(w in msg for w in ["doctor", "dr.", "who", "dentist"]):
            docs = "\n".join(f"- {d.name} ({d.specialty})" for d in self.config.doctors)
            return f"Our dental team:\n{docs}\nWould you like to see a specific doctor?"

        # Hours intent
        if any(w in msg for w in ["hour", "open", "when", "time"]):
            return (
                f"Our office hours are:\n{self.config.format_hours()}\n"
                "Would you like to schedule an appointment?"
            )

        # Greeting intent
        if any(w in msg for w in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return (
                f"Hello! Welcome to {self.config.name}. I'm your AI receptionist. "
                "I can help you with appointment scheduling, rescheduling, "
                "answer questions about our services, or help with new patient intake. "
                "How can I help you today?"
            )

        # Emergency
        if any(w in msg for w in ["emergency", "pain", "urgent", "swelling", "bleeding"]):
            return (
                "I'm sorry you're in pain! For dental emergencies, please call us immediately "
                f"at {self.config.phone}. If it's after hours and you're experiencing severe "
                "pain, swelling, or bleeding, please visit your nearest emergency room."
            )

        # Intake/new patient
        if any(w in msg for w in ["new patient", "intake", "first time", "registration"]):
            return (
                "Welcome! We'd love to have you as a new patient. I can help get you started. "
                "I'll need your full name, date of birth, phone number, and insurance information "
                "(if you have it). What's your name?"
            )

        # Default
        return (
            "I'd be happy to help with that! I can assist with scheduling appointments, "
            "rescheduling, answering questions about our services, insurance, or help "
            "with new patient intake. What would you like to do?"
        )

    def _appointment_response(self) -> str:
        return (
            "I'd be happy to help you schedule an appointment! Here's what I need:\n"
            "1. Are you a new or existing patient?\n"
            "2. What type of service do you need?\n"
            "3. What day/time works best for you?\n\n"
            f"Our office hours are:\n{self.config.format_hours()}\n\n"
            "Or if you prefer, you can call us directly at {self.config.phone}."
        )


class OllamaClient:
    """Client for Ollama local LLM."""

    def __init__(self, config: PracticeConfig):
        self.config = config
        self.base_url = config.ollama_host.rstrip("/")
        self.model = config.ollama_model

    def generate(self, system_prompt: str, user_message: str, history: list[dict]) -> str:
        """Generate a response using Ollama."""
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (limited)
        for turn in history[-10:]:
            if turn.get("role") in ("user", "assistant"):
                messages.append(turn)

        messages.append({"role": "user", "content": user_message})

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
        except Exception as e:
            # Fall back to simple client on any error
            fallback = SimpleLLMClient(self.config)
            return fallback.generate(system_prompt, user_message, history)

    def is_available(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


def get_llm_client(config: PracticeConfig) -> SimpleLLMClient | OllamaClient:
    """Factory: returns the appropriate LLM client based on config."""
    if config.llm_backend == "ollama":
        client = OllamaClient(config)
        if client.is_available():
            return client
        print("[dental-ai] Ollama not available, falling back to rule-based responses")
    return SimpleLLMClient(config)
