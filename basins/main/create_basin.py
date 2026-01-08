from __future__ import annotations

import json
from pathlib import Path

BASIN_DIR = Path(__file__).resolve().parent
BASIN_JSON = BASIN_DIR / "basin.json"


def main() -> None:
    spec = {
        "spec_version": 1,
        "name": BASIN_DIR.name,
        "mode": "pulse",
        # Only terminal ponds
        "outlets": {"derived": "0.1.0"},
        # Duck instance selection is a Basin concern
        "ducks": {
            "instances": {
                "shared": {
                    "species": "local",
                    # future: instance-level overrides (threads, memory, etc)
                    # "options": {}
                }
            },
            "default": "shared",
            # optional per-pond overrides: {"base": "shared", "derived": "shared"}
            "ponds": {},
        },
        # Populated by hydrate.py
        "hydrated": {},
    }

    BASIN_JSON.write_text(json.dumps(spec, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {BASIN_JSON}")


if __name__ == "__main__":
    main()
