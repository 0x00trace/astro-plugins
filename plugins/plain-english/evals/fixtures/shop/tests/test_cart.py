import tempfile
import unittest
from decimal import Decimal

from shop.cart import cart_total, line_total, take_percent
from shop.receipt import receipt_lines, write_receipt


class CartTest(unittest.TestCase):
    def test_line_total(self):
        self.assertEqual(line_total("2.50", 3), Decimal("7.50"))

    def test_nine_items_pay_full_price(self):
        self.assertEqual(line_total("1.00", 9), Decimal("9.00"))

    def test_ten_items_get_bulk_discount(self):
        self.assertEqual(line_total("1.00", 10), Decimal("9.50"))

    def test_take_percent_rounds_half_up(self):
        self.assertEqual(take_percent(Decimal("0.25"), 50), Decimal("0.13"))

    def test_code(self):
        self.assertEqual(cart_total([("10.00", 1)], "WELCOME10"), Decimal("9.00"))

    def test_unknown_code(self):
        with self.assertRaises(ValueError):
            cart_total([("10.00", 1)], "NOPE")


class ReceiptTest(unittest.TestCase):
    def test_receipt_lines(self):
        self.assertEqual(
            receipt_lines([("2.50", 2)], "STAFF20"),
            ["2 x 2.50 = 5.00", "code STAFF20", "total 4.00"],
        )

    def test_write_receipt(self):
        with tempfile.TemporaryDirectory(dir=".") as folder:
            path = write_receipt([("1.00", 1)], folder=folder)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read(), "1 x 1.00 = 1.00\ntotal 1.00\n")
