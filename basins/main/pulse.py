from __future__ import annotations

import json
from pathlib import Path

from duckstring import Catchment


REPO_ROOT = Path(__file__).resolve().parents[2]
CATCHMENT_JSON = REPO_ROOT / "catchment.json"
BASIN_DIR = Path(__file__).resolve().parent
BASIN_JSON = BASIN_DIR / "basin.json"


def main() -> None:
    basin_spec = json.loads(BASIN_JSON.read_text(encoding="utf-8"))
    hydrated = dict(basin_spec.get("hydrated") or {})
    hydrated_ponds = dict(hydrated.get("ponds") or {})
    stages = list(hydrated.get("stages") or [])

    if not hydrated_ponds or not stages:
        raise RuntimeError("Basin is not hydrated. Run basins/main/hydrate.py first.")

    c = Catchment.load(CATCHMENT_JSON)

    # Use hydrated code paths for execution
    c.ponds = {pond_name: info["path"] for pond_name, info in hydrated_ponds.items()}

    outlets = dict(basin_spec["outlets"])
    mode = str(basin_spec.get("mode", "pulse"))
    basin_name = str(basin_spec.get("name", BASIN_DIR.name))

    # Future: pass duck instance bindings / stages to duckstring core so runtime does not re-resolve.
    # For now, execute using the current duckstring Basin implementation.
    b = c.basin(outlets=outlets, mode=mode, name=basin_name)
    _ = b.pulse()

    root_dir = Path(c.root_dir)
    print("Pulse complete.")
    print(f"- DuckDB: {root_dir / 'state' / 'duckstring.duckdb'}")
    print(f"- Data:   {root_dir / 'data'}")
    print(f"- Demo pulse log SQLite: {root_dir / 'state' / 'demo_pulses.sqlite'}")


if __name__ == "__main__":
    main()
