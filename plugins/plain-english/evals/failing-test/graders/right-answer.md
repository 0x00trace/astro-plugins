---
type: llm
---
PASS if the reply says the cause is the comparison in `line_total` in `shop/cart.py`: `qty > BULK_QTY` leaves out a line of exactly 10 items, so it should be `>=` (or it says the bulk discount starts at 11 items instead of 10). FAIL if it names another cause, or gives no cause.
