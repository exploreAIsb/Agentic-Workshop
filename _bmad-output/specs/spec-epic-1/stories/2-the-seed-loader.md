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

### Review Findings

- [x] [Review][Patch] Transaction isn't actually atomic — DDL (DROP/CREATE) auto-commits outside the implicit transaction, so a mid-load failure leaves a table dropped-and-empty instead of rolled back [load_seed.py:26-37]
- [x] [Review][Patch] `sqlite3.connect()` result never closed, leaking a connection handle each call [load_seed.py:26]
- [x] [Review][Patch] No test ties `load_seed.DB_PATH` to `mcp/triage_server.DB_PATH`; the two could silently drift apart [load_seed.py:9]

**Rejected**
- No validation on `open_tickets` numeric type / malformed rows / missing files — low, seed CSVs are read-only/controlled, fix adds guard complexity for an unreachable path.
- No FK constraint between `tickets.customer_id` and `customers.customer_id` — out of scope for this story.
- No test of the `__main__` CLI block — low, trivial print statement.
- `app.db` missing from `.gitignore` — false: `.gitignore` already lists `app.db`.
- Hardcoded canary IDs (`T-1042`, `C-77`) undocumented in tests — cosmetic.
- Spec marked `done` without noting known limitations — rejected (fix would mean editing the spec under review).
