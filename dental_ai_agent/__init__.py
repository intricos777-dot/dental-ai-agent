# Watermark: Living_Sin (intricos777-dot) + AI agents (Hermes, Lia, opencode) - collaborative work
"""AI Dental Receptionist Agent - Main module."""
from .config import PracticeConfig, load_config
from .chatbot import DentalChatbot
from .llm_client import OllamaClient, SimpleLLMClient
from .intake import IntakeScreener

__version__ = "0.1.0"

__all__ = [
    "PracticeConfig",
    "load_config",
    "DentalChatbot",
    "OllamaClient",
    "SimpleLLMClient",
    "IntakeScreener",
]
