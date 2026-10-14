"""Unit tests for the Streamlit demo's Rasa REST client."""

import unittest
from unittest.mock import Mock

import requests

from rasa_rest_client import RasaRestClient, RasaRestError


class RasaRestClientTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.response = Mock()
        self.session.post.return_value = self.response
        self.client = RasaRestClient(
            "http://localhost:5005", timeout=4, session=self.session
        )

    def test_posts_user_message_and_returns_text_replies(self):
        self.response.json.return_value = [
            {"text": "Hello!"},
            {"image": "https://example.invalid/image.png"},
            {"text": "How can I help?"},
        ]

        replies = self.client.send_message("demo-user", "Hi")

        self.session.post.assert_called_once_with(
            "http://localhost:5005/webhooks/rest/webhook",
            json={"sender": "demo-user", "message": "Hi"},
            timeout=4,
        )
        self.assertEqual(replies, ["Hello!", "How can I help?"])

    def test_accepts_a_full_webhook_url_without_duplicating_path(self):
        client = RasaRestClient(
            "http://localhost:5005/webhooks/rest/webhook", session=self.session
        )
        self.response.json.return_value = [{"text": "Hi"}]
        client.send_message("demo-user", "Hi")
        self.assertEqual(
            self.session.post.call_args.args[0],
            "http://localhost:5005/webhooks/rest/webhook",
        )

    def test_connection_failure_is_user_safe(self):
        self.session.post.side_effect = requests.ConnectionError("private detail")
        with self.assertRaisesRegex(RasaRestError, "Check that the Rasa server is running"):
            self.client.send_message("demo-user", "Hi")

    def test_http_error_is_reported_without_response_body(self):
        self.response.status_code = 503
        self.response.raise_for_status.side_effect = requests.HTTPError(
            "private server body", response=self.response
        )
        with self.assertRaisesRegex(RasaRestError, "HTTP 503") as raised:
            self.client.send_message("demo-user", "Hi")
        self.assertNotIn("private server body", str(raised.exception))

    def test_unreadable_or_unexpected_payload_is_reported(self):
        self.response.json.side_effect = ValueError("invalid json")
        with self.assertRaisesRegex(RasaRestError, "unreadable response"):
            self.client.send_message("demo-user", "Hi")

        self.response.json.side_effect = None
        self.response.json.return_value = {"text": "not a list"}
        with self.assertRaisesRegex(RasaRestError, "unexpected response format"):
            self.client.send_message("demo-user", "Hi")

    def test_blank_sender_and_message_are_rejected(self):
        with self.assertRaises(ValueError):
            self.client.send_message(" ", "Hi")
        with self.assertRaises(ValueError):
            self.client.send_message("demo-user", " ")
        self.session.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
