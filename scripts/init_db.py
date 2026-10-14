"""Create the local orders database and insert fictional sample records."""

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from typing import Union

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from order_repository import DEFAULT_DATABASE_PATH


SAMPLE_ORDERS = [
    ("ORD-10482", "shipped", "2026-10-16"),
    ("A739205", "processing", "2026-10-18"),
    ("EC-44190", "delivered", "2026-10-10"),
    ("ORD-582914", "confirmed", "2026-10-20"),
    ("ORD-77821", "out for delivery", "2026-10-14"),
    ("B120045", "shipped", "2026-10-17"),
    ("ORD-901267", "delayed", "2026-10-21"),
    ("SHOP-33018", "processing", "2026-10-19"),
    ("C554812", "delivered", "2026-10-08"),
    ("ORD-660291", "confirmed", "2026-10-22"),
    ("EC-775034", "shipped", "2026-10-15"),
    ("A308617", "out for delivery", "2026-10-13"),
    ("ORD-441205", "processing", "2026-10-23"),
    ("SHOP-90274", "delayed", "2026-10-24"),
    ("D719063", "confirmed", "2026-10-25"),
]


def initialize_database(database_path: Union[str, os.PathLike]) -> Path:
    """Create the orders table and idempotently seed its fictional records."""
    path = Path(database_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    try:
        with connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS orders (
                       order_id TEXT PRIMARY KEY,
                       status TEXT NOT NULL,
                       estimated_delivery_date TEXT NOT NULL
                   )"""
            )
            connection.executemany(
                """INSERT INTO orders (order_id, status, estimated_delivery_date)
                   VALUES (?, ?, ?)
                   ON CONFLICT(order_id) DO UPDATE SET
                       status = excluded.status,
                       estimated_delivery_date = excluded.estimated_delivery_date""",
                SAMPLE_ORDERS,
            )
    finally:
        connection.close()
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        default=os.environ.get("ORDER_DB_PATH", str(DEFAULT_DATABASE_PATH)),
        help="SQLite file path (default: ORDER_DB_PATH or data/orders.sqlite3)",
    )
    args = parser.parse_args()
    path = initialize_database(args.db_path)
    print(f"Initialized {len(SAMPLE_ORDERS)} sample orders in {path}")


if __name__ == "__main__":
    main()
