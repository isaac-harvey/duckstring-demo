# inspect.py
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb


def _infer_root_dir(repo_root: Path) -> Path:
    """
    Prefer catchment.json's root_dir if present; otherwise default to ./catchment
    """
    spec = repo_root / "catchment.json"
    if spec.exists():
        try:
            data = json.loads(spec.read_text(encoding="utf-8"))
            root = data.get("root_dir") or "catchment"
            return (repo_root / root).resolve()
        except Exception:
            pass
    return (repo_root / "catchment").resolve()


def _parse_ident(s: str) -> tuple[str, str]:
    if "." not in s:
        raise ValueError("Expected identifier of the form {pond}.{table}, e.g. base.pulse")
    pond, table = s.split(".", 1)
    pond = pond.strip()
    table = table.strip()
    if not pond or not table:
        raise ValueError("Invalid identifier. Expected {pond}.{table}.")
    return pond, table


def main() -> None:
    ap = argparse.ArgumentParser(description="Inspect a catchment parquet table: {pond}.{table}")
    ap.add_argument("table", help="Table identifier like base.pulse")
    ap.add_argument("--limit", type=int, default=20, help="Number of rows to show (default: 20)")
    ap.add_argument("--no-head", action="store_true", help="Do not print row preview")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent
    root_dir = _infer_root_dir(repo_root)

    try:
        pond, table = _parse_ident(args.table)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    parquet_path = root_dir / "data" / pond / f"{table}.parquet"
    if not parquet_path.exists():
        print(f"Not found: {parquet_path}", file=sys.stderr)

        # Helpful: show available tables under catchment/data/{pond}/
        pond_dir = root_dir / "data" / pond
        if pond_dir.exists():
            available = sorted(p.stem for p in pond_dir.glob("*.parquet"))
            if available:
                print(f"Available in {pond}/: " + ", ".join(available), file=sys.stderr)
        else:
            data_dir = root_dir / "data"
            if data_dir.exists():
                ponds = sorted(p.name for p in data_dir.iterdir() if p.is_dir())
                if ponds:
                    print("Available ponds: " + ", ".join(ponds), file=sys.stderr)
        sys.exit(1)

    con = duckdb.connect(database=":memory:")
    try:
        rel = con.read_parquet(str(parquet_path))

        # Row count
        n = con.execute("SELECT COUNT(*) FROM rel").fetchone()[0]

        # Schema
        schema_rows = con.execute("DESCRIBE rel").fetchall()  # (column_name, column_type, null, key, default, extra)
        print(f"Catchment root: {root_dir}")
        print(f"Table: {pond}.{table}")
        print(f"Parquet: {parquet_path}")
        print(f"Rows: {n}")
        print("Schema:")
        for col, typ, *_ in schema_rows:
            print(f"  - {col}: {typ}")

        if not args.no_head:
            lim = max(0, int(args.limit))
            if lim == 0:
                return
            df = con.execute(f"SELECT * FROM rel LIMIT {lim}").df()
            print(f"\nPreview (first {min(lim, n)} rows):")
            # pandas pretty print
            print(df.to_string(index=False))

    finally:
        con.close()


if __name__ == "__main__":
    main()
