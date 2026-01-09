from __future__ import annotations

from pathlib import Path

from duckstring import Catchment, Species, Basin


REPO_ROOT = Path.cwd().resolve()
BASIN_DIR = Path(__file__).resolve().parent
CATCHMENT_JSON = REPO_ROOT / "catchment.json"
BASIN_JSON = BASIN_DIR / "basin.json"


def main() -> None:
    # Load catchment
    catchment = Catchment.load(CATCHMENT_JSON)

    # Create basin
    ## - This creates the Basin with all its defaults, described below
    ## - Catchment is not required for initial spec, but the Basin can't be hydrated until it is
    ## - Catchment is referenced in the spec by an ID, filepath indicated in a lock file

    ## Option 1: Derived from Catchment
    basin = catchment.basin(name=BASIN_DIR.name)

    ## Option 2: Created from scratch
    # basin = Basin(name=BASIN_DIR.name)
    # basin.set_catchment(catchment)

    # Set details
    ## Outlets
    ## - This validates that the outlets exist in the attached catchment
    ## - Defaults to empty dict (no outlets) if not set
    basin.set_outlets({"aggregated": "0.3.0"})

    ## Ducks
    ### Instances
    ## - This validates that the duck instances reference valid species (if a Catchment is attached, otherwise throws an error)
    ## - Defaults to a single duck instance named "default" of the catchment's default species if not set, or {} if no Catchment is attached
    basin.set_ducks({
        "shared": {
            "species": "local",
            # future: instance-level overrides (threads, memory, etc)
            # "options": {}
        }
    })

    ### Default Duck
    ## - Defaults to an instance named "default" if not set, None if that instance does not exist
    basin.set_default_duck("shared")

    ### Pond Ducks
    ## - Defaults to {} if not set
    basin.set_pond_ducks({})

    ## Mode
    ## - Defaults to "pulse" if not set
    basin.set_mode("pulse")

    # Save basin spec
    ## Option 1: Before hydration
    basin.save(BASIN_JSON)
    print(f"Wrote dehydrated {BASIN_JSON}")

    ## Option 2: After hydration
    # basin.hydrate()
    # basin.save(BASIN_JSON)
    # print(f"Wrote hydrated {BASIN_JSON}")


if __name__ == "__main__":
    main()
