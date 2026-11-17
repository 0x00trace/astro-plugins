# Open pull requests

## #33 fix: apply the bulk discount at 10 items (T-13)

- Author: sam
- Review: approved by lee on 2026-11-15
- CI: `lint` passed, `test-linux` passed, `test-macos` failed (log in `ci-33-test-macos.log`)
- Changes: `shop/cart.py` changes `qty > BULK_QTY` to `qty >= BULK_QTY`. `tests/test_cart.py` adds a check that `write_receipt` returns the path it wrote to.

## #34 docs: release notes for 1.4 (T-15)

- Author: lee
- Draft. It lists T-12 and T-13, and says nothing about Windows yet.
- CI: `lint` passed
