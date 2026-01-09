from __future__ import annotations

from pathlib import Path

from duckstring import Basin


BASIN_DIR = Path(__file__).resolve().parent
BASIN_JSON = BASIN_DIR / "basin.json"


def main() -> None:
    # Load basin
    ## - This validates against the Catchment if one is attached, stating errors like species mismatches, missing outlets, etc.
    basin = Basin.load(BASIN_JSON)

    # Pulse
    ## - First validates hydration state, match to catchment etc.
    ## - This can include progress messages if verbose=True
    ## - A pulse returns a PulseResult with details on duration, success, etc.
    pulse = basin.pulse(verbose=True)
    print(f"Completed pulse {pulse} in {pulse.duration} seconds")


if __name__ == "__main__":
    main()
