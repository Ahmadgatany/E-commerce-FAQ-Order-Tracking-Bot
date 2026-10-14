"""Custom action tests; skipped when the optional Rasa SDK is not installed."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

try:
    from actions import ActionTrackOrder, ValidateTrackOrderForm
    from order_repository import OrderRepository
    from scripts.init_db import initialize_database
except ModuleNotFoundError as error:
    if error.name != "rasa_sdk":
        raise
    ActionTrackOrder = None
    ValidateTrackOrderForm = None
    OrderRepository = None
    initialize_database = None


class DummyTracker:
    def __init__(self, order_id=None):
        self.order_id = order_id

    def get_slot(self, name):
        return self.order_id if name == "order_id" else None


@unittest.skipIf(ActionTrackOrder is None, "requires the pinned rasa-sdk dependency")
class OrderActionTests(unittest.TestCase):
    def setUp(self):
        self.dispatcher = Mock()
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "orders.sqlite3"
        initialize_database(self.database_path)
        self.repository = OrderRepository(self.database_path)
        self.repository.get_order = Mock(wraps=self.repository.get_order)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_valid_order_id_is_normalized(self):
        result = ValidateTrackOrderForm().validate_order_id(
            " ord-10482 ", self.dispatcher, DummyTracker(), {}
        )
        self.assertEqual(result, {"order_id": "ORD-10482"})
        self.dispatcher.utter_message.assert_not_called()

    def test_invalid_order_id_is_rejected_and_cleared(self):
        result = ValidateTrackOrderForm().validate_order_id(
            "??", self.dispatcher, DummyTracker(), {}
        )
        self.assertEqual(result, {"order_id": None})
        self.dispatcher.utter_message.assert_called_once_with(
            response="utter_invalid_order_id"
        )

    def test_known_order_returns_status_and_delivery_date(self):
        action = ActionTrackOrder(repository=self.repository)
        action.run(self.dispatcher, DummyTracker("ORD-10482"), {})
        self.repository.get_order.assert_called_once_with("ORD-10482")
        self.dispatcher.utter_message.assert_called_once_with(
            text="Order ORD-10482 is shipped. Estimated delivery: 2026-10-16."
        )

    def test_unknown_order_uses_not_found_response(self):
        ActionTrackOrder(repository=self.repository).run(
            self.dispatcher, DummyTracker("ORD-55555"), {}
        )
        self.dispatcher.utter_message.assert_called_once_with(
            response="utter_order_not_found"
        )

    def test_database_error_is_handled_without_exposing_details(self):
        broken_repository = OrderRepository(
            Path(self.temp_directory.name) / "missing.sqlite3"
        )
        ActionTrackOrder(repository=broken_repository).run(
            self.dispatcher, DummyTracker("ORD-10482"), {}
        )
        self.dispatcher.utter_message.assert_called_once_with(
            response="utter_order_database_error"
        )

    def test_missing_or_unexpected_slot_does_not_query_database(self):
        action = ActionTrackOrder(repository=self.repository)
        for value in (None, 123, ""):
            with self.subTest(value=value):
                self.dispatcher.reset_mock()
                action.run(self.dispatcher, DummyTracker(value), {})
                self.dispatcher.utter_message.assert_called_once_with(
                    response="utter_missing_order_id"
                )
        self.repository.get_order.assert_not_called()


if __name__ == "__main__":
    unittest.main()
