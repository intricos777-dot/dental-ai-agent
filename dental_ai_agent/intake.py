"""Patient intake screening module."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntakeForm:
    """Multi-step new patient intake form."""

    current_field: str = "full_name"
    data: dict[str, str] = field(default_factory=dict)
    _field_prompts: dict[str, str] = field(default_factory=dict, repr=False)
    _required_fields: list[str] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self._field_prompts = {
            "full_name": "What is your full name?",
            "date_of_birth": "What is your date of birth? (e.g., MM/DD/YYYY)",
            "phone": "What's your phone number?",
            "email": "What's your email address? (optional — press skip)",
            "address": "What's your home address?",
            "insurance_provider": "Do you have dental insurance? If yes, who's the provider?",
            "insurance_member_id": "What's your member ID? (or type 'skip')",
            "emergency_contact": "Who should we contact in case of emergency? (name and phone)",
            "reason_for_visit": "What brings you in today? (e.g., checkup, specific concern)",
            "medical_history": "Do you have any medical conditions we should know about? (e.g., diabetes, heart conditions)",
            "medications": "Are you currently taking any medications? If yes, please list them.",
            "allergies": "Do you have any allergies? (especially to medications, latex, or anesthesia)",
            "previous_dentist": "Did you have a previous dentist? If yes, may we request your records?",
            "additional_notes": "Anything else you'd like us to know? (or type 'done')",
        }
        self._required_fields = ["full_name", "phone", "reason_for_visit"]

    def process_answer(self, answer: str) -> str | None:
        """Process an answer and return the next question prompt, or None if complete."""
        answer = answer.strip()
        field = self.current_field

        # Handle skip for optional fields
        if answer.lower() in ("skip", "n/a", "none", "no"):
            self.data[field] = "N/A"
        else:
            self.data[field] = answer

        # Determine next field
        all_fields = list(self._field_prompts.keys())
        if field in all_fields:
            current_idx = all_fields.index(field)
            # Find next non-completed field
            for next_field in all_fields[current_idx + 1:]:
                if next_field not in self.data:
                    self.current_field = next_field
                    return self._field_prompts[next_field]

        # All fields complete
        self.current_field = "complete"
        return None

    def is_complete(self) -> bool:
        """Check if intake is complete (all fields filled or user finished)."""
        return self.current_field == "complete"

    def all_required_filled(self) -> bool:
        """Check if all required fields are filled."""
        return all(f in self.data for f in self._required_fields)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the collected intake data."""
        return {
            "patient_name": self.data.get("full_name", "Unknown"),
            "contact": {
                "phone": self.data.get("phone", ""),
                "email": self.data.get("email", ""),
                "address": self.data.get("address", ""),
            },
            "insurance": {
                "provider": self.data.get("insurance_provider", "None"),
                "member_id": self.data.get("insurance_member_id", "N/A"),
            },
            "medical": {
                "conditions": self.data.get("medical_history", "None reported"),
                "medications": self.data.get("medications", "None reported"),
                "allergies": self.data.get("allergies", "None reported"),
            },
            "dental": {
                "reason": self.data.get("reason_for_visit", "Checkup"),
                "previous_dentist": self.data.get("previous_dentist", "None"),
                "notes": self.data.get("additional_notes", ""),
            },
            "emergency_contact": self.data.get("emergency_contact", "Not provided"),
        }

    def to_dict(self) -> dict[str, str]:
        """Return raw collected data."""
        return self.data.copy()


class IntakeScreener:
    """Screens intake forms for completeness and flags."""

    @staticmethod
    def screen(form: IntakeForm) -> list[str]:
        """Screen intake form and return any alerts/flags."""
        alerts = []
        data = form.data

        # Check for common medical flags
        medical = data.get("medical_history", "").lower()
        if any(term in medical for term in ["diabetes", "heart", "blood pressure", "hypertension"]):
            alerts.append("⚠️ Medical condition noted — doctor review required")

        allergies = data.get("allergies", "").lower()
        if any(term in allergies for term in ["latex", "anesthesia", "penicillin"]):
            alerts.append("⚠️ Allergy alert — ensure flagged in patient record")

        medications = data.get("medications", "").lower()
        if any(term in medications for term in ["blood thinner", "warfarin", "heparin"]):
            alerts.append("⚠️ Blood thinner noted — important for procedures")

        return alerts
