import csv
import importlib.util
import sqlite3

from load_seed import DB_PATH, ROOT, SEED_DIR, load


def _dump(db):
    with sqlite3.connect(db) as conn:
        return {t: conn.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall() for t in ("tickets", "customers")}


def _csv_rows(name):
    with open(SEED_DIR / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_columns_match_csvs(tmp_path):
    db = tmp_path / "app.db"
    load(db)
    with sqlite3.connect(db) as conn:
        for table, name in (("tickets", "tickets.csv"), ("customers", "customers.csv")):
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
            assert cols == list(_csv_rows(name)[0])


def test_row_counts_and_values(tmp_path):
    db = tmp_path / "app.db"
    counts = load(db)
    assert counts == {"customers": len(_csv_rows("customers.csv")), "tickets": len(_csv_rows("tickets.csv"))}
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT customer_id, plan, open_tickets FROM customers WHERE name='Northwind'").fetchone() == ("C-77", "Enterprise", 2)


def test_idempotent(tmp_path):
    db = tmp_path / "app.db"
    load(db)
    first = _dump(db)
    load(db)
    assert _dump(db) == first


def test_mcp_queries_work(tmp_path):
    db = tmp_path / "app.db"
    load(db)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT ticket_id, customer_id, created_at, text FROM tickets WHERE ticket_id='T-1042'").fetchone()
        assert conn.execute("SELECT customer_id, name, plan, open_tickets FROM customers WHERE customer_id='C-77'").fetchone()


def test_seed_files_untouched(tmp_path):
    before = {p.name: p.read_bytes() for p in SEED_DIR.glob("*.csv")}
    load(tmp_path / "app.db")
    assert {p.name: p.read_bytes() for p in SEED_DIR.glob("*.csv")} == before


def test_default_db_path_matches_triage_server():
    """load_seed and mcp/triage_server must agree on where app.db lives, or the
    loader can silently populate a file the triage agent never reads."""
    spec = importlib.util.spec_from_file_location("triage_server", ROOT / "mcp" / "triage_server.py")
    triage_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(triage_server)
    assert DB_PATH == triage_server.DB_PATH
