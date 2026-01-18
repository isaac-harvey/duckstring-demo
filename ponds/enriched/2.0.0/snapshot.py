from __future__ import annotations

from pathlib import Path

from duckstring import Catchment, Snapshot

from pond import pond

SNAPSHOT_JSON = "snapshot.json"


def _load_source_catchment() -> Catchment:
    repo_root = Path(__file__).resolve().parents[3]
    return Catchment.load(str(repo_root / "catchment.json"))


def snapshot() -> Snapshot:
    """
    Small subset snapshot for quick development and iteration.
    """
    p = pond()

    source = _load_source_catchment()
    sink = Catchment(root_dir=".duckstring/small")

    snap = Snapshot(
        name="small",
        description="Small subset of source data for quick development and testing.",
        pond=p,
        source_catchment=source,
        sink_catchment=sink,
    )

    trips = snap.upstream["ingest"].get("trips_raw", infer_select=True)
    trips = trips.order_by(trips.pickup_at).limit(20_000)
    snap.sink(trips)

    return snap


if __name__ == "__main__":
    snap = snapshot()
    snap.materialize(registry_path=SNAPSHOT_JSON, activate=True, verbose=True)
