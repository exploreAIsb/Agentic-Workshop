---
id: SPEC-epic-1
companions: [../../../mcp/triage_server.py]
sources: [../../../INTENT.md]
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Epic 1: triage data and schema

## Why

This is the workshop's first lab and the foundation everything else is built on: before there is an agent to run or an eval to score, there has to be a stable, testable shape for what a triage decision *is*, and a live database seeded with the sample tickets and customers to triage. Without this epic, Epic 2's agent has no schema to return decisions in and no data for its MCP tools to query, and Epic 3's eval has nothing to score against.

## Capabilities

- **CAP-1**
  - **intent:** A triage decision can be represented and validated as a single JSON object with a category, a priority, a route and a rationale.
  - **success:** An object with category in `billing`, `bug`, `access`, `performance` or `how-to`; priority in `P1`–`P4`; route in `billing-team`, `bug-team`, `access-team`, `performance-team` or `how-to-team`; and a one-sentence rationale validates successfully. Anything else — a missing field, an out-of-range value, extra structure — is rejected with a clear error.

- **CAP-2**
  - **intent:** A person can load the seed data into a local SQLite database with one command.
  - **success:** `uv run python load_seed.py` reads `seed/tickets.csv` and `seed/customers.csv` and writes them into `app.db` as tables `tickets` and `customers` with the same columns as the CSVs. Running the command twice leaves `app.db` in the same state — no duplicate or drifting rows.

## Constraints

- `seed/tickets.csv` and `seed/customers.csv` are read-only; the loader reads them and never writes to them.
- No network calls and no API keys in this epic — schema validation and the loader are local-only.
- `mcp/triage_server.py` already queries `app.db` (`tickets` by `ticket_id, customer_id, created_at, text`; `customers` by `customer_id, name, plan, open_tickets`) and is read-only. `load_seed.py`'s table and column names must keep those queries working.

## Non-goals

- The agent, the MCP tools, evals and any user interface (Epic 2 and Epic 3).

## Success signal

`uv run python load_seed.py` populates `app.db` with `tickets` and `customers` tables matching the CSVs' columns, idempotently on repeat runs. A triage decision with a valid category, priority, route and rationale validates against the Epic 1 schema; a malformed one is rejected with a clear error.

## Assumptions

- The schema validates category, priority and route as independent enums, per INTENT.md's literal field lists. It does not enforce that route corresponds to category under `TRIAGE_POLICY.md`'s mapping (e.g. `billing` → `billing-team`) — that pairing is policy logic the Epic 2 agent applies, not a schema-level constraint.
