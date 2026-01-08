from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Set, List

from duckstring import PondManifest


REPO_ROOT = Path(__file__).resolve().parents[2]
CATCHMENT_JSON = REPO_ROOT / "catchment.json"
BASIN_DIR = Path(__file__).resolve().parent
BASIN_JSON = BASIN_DIR / "basin.json"


def _toposort(edges: Dict[str, Set[str]]) -> List[str]:
    nodes = set(edges.keys())
    indeg = {n: 0 for n in nodes}
    downstream = {n: set() for n in nodes}

    for n, ups in edges.items():
        for u in ups:
            if u not in nodes:
                continue
            indeg[n] += 1
            downstream[u].add(n)

    q = [n for n in sorted(nodes) if indeg[n] == 0]
    out: List[str] = []
    while q:
        n = q.pop(0)
        out.append(n)
        for d in sorted(downstream.get(n, set())):
            indeg[d] -= 1
            if indeg[d] == 0:
                q.append(d)

    if len(out) != len(nodes):
        raise ValueError("Cycle detected in basin dependency graph.")
    return out


def main() -> None:
    _ = json.loads(CATCHMENT_JSON.read_text(encoding="utf-8"))
    basin = json.loads(BASIN_JSON.read_text(encoding="utf-8"))

    outlets: Dict[str, str] = dict(basin["outlets"])
    ponds_dir = BASIN_DIR / "ponds"

    manifests: Dict[str, PondManifest] = {}
    edges: Dict[str, Set[str]] = {}
    versions: Dict[str, str] = {}
    pond_paths: Dict[str, str] = {}

    def read_manifest(pond_name: str) -> PondManifest:
        if pond_name in manifests:
            return manifests[pond_name]
        mf_path = ponds_dir / pond_name / "duckstring.manifest.json"
        if not mf_path.exists():
            raise FileNotFoundError(f"Missing manifest for pond {pond_name!r}: {mf_path}")
        mf = PondManifest.from_dict(json.loads(mf_path.read_text(encoding="utf-8")))
        manifests[pond_name] = mf
        edges[pond_name] = set(mf.sources.keys())
        versions[pond_name] = mf.version
        pond_paths[pond_name] = str((ponds_dir / pond_name).as_posix())
        return mf

    def visit(pond_name: str) -> None:
        mf = read_manifest(pond_name)
        for up in mf.sources.keys():
            visit(up)

    for out in outlets.keys():
        visit(out)

    topo = _toposort(edges)

    basin["resolved"] = {
        "ponds_topo": topo,
        "pond_paths": pond_paths,
        "pond_versions": versions,
        "generated_by": "basins/main/hydrate.py",
    }

    BASIN_JSON.write_text(json.dumps(basin, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Hydrated basin DAG into {BASIN_JSON}")


if __name__ == "__main__":
    main()
