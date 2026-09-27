"""Load seed/tickets.csv and seed/customers.csv into app.db (Epic 1, CAP-2)."""

import contextlib
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED_DIR = ROOT / "seed"
DB_PATH = ROOT / "app.db"

TABLES = {
    "customers": (
        "customer_id TEXT PRIMARY KEY, name TEXT, plan TEXT, open_tickets INTEGER",
        "customers.csv",
    ),
    "tickets": (
        "ticket_id TEXT PRIMARY KEY, customer_id TEXT, created_at TEXT, text TEXT",
        "tickets.csv",
    ),
}


def load(db_path: Path = DB_PATH, seed_dir: Path = SEED_DIR) -> dict[str, int]:
    """Rebuild both tables from the CSVs in one transaction; return row counts."""
    counts = {}
    # isolation_level=None (autocommit) plus an explicit BEGIN puts the DROP/CREATE
    # DDL in the same transaction as the inserts -- under the default legacy mode,
    # sqlite3 auto-commits DDL immediately, so a failure partway through would
    # otherwise leave a table dropped instead of rolled back to its prior state.
    with contextlib.closing(sqlite3.connect(db_path, isolation_level=None)) as conn:
        conn.execute("BEGIN")
        try:
            for table, (columns, filename) in TABLES.items():
                with open(seed_dir / filename, newline="", encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
                names = [c.split()[0] for c in columns.split(", ")]
                conn.execute(f"DROP TABLE IF EXISTS {table}")
                conn.execute(f"CREATE TABLE {table} ({columns})")
                conn.executemany(
                    f"INSERT INTO {table} ({', '.join(names)}) VALUES ({', '.join('?' * len(names))})",
                    [[row[n] for n in names] for row in rows],
                )
                counts[table] = len(rows)
        except BaseException:
            conn.rollback()
            raise
        else:
            conn.commit()
    return counts


if __name__ == "__main__":
    for table, n in load().items():
        print(f"{table}: {n} rows")
