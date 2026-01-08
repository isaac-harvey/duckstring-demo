from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

from duckstring import PondManifest


REPO_ROOT = Path(__file__).resolve().parents[2]
BASIN_DIR = Path(__file__).resolve().parent
BASIN_JSON = BASIN_DIR / "basin.json"


def _parse_major(version: str) -> int:
    # semver-ish: "X.Y.Z"
    try:
        return int(version.split(".", 1)[0])
    except Exception as e:  # pragma: no cover
        raise ValueError(f"Invalid version string: {version!r}") from e


def _layered_stages(edges: Dict[str, Set[str]]) -> List[List[str]]:
    """
    Return stages as list[list[node]] such that all nodes in a stage can run in parallel.
    Deterministic ordering: nodes sorted within each stage.
    """
    nodes = set(edges.keys())
    indeg = {n: 0 for n in nodes}
    downstream = {n: set() for n in nodes}

    for n, ups in edges.items():
        for u in ups:
            if u not in nodes:
                continue
            indeg[n] += 1
            downstream[u].add(n)

    stages: List[List[str]] = []
    ready = sorted([n for n in nodes if indeg[n] == 0])

    processed = set()
    while ready:
        stage = list(ready)
        stages.append(stage)
        ready = []
        for n in stage:
            processed.add(n)
            for d in downstream.get(n, set()):
                indeg[d] -= 1
                if indeg[d] == 0:
                    ready.append(d)
        ready = sorted(ready)

    if len(processed) != len(nodes):
        raise ValueError("Cycle detected in basin dependency graph.")
    return stages


def main() -> None:
    basin = json.loads(BASIN_JSON.read_text(encoding="utf-8"))

    outlets: Dict[str, str] = dict(basin["outlets"])
    ponds_dir = BASIN_DIR / "ponds"

    manifests: Dict[str, PondManifest] = {}
    edges: Dict[str, Set[str]] = {}
    pond_paths: Dict[str, str] = {}
    pond_versions: Dict[str, str] = {}

    def read_manifest(pond_name: str) -> PondManifest:
        if pond_name in manifests:
            return manifests[pond_name]

        mf_path = ponds_dir / pond_name / "duckstring.manifest.json"
        if not mf_path.exists():
            raise FileNotFoundError(f"Missing manifest for pond {pond_name!r}: {mf_path}")

        mf = PondManifest.from_dict(json.loads(mf_path.read_text(encoding="utf-8")))
        manifests[pond_name] = mf

        edges[pond_name] = set(mf.sources.keys())
        pond_versions[pond_name] = mf.version

        # store absolute path to hydrated code dir
        pond_paths[pond_name] = str((ponds_dir / pond_name).resolve())
        return mf

    def visit(pond_name: str) -> None:
        mf = read_manifest(pond_name)
        for up in mf.sources.keys():
            visit(up)

    # Discover all ponds required by outlets
    for out in outlets.keys():
        visit(out)

    # Validate outlet version pins match manifests (demo assumes pinned = exact)
    for out_name, out_ver in outlets.items():
        actual = pond_versions.get(out_name)
        if actual is None:
            raise KeyError(f"Outlet pond {out_name!r} not discovered during hydration.")
        if actual != out_ver:
            raise ValueError(
                f"Outlet {out_name!r} requires version {out_ver!r} but manifest is {actual!r}."
            )

    # Validate that all upstream edges are present as hydrated ponds
    for n, ups in list(edges.items()):
        missing = sorted([u for u in ups if u not in edges])
        if missing:
            raise ValueError(
                f"Pond {n!r} depends on missing ponds (not hydrated / missing manifests): {missing}"
            )

    # Build parallel stages from DAG
    stages = _layered_stages(edges)

    # Duck assignment per pond: basin.ducks.ponds overrides basin.ducks.default
    ducks = basin.get("ducks") or {}
    default_duck = ducks.get("default")
    pond_ducks = dict(ducks.get("ponds") or {})

    if not default_duck:
        raise ValueError("basin.ducks.default must be set before hydration.")

    instances = dict(ducks.get("instances") or {})
    if default_duck not in instances:
        raise ValueError(f"basin.ducks.default={default_duck!r} not found in basin.ducks.instances")

    for pond_name, duck_name in pond_ducks.items():
        if duck_name not in instances:
            raise ValueError(
                f"basin.ducks.ponds[{pond_name!r}] refers to unknown duck instance {duck_name!r}"
            )

    hydrated_ponds: Dict[str, dict] = {}
    for pond_name in sorted(edges.keys()):
        version = pond_versions[pond_name]
        deps = sorted(edges[pond_name])
        duck_name = pond_ducks.get(pond_name, default_duck)

        hydrated_ponds[pond_name] = {
            "version": version,
            "major": _parse_major(version),
            "path": pond_paths[pond_name],
            "dependencies": deps,
            "run_if": "all_succeeded",
            "duck": duck_name,
        }

    basin["hydrated"] = {
        "ponds": hydrated_ponds,
        "stages": stages,
    }

    BASIN_JSON.write_text(json.dumps(basin, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Hydrated basin into {BASIN_JSON}")


if __name__ == "__main__":
    main()
