# Watermark: Living_Sin (intricos777-dot) + AI agents (Hermes, Lia, opencode) - collaborative work
# Copyright (c) 2026 Living Sin (intricos777-dot) + AI agents (Hermes, Lia, opencode) - collaborative work
# Licensed under Living Sin Proprietary License (LSPL-1.0)
# See LICENSE file for details.
"""Demo script for the AI Dental Receptionist.

Shows the agent handling common patient interactions in a terminal demo.
No Ollama required — uses the rule-based fallback for demo purposes.
"""
from __future__ import annotations

import sys
from typing import Any

from .chatbot import DentalChatbot
from .config import PracticeConfig


def print_separator():
    print("\n" + "─" * 60 + "\n")


def run_interactive_demo():
    """Run an interactive terminal demo where you play the patient."""
    config = PracticeConfig()
    bot = DentalChatbot(config)

    print("\n🦷 AI Dental Receptionist — Interactive Demo")
    print("=" * 50)
    print(f"   Practice: {config.name}")
    print(f"   Type your messages as if you're a patient.")
    print(f"   Type 'quit' to exit, 'reset' to start over.\n")

    session_id = "interactive-demo"
    print(f"🤖 AI: Hello! Welcome to {config.name}. I'm your AI receptionist.")
    print("      I can help with scheduling, rescheduling, answer questions")
    print("      about our services, or help with new patient intake.")
    print("      How can I help you today?\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 👋")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\nThank you for trying the demo! 👋\n")
            break
        if user_input.lower() == "reset":
            bot.reset_session(session_id)
            print("\n🤖 AI: Session reset. How can I help you?\n")
            continue

        result = bot.chat(user_input, session_id)
        print(f"\n🤖 AI: {result['response']}")
        print(f"     [intent: {result['intent']}, turn: {result['turn']}]\n")


def run_automated_demo():
    """Run a scripted demo showing all capabilities."""
    config = PracticeConfig()
    bot = DentalChatbot(config)

    demo_scenarios = [
        {
            "title": "📅 SCENARIO 1: Appointment Confirmation",
            "messages": [
                "Hi, I need to confirm my appointment",
                "Yes, I'll be there",
            ],
        },
        {
            "title": "🔄 SCENARIO 2: Rescheduling",
            "messages": [
                "Hi, I'm John Smith. I need to reschedule my appointment",
                "How about Tuesday at 2pm?",
                "Yes, that works",
            ],
        },
        {
            "title": "📋 SCENARIO 3: New Patient Intake",
            "messages": [
                "I'm a new patient and need to register",
                "Jane Marie Wilson",
                "03/15/1990",
                "(555) 987-6543",
                "jane.wilson@email.com",
                "456 Oak Avenue, Springfield",
                "Yes, Delta Dental",
                "MEM123456789",
                "Bob Wilson - (555) 111-2222",
                "I need a checkup and cleaning, I've been having some sensitivity",
                "No major conditions",
                "Ibuprofen occasionally",
                "No allergies",
                "Dr. Smith at Main Street Dental, yes please",
                "Looking forward to meeting the team",
            ],
        },
        {
            "title": "❓ SCENARIO 4: FAQ — Insurance",
            "messages": [
                "Do you accept Cigna insurance?",
            ],
        },
        {
            "title": "❓ SCENARIO 5: FAQ — Pricing",
            "messages": [
                "How much does a root canal cost?",
            ],
        },
        {
            "title": "🚨 SCENARIO 6: Emergency Triage",
            "messages": [
                "I have severe tooth pain and swelling",
            ],
        },
        {
            "title": "👋 SCENARIO 7: Office Hours & Services",
            "messages": [
                "What are your hours on Saturday?",
                "What services do you offer?",
                "Thank you, that's all I needed",
            ],
        },
    ]

    print("\n" + "=" * 60)
    print("🦷 AI Dental Receptionist — Automated Demo")
    print("=" * 60)
    print(f"\n   Practice: {config.name}")
    print(f"   LLM Backend: {config.llm_backend}")
    print(f"   This demo shows the agent handling common scenarios.\n")

    for i, scenario in enumerate(demo_scenarios):
        session_id = f"demo-{i}"
        print_separator()
        print(f"{scenario['title']}\n")

        for message in scenario["messages"]:
            print(f"👤 Patient: {message}")
            result = bot.chat(message, session_id)
            print(f"\n🤖 AI: {result['response']}")
            if result["actions"]:
                print(f"   [actions: {', '.join(a.get('type', '') for a in result['actions'])}]")
            print()

    print_separator()
    print("✅ Demo complete! All scenarios handled successfully.")
    print(f"\n   The agent handled:")
    print("   • Appointment confirmations")
    print("   • Rescheduling")
    print("   • Full new patient intake (13-field form)")
    print("   • Insurance inquiries")
    print("   • Pricing questions")
    print("   • Emergency triage")
    print("   • Office hours & services")
    print()


def main():
    """Entry point for demo script."""
    if "--interactive" in sys.argv or "-i" in sys.argv:
        run_interactive_demo()
    else:
        run_automated_demo()


if __name__ == "__main__":
    main()
