"""SQLite repository tests using isolated temporary database files."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from order_repository import OrderRepository
from scripts.init_db import initialize_database


class OrderRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "orders.sqlite3"
        initialize_database(self.database_path)
        self.repository = OrderRepository(self.database_path)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_returns_order_status_and_delivery_date(self):
        order = self.repository.get_order(" ord-10482 ")
        self.assertEqual(order.order_id, "ORD-10482")
        self.assertEqual(order.status, "shipped")
        self.assertEqual(order.estimated_delivery_date, "2026-10-16")

    def test_unknown_order_returns_none(self):
        self.assertIsNone(self.repository.get_order("ORD-55555"))

    def test_unexpected_or_missing_input_returns_none(self):
        for value in (None, 123, "", "  ", "x" * 33):
            with self.subTest(value=value):
                self.assertIsNone(self.repository.get_order(value))

    def test_missing_database_raises_sqlite_error(self):
        repository = OrderRepository(Path(self.temp_directory.name) / "missing.sqlite3")
        with self.assertRaises(sqlite3.OperationalError):
            repository.get_order("ORD-10482")

    def test_database_without_orders_table_raises_sqlite_error(self):
        invalid_path = Path(self.temp_directory.name) / "wrong-schema.sqlite3"
        connection = sqlite3.connect(invalid_path)
        try:
            connection.execute("CREATE TABLE something_else (value TEXT)")
        finally:
            connection.close()
        with self.assertRaises(sqlite3.OperationalError):
            OrderRepository(invalid_path).get_order("ORD-10482")


if __name__ == "__main__":
    unittest.main()
