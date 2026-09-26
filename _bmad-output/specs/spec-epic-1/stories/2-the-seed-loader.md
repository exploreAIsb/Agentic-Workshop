---
title: 'The seed loader'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** There is no `app.db`, so `mcp/triage_server.py` has nothing to query and the agent has no ticket data (CAP-2).

**Approach:** Add `load_seed.py`: `uv run python load_seed.py` reads `seed/tickets.csv` and `seed/customers.csv` and rewrites tables `tickets` and `customers` in `app.db` with the CSVs' columns, inside one transaction, so repeat runs leave identical state. Seed files are only read.

</frozen-after-approval>

## Implementation Notes

- Idempotency: drop and recreate both tables in one transaction, then insert; primary keys on `ticket_id` / `customer_id`.
- Types: `open_tickets` is INTEGER, every other column TEXT. Column names match the CSVs and the queries in `mcp/triage_server.py`.
- Files: `load_seed.py`, `tests/test_load_seed.py`.
