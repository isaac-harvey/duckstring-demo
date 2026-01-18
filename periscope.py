from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import duckdb


_VERSION_DIR_RE = re.compile(r"^(?P<pond>[A-Za-z0-9_\-]+)@(?P<maj>\d+)\.(?P<min>\d+)\.(?P<pat>\d+)$")
_SEMVER_DIR_RE = re.compile(r"^(?P<maj>\d+)\.(?P<min>\d+)\.(?P<pat>\d+)$")


@dataclass(frozen=True, order=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse_prefix(cls, s: str) -> tuple[str, tuple[int, ...] | None]:
        """
        Accept:
          - "base" -> ("base", None)
          - "base@0" -> ("base", (0,))
          - "base@0.1" -> ("base", (0,1))
          - "base@0.1.0" -> ("base", (0,1,0))
        """
        s = s.strip()
        if not s:
            raise ValueError("Pond must be non-empty.")

        if "@" not in s:
            return s, None

        pond, ver = s.split("@", 1)
        pond = pond.strip()
        ver = ver.strip()

        if not pond or not ver:
            raise ValueError("Invalid pond ref. Use pond or pond@version (e.g. base@0.1.0).")

        parts = ver.split(".")
        if len(parts) > 3:
            raise ValueError("Version prefix must be major, major.minor, or major.minor.patch (e.g. 0, 0.1, 0.1.0).")

        prefix: list[int] = []
        for p in parts:
            if not p.isdigit():
                raise ValueError("Version prefix must be numeric (e.g. 0, 0.1, 0.1.0).")
            prefix.append(int(p))

        return pond, tuple(prefix)


def _infer_root_dir(repo_root: Path) -> Path:
    """
    Prefer catchment.json's root_dir if present; otherwise default to .duckstring
    """
    spec = repo_root / "catchment.json"
    if spec.exists():
        try:
            data = json.loads(spec.read_text(encoding="utf-8"))
            root = data.get("root_dir") or ".duckstring"
            return (repo_root / root).resolve()
        except Exception:
            pass
    return (repo_root / ".duckstring").resolve()


def _list_version_dirs(data_dir: Path, pond: str) -> list[tuple[SemVer, Path]]:
    out: list[tuple[SemVer, Path]] = []
    if not data_dir.exists():
        return out

    versions: dict[SemVer, Path] = {}

    pond_dir = data_dir / pond
    if pond_dir.exists():
        for p in pond_dir.iterdir():
            if not p.is_dir():
                continue
            m = _SEMVER_DIR_RE.match(p.name)
            if not m:
                continue
            v = SemVer(int(m.group("maj")), int(m.group("min")), int(m.group("pat")))
            versions[v] = p

    for p in data_dir.iterdir():
        if not p.is_dir():
            continue
        m = _VERSION_DIR_RE.match(p.name)
        if not m or m.group("pond") != pond:
            continue
        v = SemVer(int(m.group("maj")), int(m.group("min")), int(m.group("pat")))
        versions.setdefault(v, p)

    out = [(v, d) for v, d in versions.items()]
    out.sort(key=lambda t: t[0])
    return out


def _match_prefix(ver: SemVer, prefix: tuple[int, ...]) -> bool:
    if len(prefix) == 1:
        return ver.major == prefix[0]
    if len(prefix) == 2:
        return ver.major == prefix[0] and ver.minor == prefix[1]
    if len(prefix) == 3:
        return ver.major == prefix[0] and ver.minor == prefix[1] and ver.patch == prefix[2]
    return False


def _resolve_pond_dir(root_dir: Path, pond: str, prefix: tuple[int, ...] | None) -> tuple[Path, str]:
    """
    Returns (pond_dir, display_label_version)

    Resolution rules:
      - pond@X.Y.Z: exact directory must exist
      - pond@X.Y: choose max patch among matching
      - pond@X: choose max minor/patch among matching
      - pond: choose max major/minor/patch overall
    """
    data_dir = root_dir / "data"
    versions = _list_version_dirs(data_dir, pond)

    if prefix is None:
        if versions:
            v, d = versions[-1]
            return d, f"{v.major}.{v.minor}.{v.patch}"
        # fallback for legacy/unversioned layout
        return (data_dir / pond), "<unversioned>"

    # exact: require it exists
    if len(prefix) == 3:
        want = SemVer(prefix[0], prefix[1], prefix[2])
        want_dir = data_dir / pond / f"{want.major}.{want.minor}.{want.patch}"
        if want_dir.exists():
            return want_dir, f"{want.major}.{want.minor}.{want.patch}"
        legacy_dir = data_dir / f"{pond}@{want.major}.{want.minor}.{want.patch}"
        if legacy_dir.exists():
            return legacy_dir, f"{want.major}.{want.minor}.{want.patch}"
        raise FileNotFoundError(f"Missing directory: {want_dir}")

    # prefix: choose max match
    candidates = [(v, d) for (v, d) in versions if _match_prefix(v, prefix)]
    if candidates:
        v, d = candidates[-1]
        return d, f"{v.major}.{v.minor}.{v.patch}"

    # no candidates: report available
    avail = ", ".join(f"{v.major}.{v.minor}.{v.patch}" for (v, _) in versions) or "<none>"
    raise FileNotFoundError(f"No versions found for {pond}@{'.'.join(map(str, prefix))}. Available: {avail}")


def _sql_str(value: str) -> str:
    return value.replace("'", "''")


def _list_tables_with_stats(pond_dir: Path) -> None:
    parquet_files = sorted(pond_dir.glob("*.parquet"))
    if not parquet_files:
        print("No tables found.")
        return

    con = duckdb.connect(database=":memory:")
    try:
        rows: list[tuple[str, int, int, int]] = []
        for p in parquet_files:
            sql_path = _sql_str(str(p))
            n_rows = con.execute(
                f"SELECT COUNT(*) FROM read_parquet('{sql_path}')"
            ).fetchone()[0]
            schema_rows = con.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{sql_path}')"
            ).fetchall()
            n_cols = len(schema_rows)
            rows.append((p.stem, n_rows, n_cols, p.stat().st_size))

        name_w = max(len(r[0]) for r in rows)
        print("Tables:")
        for name, n_rows, n_cols, size_bytes in rows:
            size_mb = size_bytes / (1024 * 1024)
            print(
                f"  - {name:<{name_w}}  rows={n_rows:<10} cols={n_cols:<4} size={size_mb:6.2f} MB"
            )
    finally:
        con.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Inspect a catchment parquet table: pond[@verprefix] [table]"
    )
    ap.add_argument("pond", help="Pond ref: base, base@0, base@0.1, or base@0.1.0")
    ap.add_argument("table", nargs="?", help="Table name (omit to list available tables)")
    ap.add_argument("--limit", type=int, default=20, help="Number of rows to show (default: 20)")
    ap.add_argument("--no-head", action="store_true", help="Do not print row preview")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent
    root_dir = _infer_root_dir(repo_root)

    try:
        pond, prefix = SemVer.parse_prefix(args.pond)
        table = args.table.strip() if args.table else None
        if table is not None and not table:
            raise ValueError("Table must be non-empty.")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        pond_dir, resolved_version = _resolve_pond_dir(root_dir, pond, prefix)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if table is None:
        label = f"{pond}@{resolved_version}" if resolved_version != "<unversioned>" else pond
        print(f"Catchment root: {root_dir}")
        print(f"Pond: {label}")
        print(f"Data dir: {pond_dir}")
        _list_tables_with_stats(pond_dir)
        return

    parquet_path = pond_dir / f"{table}.parquet"
    if not parquet_path.exists():
        print(f"Not found: {parquet_path}", file=sys.stderr)
        if pond_dir.exists():
            available = sorted(p.stem for p in pond_dir.glob("*.parquet"))
            if available:
                print("Available tables:", file=sys.stderr)
                for t in available:
                    print(f"  - {t}", file=sys.stderr)
        sys.exit(1)

    con = duckdb.connect(database=":memory:")
    try:
        rel = con.read_parquet(str(parquet_path))
        n = con.execute("SELECT COUNT(*) FROM rel").fetchone()[0]
        schema_rows = con.execute("DESCRIBE rel").fetchall()

        label = f"{pond}@{resolved_version}" if resolved_version != "<unversioned>" else f"{pond}.{table}"

        print(f"Catchment root: {root_dir}")
        print(f"Pond: {label}")
        print(f"Table: {table}")
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
            print(df.to_string(index=False))
    finally:
        con.close()


if __name__ == "__main__":
    main()
