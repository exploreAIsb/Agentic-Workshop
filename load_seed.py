"""Load seed/tickets.csv and seed/customers.csv into app.db (Epic 1, CAP-2)."""

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
    with sqlite3.connect(db_path) as conn:
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
    return counts


if __name__ == "__main__":
    for table, n in load().items():
        print(f"{table}: {n} rows")
