"""Small client for the local Rasa REST webhook used by the Streamlit demo."""

import os
from typing import Any, List, Optional

import requests


class RasaRestError(RuntimeError):
    """A user-safe error communicating with the Rasa REST channel."""


class RasaRestClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        session: Optional[Any] = None,
    ):
        configured_url = base_url or os.environ.get(
            "RASA_REST_URL", "http://localhost:5005"
        )
        configured_url = configured_url.rstrip("/")
        if not configured_url.endswith("/webhooks/rest/webhook"):
            configured_url += "/webhooks/rest/webhook"
        self.endpoint = configured_url
        self.timeout = timeout
        self.session = session or requests

    def send_message(self, sender: str, message: str) -> List[str]:
        if not isinstance(sender, str) or not sender.strip():
            raise ValueError("A non-empty sender ID is required.")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("A non-empty message is required.")

        try:
            response = self.session.post(
                self.endpoint,
                json={"sender": sender, "message": message},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            if status is None:
                status = getattr(locals().get("response"), "status_code", "unknown")
            raise RasaRestError(f"Rasa returned an HTTP {status} server error.") from None
        except requests.RequestException:
            raise RasaRestError(
                "Cannot connect to Rasa. Check that the Rasa server is running."
            ) from None

        try:
            payload = response.json()
        except (ValueError, requests.RequestException):
            raise RasaRestError("Rasa returned an unreadable response.") from None
        if not isinstance(payload, list):
            raise RasaRestError("Rasa returned an unexpected response format.")

        messages = [
            item["text"]
            for item in payload
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ]
        return messages or ["The assistant returned no text response."]
