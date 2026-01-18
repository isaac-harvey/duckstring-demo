from __future__ import annotations

from pathlib import Path

from duckstring import Catchment, Snapshot
from .pond import pond


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

    trips = snap.upstream["enriched"].get("trips_enriched", infer_select=True)
    trips = (
        trips.filter(trips.trip_date >= "2022-01-01")
        .filter(trips.trip_date < "2023-01-01")
        .order_by(trips.trip_date)
        .limit(20_000)
    )
    snap.sink(trips)

    trip_daily_summary = snap.downstream.get("trip_daily_summary")
    trip_daily_summary = trip_daily_summary.filter(trip_daily_summary.ds_pulse <= 12)
    snap.sink(trip_daily_summary)

    return snap


if __name__ == "__main__":
    snap = snapshot()
    snap.materialize(registry_path=SNAPSHOT_JSON, activate=True, verbose=True)
