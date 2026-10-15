"""End-to-end NLU and dialogue checks against the latest trained Rasa model."""

import asyncio
import unittest
from pathlib import Path

try:
    from rasa.core.agent import Agent
except ModuleNotFoundError as error:
    if error.name != "rasa":
        raise
    Agent = None


MODEL_FILES = sorted(
    Path("models").glob("*.tar.gz"), key=lambda path: path.stat().st_mtime
)


@unittest.skipUnless(Agent is not None and MODEL_FILES, "train a Rasa model first")
class RasaConversationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = Agent.load(str(MODEL_FILES[-1]))

    def parse(self, message):
        return asyncio.run(self.agent.parse_message(message))

    def converse(self, message, sender_id):
        return asyncio.run(self.agent.handle_text(message, sender_id=sender_id))

    def test_unusual_help_request_falls_back_instead_of_answering_returns(self):
        message = "Can you help me with something unusual?"
        parsed = self.parse(message)
        self.assertEqual(parsed["intent"]["name"], "nlu_fallback")

        replies = self.converse(message, "unusual-help-regression")
        self.assertEqual(
            replies,
            [{"recipient_id": "unusual-help-regression", "text":
              "I can help with returns or order tracking. What would you like to know?"}],
        )
        self.assertNotIn("return policy", replies[0]["text"].lower())

    def test_unrelated_questions_receive_store_scope_guidance(self):
        for index, message in enumerate(
            (
                "What is the capital of France?",
                "Tell me a joke",
                "Book me a flight to Cairo",
            )
        ):
            with self.subTest(message=message):
                reply = self.converse(message, "unrelated-{}".format(index))
                self.assertEqual(len(reply), 1)
                self.assertIn("returns or order tracking", reply[0]["text"])

    def test_supported_intents_and_responses_keep_their_routes(self):
        expected_intents = {
            "Hello!": "greet",
            "See you later": "goodbye",
            "What is your return policy?": "ask_return_policy",
            "Where is my order?": "track_order",
            "Are you a real person?": "bot_challenge",
        }
        for message, intent in expected_intents.items():
            with self.subTest(message=message):
                self.assertEqual(self.parse(message)["intent"]["name"], intent)

        expected_responses = {
            "Hello!": ("hello!", "hi there!"),
            "See you later": ("goodbye!", "take care,"),
            "What is your return policy?": ("most unused items can be returned",),
            "Are you a real person?": ("virtual assistant",),
        }
        for index, (message, response_fragment) in enumerate(expected_responses.items()):
            with self.subTest(response_for=message):
                replies = self.converse(message, "supported-{}".format(index))
                self.assertEqual(len(replies), 1)
                response_text = replies[0]["text"].lower()
                self.assertTrue(
                    any(fragment in response_text for fragment in response_fragment)
                )


if __name__ == "__main__":
    unittest.main()
