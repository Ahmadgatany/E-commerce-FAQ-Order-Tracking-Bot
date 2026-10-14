"""Rasa form validation and order tracking dialogue actions."""

import logging
import re
import sqlite3
from typing import Any, Dict, List, Optional, Text

from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher

from order_repository import OrderRepository


logger = logging.getLogger(__name__)
ORDER_ID_PATTERN = re.compile(r"^#?[A-Za-z0-9](?:[A-Za-z0-9-]{3,18}[A-Za-z0-9])$")


class ValidateTrackOrderForm(FormValidationAction):
    """Accept plausible order references and ask again for invalid input."""

    def name(self) -> Text:
        return "validate_track_order_form"

    def validate_order_id(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        order_id = str(slot_value or "").strip()
        if ORDER_ID_PATTERN.fullmatch(order_id):
            return {"order_id": order_id.upper()}

        dispatcher.utter_message(response="utter_invalid_order_id")
        return {"order_id": None}


class ActionTrackOrder(Action):
    """Look up order data through the SQLite repository."""

    def __init__(self, repository: Optional[OrderRepository] = None):
        self.repository = repository or OrderRepository()

    def name(self) -> Text:
        return "action_track_order"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        raw_order_id = tracker.get_slot("order_id")
        if not isinstance(raw_order_id, str) or not raw_order_id.strip():
            dispatcher.utter_message(response="utter_missing_order_id")
            return [SlotSet("order_id", None)]

        order_id = raw_order_id.strip().upper()
        if not ORDER_ID_PATTERN.fullmatch(order_id):
            dispatcher.utter_message(response="utter_invalid_order_id")
            return [SlotSet("order_id", None)]

        try:
            order = self.repository.get_order(order_id)
        except sqlite3.Error:
            logger.exception("Order database lookup failed")
            dispatcher.utter_message(response="utter_order_database_error")
        except Exception:
            logger.exception("Unexpected error while looking up an order")
            dispatcher.utter_message(response="utter_order_lookup_error")
        else:
            if order is None:
                dispatcher.utter_message(response="utter_order_not_found")
            else:
                dispatcher.utter_message(
                    text=(
                        f"Order {order.order_id} is {order.status}. "
                        f"Estimated delivery: {order.estimated_delivery_date}."
                    )
                )

        return [SlotSet("order_id", None)]
