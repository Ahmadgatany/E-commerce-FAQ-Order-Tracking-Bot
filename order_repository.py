"""SQLite access for order tracking, kept separate from Rasa actions."""

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


DEFAULT_DATABASE_PATH = Path("data") / "orders.sqlite3"
DatabasePath = Union[str, os.PathLike]


@dataclass(frozen=True)
class Order:
    order_id: str
    status: str
    estimated_delivery_date: str


class OrderRepository:
    """Read order records from the configured local SQLite database."""

    def __init__(self, database_path: Optional[DatabasePath] = None):
        configured_path = database_path or os.environ.get(
            "ORDER_DB_PATH", str(DEFAULT_DATABASE_PATH)
        )
        self.database_path = Path(configured_path).expanduser()

    def get_order(self, order_id: object) -> Optional[Order]:
        """Return an order by ID, or ``None`` for invalid/unknown IDs.

        SQLite errors are allowed to propagate so the Rasa action can respond
        safely while logs retain the diagnostic context.
        """
        if not isinstance(order_id, str):
            return None
        normalized_id = order_id.strip().upper()
        if not normalized_id or len(normalized_id) > 32:
            return None
        if not self.database_path.is_file():
            raise sqlite3.OperationalError("Order database does not exist")

        connection = sqlite3.connect(str(self.database_path), timeout=5)
        try:
            with connection:
                connection.row_factory = sqlite3.Row
                row = connection.execute(
                    """SELECT order_id, status, estimated_delivery_date
                       FROM orders WHERE order_id = ?""",
                    (normalized_id,),
                ).fetchone()
        finally:
            connection.close()

        if row is None:
            return None
        return Order(
            order_id=row["order_id"],
            status=row["status"],
            estimated_delivery_date=row["estimated_delivery_date"],
        )
