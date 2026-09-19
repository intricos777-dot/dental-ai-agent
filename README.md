# AI Dental Receptionist

An AI-powered receptionist for dental practices. Handles appointment confirmations, rescheduling, patient intake screening, and FAQ answering — 24/7, at a fraction of the cost of a human receptionist.

**Value Proposition:** $500-$2,000/month per client (replaces 1-2 front-desk staff for after-hours and overflow call handling).

## Features

- **Appointment Confirmations** — Automatically confirm upcoming appointments via chat
- **Rescheduling** — Handle reschedule requests with natural conversation
- **New Patient Intake** — 13-field digital intake form (medical history, insurance, etc.)
- **FAQ Answering** — Insurance, pricing, services, hours, doctor info
- **Emergency Triage** — Detects emergencies and directs appropriately
- **Multi-doctor Support** — Handles multiple providers with different specialties
- **PMS Integration** — Hooks for Dentrix, Open Dental, Curve Dental
- **Webhook Support** — Send events to any external system
- **Local LLM** — Works with Ollama for private, offline operation
- **Demo Mode** — Rule-based fallback for demos without GPU

## Quick Start

### 1. Install

```bash
cd dental-ai-agent
pip install -e .
```

### 2. Run the Demo

```bash
# Automated demo (scripted scenarios)
dental-ai-demo

# Interactive demo (you play the patient)
dental-ai-demo --interactive
```

### 3. Run the API Server

```bash
# With default config
dental-ai-api

# With custom config
dental-ai-api --config /path/to/config.yaml --port 8000
```

### 4. (Optional) Enable Ollama for Smarter Responses

```bash
# Install Ollama from https://ollama.com
ollama pull llama3.2

# The agent will auto-detect Ollama and use it
# Falls back to rule-based responses if Ollama is unavailable
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Send a message to the AI |
| `GET` | `/sessions/{id}` | Get session state |
| `DELETE` | `/sessions/{id}` | Reset session |
| `GET` | `/appointments` | List confirmed appointments |
| `GET` | `/practice` | Get practice info |

### Example API Usage

```bash
# Chat with the AI
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi, I need to reschedule my appointment"}'

# Get practice info
curl http://localhost:8000/practice

# List appointments
curl http://localhost:8000/appointments
```

## Configuration

Copy `config.example.yaml` to `config.yaml` and customize:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your practice details
```

Key settings:
- `name` — Practice name
- `phone`, `email`, `address` — Contact info
- `hours` — Operating hours by day
- `services` — List of services offered
- `doctors` — Provider names and specialties
- `insurance_plans` — Accepted insurance plans
- `llm_backend` — `"ollama"` or `"simple"` (rule-based)
- `ollama_model` — Model name (default: `llama3.2:latest`)

Set `DENTAL_AI_CONFIG` env var to point to your config:
```bash
export DENTAL_AI_CONFIG=/path/to/config.yaml
```

## Integrations

### Practice Management Systems

```python
from dental_ai_agent.integrations import DentrixIntegration, IntegrationManager

# Set up Dentrix integration
dentrix = DentrixIntegration(
    base_url="https://your-practice.dentrix.com",
    api_key="your-api-key"
)

# Use with the chatbot
manager = IntegrationManager()
manager.add_pms("dentrix", dentrix)
```

Supported PMS systems:
- **Dentrix** — Industry leader, large practices
- **Open Dental** — Open-source friendly
- **Curve Dental** — Cloud-based

### Webhooks

```python
from dental_ai_agent.integrations import WebhookIntegration

webhook = WebhookIntegration(
    webhook_url="https://your-system.com/webhooks/dental-ai",
    secret="your-webhook-secret"
)

# Send events
webhook.notify_appointment_confirmed({
    "patient": "John Smith",
    "date": "2025-01-15",
    "time": "10:00"
})
```

## Project Structure

```
dental-ai-agent/
├── dental_ai_agent/
│   ├── __init__.py          # Package exports
│   ├── config.py            # Practice configuration
│   ├── chatbot.py           # Core chatbot logic
│   ├── llm_client.py        # LLM client (Ollama + fallback)
│   ├── intake.py            # Patient intake screening
│   ├── api.py               # FastAPI HTTP server
│   ├── demo.py              # Demo script
│   └── integrations/
│       └── __init__.py      # PMS integrations
├── config.example.yaml      # Example configuration
├── pyproject.toml           # Package metadata
└── README.md                # This file
```

## Client Onboarding Guide

### For Your Dental Practice Clients

1. **Initial Setup (30 min)**
   - Copy `config.example.yaml` → `config.yaml`
   - Fill in practice details (name, hours, doctors, services)
   - Set up integrations (PMS API keys, webhooks)

2. **Deployment Options**
   - **Local server** — Run on an office computer
   - **Cloud VM** — Deploy to AWS/DigitalOcean for 24/7 uptime
   - **Docker** — Containerized deployment (Dockerfile coming soon)

3. **Integration Points**
   - **Website chat widget** — Connect `/chat` endpoint to frontend
   - **SMS/voice** — Use Twilio integration (coming soon)
   - **PMS sync** — Auto-create appointments in Dentrix/Open Dental

4. **Customization**
   - Edit system prompt in `chatbot.py` for tone/style
   - Add custom services, insurance plans in config
   - Modify intake form fields in `intake.py`

5. **Pricing Tiers**
   - **Starter ($500/mo)** — Rule-based, website chat only
   - **Professional ($1,000/mo)** — Ollama LLM, PMS integration
   - **Enterprise ($2,000/mo)** — Multi-location, custom model, priority support

## Development

```bash
# Install dev dependencies
pip install -e ".[dev,ollama]"

# Run tests
pytest

# Run with auto-reload
dental-ai-api --reload
```

## License

MIT
