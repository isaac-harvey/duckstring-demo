from __future__ import annotations

from pathlib import Path

from duckstring import Basin


BASIN_DIR = Path(__file__).resolve().parent
BASIN_JSON = BASIN_DIR / "basin.json"


def main() -> None:
    # Load basin
    ## - This validates against the Catchment if one is attached, stating errors like species mismatches, missing outlets, etc.
    basin = Basin.load(BASIN_JSON)

    # Hydrate
    ## - Copy the outlet ponds (with version) to a .duckstring/ponds/ directory (or whichever root_dir is set), if not already present
    ## - Continue doing the same for any dependencies of those ponds, backwards up the DAG
    ## - Build the necessary details for the hydrated section of the basin spec
    basin.hydrate()

    # Save basin spec
    basin.save(BASIN_JSON)
    print(f"Wrote hydrated {BASIN_JSON}")


if __name__ == "__main__":
    main()
