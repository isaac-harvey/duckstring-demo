from __future__ import annotations

from pathlib import Path

from duckstring import Catchment, Species


REPO_ROOT = Path(__file__).resolve().parent
CATCHMENT_JSON = REPO_ROOT / "catchment.json"
PONDS_JSON = REPO_ROOT / "ponds.json"


def main() -> None:
    catchment = Catchment(root_dir=".duckstring")

    # Ponds
    ## Option 1: From local file
    catchment.load_ponds(PONDS_JSON)

    ## Option 2: From scratch, optionally overwriting existing ponds
    # catchment.set_ponds(
    #     reference_type="local", # Can also be git, S3 etc.
    #     version_by={
    #         "type": "directory", # This is also the default
    #         "template": "{pond}/{version}", # This indicates that within the folder for each pond, versions are subfolders named by version, and is the default
    #     },
    #     ponds={
    #         "ingest@0.1.0": str(REPO_ROOT / "ponds" / "ingest" / "0.1.0"),
    #         "enriched@0.1.0": str(REPO_ROOT / "ponds" / "enriched" / "0.1.0"),
    #         "aggregated@0.1.0": str(REPO_ROOT / "ponds" / "aggregated" / "0.1.0"),
    #     },
    #     overwrite=False
    # )

    # ### Example git-based ponds
    # catchment.set_ponds(
    #     reference_type="git",
    #     version_by={
    #         "type": "branch", # Can be tag too
    #         "template": "release/{version}", # This indicates to use the version from the branch name
    #     },
    #     ponds={
    #         "ingest": "https://path/to/repo/ingest.git",
    #         "enriched@0.1.0": "https://path/to/repo/enriched.git@release/0.1.0", # Version in pond name, so will use that directly - must be able to resolve to a branch/commit or it will error
    #     },
    #     overwrite=False
    # )

    # Duck Species
    catchment.set_species(
        {
            "local": Species(kind="local", engine="duckdb"),
        },
        overwrite=False,
    )
    catchment.set_default_species("local")

    # Save catchment spec
    catchment.save(CATCHMENT_JSON)
    print(f"Wrote {CATCHMENT_JSON}")


if __name__ == "__main__":
    main()
