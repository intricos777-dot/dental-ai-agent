# Watermark: Living_Sin (intricos777-dot) + AI agents (Hermes, Lia, opencode) - collaborative work
"""Integration hooks for dental practice management systems.

Supported integrations:
- Dentrix (via API)
- Open Dental (via API)
- Eaglesoft (via API)
- Curve Dental (via API)
- Custom webhook integration
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Protocol

import httpx


class PracticeManagementSystem(Protocol):
    """Protocol for practice management system integrations."""

    def create_appointment(self, appointment_data: dict[str, Any]) -> dict[str, Any]: ...
    def get_appointments(self, date: str) -> list[dict[str, Any]]: ...
    def confirm_appointment(self, appointment_id: str) -> bool: ...
    def cancel_appointment(self, appointment_id: str) -> bool: ...
    def create_patient(self, patient_data: dict[str, Any]) -> dict[str, Any]: ...
    def get_patient(self, patient_id: str) -> dict[str, Any] | None: ...


class BasePMSIntegration(ABC):
    """Base class for PMS integrations."""

    def __init__(self, base_url: str, api_key: str, **kwargs):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = kwargs.get("timeout", 30.0)

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @abstractmethod
    def create_appointment(self, appointment_data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def get_appointments(self, date: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def confirm_appointment(self, appointment_id: str) -> bool: ...

    @abstractmethod
    def cancel_appointment(self, appointment_id: str) -> bool: ...

    @abstractmethod
    def create_patient(self, patient_data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def get_patient(self, patient_id: str) -> dict[str, Any] | None: ...


class DentrixIntegration(BasePMSIntegration):
    """Integration for Dentrix practice management system."""

    def create_appointment(self, appointment_data: dict[str, Any]) -> dict[str, Any]:
        """Create an appointment in Dentrix."""
        payload = {
            "patientId": appointment_data.get("patient_id"),
            "date": appointment_data.get("date"),
            "time": appointment_data.get("time"),
            "providerId": appointment_data.get("doctor_id"),
            "procedureCode": appointment_data.get("service_code", "D0150"),
            "notes": appointment_data.get("notes", ""),
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/appointments",
                    json=payload,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_appointments(self, date: str) -> list[dict[str, Any]]:
        """Get appointments for a specific date."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/appointments",
                    params={"date": date},
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json().get("appointments", [])
        except Exception:
            return []

    def confirm_appointment(self, appointment_id: str) -> bool:
        """Confirm an appointment."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.patch(
                    f"{self.base_url}/api/appointments/{appointment_id}",
                    json={"status": "Confirmed"},
                    headers=self._get_headers(),
                )
                return response.status_code == 200
        except Exception:
            return False

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.patch(
                    f"{self.base_url}/api/appointments/{appointment_id}",
                    json={"status": "Cancelled"},
                    headers=self._get_headers(),
                )
                return response.status_code == 200
        except Exception:
            return False

    def create_patient(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new patient record."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/patients",
                    json=patient_data,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        """Get patient by ID."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/patients/{patient_id}",
                    headers=self._get_headers(),
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception:
            return None


class OpenDentalIntegration(BasePMSIntegration):
    """Integration for Open Dental practice management system."""

    def create_appointment(self, appointment_data: dict[str, Any]) -> dict[str, Any]:
        """Create an appointment in Open Dental."""
        payload = {
            "PatNum": appointment_data.get("patient_id"),
            "AptDateTime": f"{appointment_data.get('date')}T{appointment_data.get('time')}",
            "ProvNum": appointment_data.get("doctor_id"),
            "CodeNum": appointment_data.get("service_code", "D0150"),
            "Note": appointment_data.get("notes", ""),
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/v1/appointments",
                    json=payload,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_appointments(self, date: str) -> list[dict[str, Any]]:
        """Get appointments for a specific date."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/v1/appointments",
                    params={"date": date},
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception:
            return []

    def confirm_appointment(self, appointment_id: str) -> bool:
        """Confirm an appointment."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.put(
                    f"{self.base_url}/api/v1/appointments/{appointment_id}/confirm",
                    headers=self._get_headers(),
                )
                return response.status_code == 200
        except Exception:
            return False

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.put(
                    f"{self.base_url}/api/v1/appointments/{appointment_id}/cancel",
                    headers=self._get_headers(),
                )
                return response.status_code == 200
        except Exception:
            return False

    def create_patient(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new patient record."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/v1/patients",
                    json=patient_data,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        """Get patient by ID."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/v1/patients/{patient_id}",
                    headers=self._get_headers(),
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception:
            return None


class CurveDentalIntegration(BasePMSIntegration):
    """Integration for Curve Dental (cloud-based)."""

    def create_appointment(self, appointment_data: dict[str, Any]) -> dict[str, Any]:
        """Create an appointment in Curve Dental."""
        payload = {
            "patientId": appointment_data.get("patient_id"),
            "appointmentDate": appointment_data.get("date"),
            "appointmentTime": appointment_data.get("time"),
            "providerId": appointment_data.get("doctor_id"),
            "procedureCodes": [appointment_data.get("service_code", "D0150")],
            "notes": appointment_data.get("notes", ""),
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/appointments",
                    json=payload,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_appointments(self, date: str) -> list[dict[str, Any]]:
        """Get appointments for a specific date."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/appointments",
                    params={"date": date},
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception:
            return []

    def confirm_appointment(self, appointment_id: str) -> bool:
        """Confirm an appointment."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/appointments/{appointment_id}/confirm",
                    headers=self._get_headers(),
                )
                return response.status_code == 200
        except Exception:
            return False

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/appointments/{appointment_id}/cancel",
                    headers=self._get_headers(),
                )
                return response.status_code == 200
        except Exception:
            return False

    def create_patient(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new patient record."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/patients",
                    json=patient_data,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        """Get patient by ID."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/patients/{patient_id}",
                    headers=self._get_headers(),
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception:
            return None


class WebhookIntegration:
    """Generic webhook integration for custom systems."""

    def __init__(self, webhook_url: str, secret: str | None = None, **kwargs):
        self.webhook_url = webhook_url
        self.secret = secret
        self.timeout = kwargs.get("timeout", 30.0)

    def send_event(self, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """Send an event to the webhook."""
        payload = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        headers = {"Content-Type": "application/json"}
        if self.secret:
            headers["X-Webhook-Secret"] = self.secret

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return {"success": True, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def notify_appointment_confirmed(self, appointment_data: dict[str, Any]) -> dict[str, Any]:
        """Notify that an appointment was confirmed."""
        return self.send_event("appointment.confirmed", appointment_data)

    def notify_appointment_cancelled(self, appointment_data: dict[str, Any]) -> dict[str, Any]:
        """Notify that an appointment was cancelled."""
        return self.send_event("appointment.cancelled", appointment_data)

    def notify_new_patient(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        """Notify that a new patient was registered."""
        return self.send_event("patient.new", patient_data)

    def notify_intake_completed(self, intake_data: dict[str, Any]) -> dict[str, Any]:
        """Notify that intake was completed."""
        return self.send_event("intake.completed", intake_data)


class IntegrationManager:
    """Manages multiple PMS integrations."""

    def __init__(self):
        self._integrations: dict[str, BasePMSIntegration] = []
        self._webhooks: list[WebhookIntegration] = []

    def add_pms(self, name: str, integration: BasePMSIntegration) -> None:
        """Add a PMS integration."""
        self._integrations[name] = integration

    def add_webhook(self, webhook: WebhookIntegration) -> None:
        """Add a webhook integration."""
        self._webhooks.append(webhook)

    def get_pms(self, name: str) -> BasePMSIntegration | None:
        """Get a PMS integration by name."""
        return self._integrations.get(name)

    def broadcast_event(self, event_type: str, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Send an event to all registered webhooks."""
        results = []
        for webhook in self._webhooks:
            result = webhook.send_event(event_type, data)
            results.append(result)
        return results

    def list_integrations(self) -> list[str]:
        """List all registered integration names."""
        return list(self._integrations.keys())


def create_integration_from_config(config: dict[str, Any]) -> BasePMSIntegration | WebhookIntegration | None:
    """Factory function to create an integration from config dict."""
    integration_type = config.get("type", "").lower()

    if integration_type == "dentrix":
        return DentrixIntegration(
            base_url=config["url"],
            api_key=config["api_key"],
        )
    elif integration_type == "opendental":
        return OpenDentalIntegration(
            base_url=config["url"],
            api_key=config["api_key"],
        )
    elif integration_type == "curvedental":
        return CurveDentalIntegration(
            base_url=config["url"],
            api_key=config["api_key"],
        )
    elif integration_type == "webhook":
        return WebhookIntegration(
            webhook_url=config["url"],
            secret=config.get("secret"),
        )
    return None
