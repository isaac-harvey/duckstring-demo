from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import ibis

from duckstring import Pond


POND_VERSION = "0.1.0"


def pond(resolver=None) -> Pond:
    """
    Demo pond: base

    Each execution appends a new timestamp to a persistent log (SQLite),
    then materializes the full history as the exported table `pulse(ts)`.
    """
    p = Pond(
        name="base",
        description="Pulse logger: persists a timestamp per execution.",
        version=POND_VERSION,
    )
    if resolver is not None:
        p.attach_resolver(resolver)

    # Persist pulse timestamps outside DuckDB so we can rebuild the full history
    # deterministically on each run (duckstring v1 is "replace" materialization).
    root_dir = Path(getattr(getattr(resolver, "catchment", None), "root_dir", "catchment"))
    db_path = root_dir / "state" / "demo_pulses.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    ts = float(time.time())

    con = sqlite3.connect(str(db_path))
    try:
        con.execute("CREATE TABLE IF NOT EXISTS pulse (ts REAL NOT NULL)")
        con.execute("INSERT INTO pulse(ts) VALUES (?)", (ts,))
        rows = [r[0] for r in con.execute("SELECT ts FROM pulse ORDER BY ts").fetchall()]
        con.commit()
    finally:
        con.close()

    schema = ibis.schema({"ts": "timestamp"})
    data = [{"ts": datetime.fromtimestamp(x, tz=timezone.utc)} for x in rows]
    t = ibis.memtable(data, schema=schema)

    p.sink({"pulse": t})
    p.flow([None])
    return p
