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
    resolved = dict(basin_spec.get("resolved") or {})
    pond_paths = dict(resolved.get("pond_paths") or {})

    if not pond_paths:
        raise RuntimeError("Basin is not hydrated. Run basins/main/hydrate.py first.")

    c = Catchment.load(CATCHMENT_JSON)

    c.ponds = {
        name: str((BASIN_DIR / Path(path)).resolve()) if not Path(path).is_absolute() else path
        for name, path in pond_paths.items()
    }

    outlets = dict(basin_spec["outlets"])
    mode = str(basin_spec.get("mode", "pulse"))
    basin_name = str(basin_spec.get("name", BASIN_DIR.name))

    b = c.basin(outlets=outlets, mode=mode, name=basin_name)

    _ = b.pulse()

    print("Pulse complete.")
    print(f"- DuckDB: {Path(c.root_dir) / 'state' / 'duckstring.duckdb'}")
    print(f"- Data:   {Path(c.root_dir) / 'data'}")
    print(f"- Demo pulse log SQLite: {Path(c.root_dir) / 'state' / 'demo_pulses.sqlite'}")


if __name__ == "__main__":
    main()
