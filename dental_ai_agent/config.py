# Watermark: Living_Sin (intricos777-dot) + AI agents (Hermes, Lia, opencode) - collaborative work
"""Configuration management for the dental AI agent."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DoctorConfig:
    name: str
    specialty: str = "General Dentistry"
    available_days: list[str] = field(default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri"])


@dataclass
class PracticeConfig:
    """Configuration for a dental practice."""

    name: str = "Bright Smile Dental"
    phone: str = "(555) 123-4567"
    email: str = "info@brightsmiledental.com"
    address: str = "123 Main Street, Suite 100, Anytown, USA 12345"

    # Operating hours: day -> (open, close) in 24h format
    hours: dict[str, tuple[str, str]] = field(default_factory=lambda: {
        "Mon": ("08:00", "17:00"),
        "Tue": ("08:00", "17:00"),
        "Wed": ("08:00", "17:00"),
        "Thu": ("08:00", "17:00"),
        "Fri": ("08:00", "16:00"),
        "Sat": ("09:00", "13:00"),
        "Sun": (None, None),
    })

    services: list[str] = field(default_factory=lambda: [
        "General Checkup & Cleaning",
        "Teeth Whitening",
        "Dental Fillings",
        "Root Canal Treatment",
        "Tooth Extraction",
        "Dental Crowns & Bridges",
        "Dental Implants",
        "Orthodontics (Braces/Invisalign)",
        "Pediatric Dentistry",
        "Periodontal Treatment",
    ])

    doctors: list[DoctorConfig] = field(default_factory=lambda: [
        DoctorConfig(name="Dr. Sarah Johnson", specialty="General Dentistry"),
        DoctorConfig(name="Dr. Michael Chen", specialty="Orthodontics"),
        DoctorConfig(name="Dr. Emily Rodriguez", specialty="Pediatric Dentistry"),
    ])

    # Insurance plans accepted
    insurance_plans: list[str] = field(default_factory=lambda: [
        "Delta Dental",
        "Cigna Dental",
        "Aetna Dental",
        "MetLife Dental",
        "UnitedHealthcare Dental",
        "Guardian Dental",
    ])

    # LLM settings
    llm_backend: str = "ollama"  # "ollama" or "simple"
    ollama_model: str = "llama3.2:latest"
    ollama_host: str = "http://localhost:11434"

    # Agent behavior
    max_conversation_turns: int = 20
    confirmation_required: bool = True
    collect_insurance_info: bool = True

    # Integration settings
    integrations: dict[str, Any] = field(default_factory=dict)

    def is_open(self, day: str) -> bool:
        """Check if the practice is open on a given day."""
        if day not in self.hours:
            return False
        open_time, close_time = self.hours[day]
        return open_time is not None and close_time is not None

    def format_hours(self) -> str:
        """Return a human-readable string of operating hours."""
        day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        lines = []
        for day in day_order:
            if day in self.hours:
                open_time, close_time = self.hours[day]
                if open_time and close_time:
                    lines.append(f"{day}: {open_time} - {close_time}")
                else:
                    lines.append(f"{day}: Closed")
        return "\n".join(lines)


def load_config(path: str | Path | None = None) -> PracticeConfig:
    """Load practice configuration from a YAML file.

    If no path is given, checks DENTAL_AI_CONFIG env var, then defaults.
    """
    if path is None:
        env_path = os.environ.get("DENTAL_AI_CONFIG")
        if env_path:
            path = env_path
        else:
            return PracticeConfig()

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    doctors_raw = data.pop("doctors", [])
    doctors = [DoctorConfig(**d) for d in doctors_raw]

    return PracticeConfig(doctors=doctors, **data)


def save_default_config(path: str | Path) -> None:
    """Write a default configuration file to the given path."""
    config = PracticeConfig()
    data = {
        "name": config.name,
        "phone": config.phone,
        "email": config.email,
        "address": config.address,
        "hours": {k: list(v) for k, v in config.hours.items()},
        "services": config.services,
        "doctors": [
            {"name": d.name, "specialty": d.specialty, "available_days": d.available_days}
            for d in config.doctors
        ],
        "insurance_plans": config.insurance_plans,
        "llm_backend": config.llm_backend,
        "ollama_model": config.ollama_model,
        "ollama_host": config.ollama_host,
        "max_conversation_turns": config.max_conversation_turns,
        "confirmation_required": config.confirmation_required,
        "collect_insurance_info": config.collect_insurance_info,
        "integrations": config.integrations,
    }
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
