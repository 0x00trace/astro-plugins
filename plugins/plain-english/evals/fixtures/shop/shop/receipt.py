"""Write a plain-text receipt for a cart."""

import os
import tempfile

from shop.cart import cart_total, line_total


def receipt_lines(lines, code=None):
    out = [f"{qty} x {price} = {line_total(price, qty)}" for price, qty in lines]
    if code:
        out.append(f"code {code}")
    out.append(f"total {cart_total(lines, code)}")
    return out


def write_receipt(lines, code=None, folder=None):
    """Write the receipt to receipt.txt in folder, or in the temp folder, and return its path."""
    path = os.path.join(folder or tempfile.gettempdir(), "receipt.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(receipt_lines(lines, code)) + "\n")
    return path
