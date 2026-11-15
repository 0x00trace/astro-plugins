# Ledger API

Every response is JSON. Errors come back as `{"error": "<code>"}` with a 4xx or 5xx status.

| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| GET | `/health` | | `{"ok": true}` |
| POST | `/accounts` | `{"name": string}` | `{"id": number}` |
| POST | `/accounts/:id/entries` | `{"amountCents": int, "bookedOn": "YYYY-MM-DD"}` | `{"ok": true}` |
