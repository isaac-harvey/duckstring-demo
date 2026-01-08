from __future__ import annotations

from pathlib import Path

from duckstring import Catchment, Species


REPO_ROOT = Path(__file__).resolve().parent
CATCHMENT_JSON = REPO_ROOT / "catchment.json"
PONDS_JSON = REPO_ROOT / "ponds.json"


def main() -> None:
    c = Catchment(root_dir="catchment")

    # Load pond catalog (local paths in this demo; could be git URLs in future)
    c.load_ponds(PONDS_JSON)

    # Register compute species (v1: local duckdb only)
    c.set_species(
        {
            "local": Species(kind="local", engine="duckdb"),
        },
        overwrite=False,
    )
    c.set_default_species("local")

    c.save(CATCHMENT_JSON)
    print(f"Wrote {CATCHMENT_JSON}")


if __name__ == "__main__":
    main()
