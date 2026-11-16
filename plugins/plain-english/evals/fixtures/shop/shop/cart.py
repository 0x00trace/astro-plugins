"""Cart totals for the checkout."""

from decimal import ROUND_HALF_UP, Decimal

BULK_QTY = 10
BULK_PERCENT = 5
CODES = {"WELCOME10": 10, "STAFF20": 20}


def line_total(price, qty):
    """Price times quantity, with the bulk discount once a line reaches BULK_QTY items."""
    total = Decimal(price) * qty
    if qty > BULK_QTY:
        total = take_percent(total, BULK_PERCENT)
    return total


def take_percent(amount, percent):
    """Take percent off amount, rounded half up to the cent."""
    off = amount * Decimal(percent) / 100
    return (amount - off).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def cart_total(lines, code=None):
    """Sum the lines, then apply a discount code if one is given."""
    total = sum((line_total(price, qty) for price, qty in lines), Decimal(0))
    if code is not None:
        if code not in CODES:
            raise ValueError(f"unknown discount code: {code}")
        total = take_percent(total, CODES[code])
    return total.quantize(Decimal("0.01"))
