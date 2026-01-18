from __future__ import annotations

"""
snapshot.py

Offline/dev UX for ponds via "snapshots":

A Snapshot materializes (copies) a *subset* of upstream input tables into a local
sink catchment, so the pond can be executed offline against those inputs.

Key design points (captured here for future implementation):

- Snapshot definitions are Python/Ibis (no YAML), matching the pond coding UX.
- Snapshot uses the pond's own upstream declarations as the single source of truth
  for where data comes from (versions, upstream pond names, etc).
- Per-table snapshot logic is expressed in Ibis and typically only uses safe ops:
  filter/select/limit/order_by/sample/distinct. Other ops are allowed but should
  emit WARNINGS (not errors) by default, with an opt-in strict mode later.
- Column selection:
  - Pond upstream.get(..., select_map=...) is required; Snapshot infer_select=True
    must rely on that stored select-map metadata.
  - If no select-map metadata exists, which should be impossible, ERROR.
- Metadata:
  - The object returned by snap.upstream[...] should attach hidden TableRef metadata
    (upstream pond ref + upstream table name + select-map) to the Ibis table/expr,
    so snap.sink(expr) can infer identity without extra args.
- Sink catchment management:
  - Each snapshot has its own sink catchment, scoped to *this pond*.
  - Materialization should create/maintain a snapshot registry file (snapshot.json)
    that records snapshots, their sink catchment locations/settings, and which
    snapshot is currently active.
  - Tools (periscope/run/etc) can default to the "active" snapshot's catchment
    when no catchment is explicitly provided.

Suggested snapshot registry structure (example):
{
  "active": "small",
  "snapshots": {
    "small": {
      "description": "...",
      "pond": {"name": "aggregated", "version": "1.0.0"},
      "source_catchment": {"root_dir": "path/to/.duckstring", ...},
      "sink_catchment": {"root_dir": ".duckstring", ...},
      "materialized_at": "2026-01-12T15:00:00+11:00",
      "sources": {
        "enriched@2.0.0": {
          "trips_enriched": {
            "rows": 20000,
            "sql": "SELECT ... FROM ... WHERE ..."
          }
        }
      }
    }
  }
}

Implementation notes for Snapshot.materialize(registry_path=...):
- Loads/creates snapshot.json
- Ensures sink_catchment exists on disk and has a catchment.json
- Materializes each declared snap.sink(...) table into sink catchment storage
- Updates registry entry + sets active snapshot (default True)
"""

from duckstring import Catchment, Snapshot
from .pond import pond


SNAPSHOT_JSON = "snapshot.json"


def snapshot() -> Snapshot:
    """
    Small subset snapshot for quick development and iteration.

    Pattern:
    - Build the pond (single source of truth for upstream refs + select-maps).
    - Define source catchment (where upstream data is read from).
    - Define sink catchment (where the local snapshot will be written).
    - For each table you want in the snapshot:
        - obtain via snap.upstream[...] (carries metadata)
        - apply Ibis filtering/sampling/limit logic
        - register with snap.sink(expr)
    """
    # Pond definition (contains upstream pond refs and required select-maps).
    p = pond()

    # Source catchment: where the referenced upstream tables currently live.
    source = Catchment.load("source_catchment.json")

    # Sink catchment: where the snapshot tables should go.
    ## Most of the time the default Catchment() is adequate (local, DuckDB engine), but any catchment can be specified (e.g. remote storage)
    ## Snapshots follow the same version rules as for Basins: keep the maximum pond_version within a major, create a new version directory for each major
    ## Snapshotted upstream tables for a sink catchment will go to {root_dir}/snapshots/{pond_name}/{pond_version}/upstream/{upstream_pond_name}/{upstream_pond_version}/{table_name}
    ## Snapshotted downstream tables (within this pond) will go to {root_dir}/snapshots/{pond_name}/{pond_version}/downstream/{table_name}
    ## Output downstream tables (within this pond), the result of a pulse, will go to {root_dir}/snapshots/{pond_name}/{pond_version}/output/{table_name}
    ## If using snap.flow(in_place=True) and the tables in .../output/... do not yet exist, the source data is .../downstream/...
    ## If using snap.flow(in_place=True) and the tables in .../output/... do already exist, the source data is .../output/...
    ## If using snap.flow(in_place=False) the source data is .../downstream/... and the tables in .../output/... are overwritten
    sink = Catchment(root_dir=".duckstring/small")

    # Instantiate snapshot
    snap = Snapshot(
        name="small",
        description="Small subset of source data for quick development and testing.",
        pond=p,
        source_catchment=source,
        sink_catchment=sink,
    )

    # Retrieve upstream table
    # - With infer_select=True (default False), the select dict used for this table in the pond is used to define the set of columns to retrieve (so that only used columns are snapshotted)
    # - Unlike in the pond, the select is without alias (only the keys are considered)
    # - If the table was not used in a .get() operation in the pond, infer_select results in SELECT *
    # - If the table was used in multiple .get() operations, infer_select results in the full set of columns from any .get() operation
    trips = snap.upstream["enriched"].get("trips_enriched", infer_select=True)

    # Apply snapshot subset logic (Ibis).
    # Recommended for deterministic "tiny" datasets: order_by + limit.
    trips = (
        trips.filter(trips.trip_date >= "2022-01-01")
        .filter(trips.trip_date < "2023-01-01")
        .order_by(trips.trip_date)
        .limit(20_000)
    )

    # Register this table for materialization into the sink catchment.
    # snap.sink(expr) should infer destination identity from attached TableRef metadata:
    # - upstream pond ref (e.g. enriched@2.0.0)
    # - upstream table name (trips_enriched)
    snap.sink(trips)

    # Repeat for other upstream tables as needed:
    # other = snap.upstream["enriched"].get("other_table", infer_select=True)
    # other = other.filter(...).limit(...)
    # snap.sink(other)

    # Retrieve downstream table
    # - Downstream tables (within the pond) can be omitted if the pond overwrites on sink
    # - This is mostly used to test things like incremental loads or schema migrations
    trip_daily_summary = snap.downstream.get("trip_daily_summary")

    # - Example where a max pulse is loaded to test incremental logic
    MAX_PULSE = 12
    trip_daily_summary = (
        trip_daily_summary.filter(trip_daily_summary.ds_pulse <= MAX_PULSE)
    )

    snap.sink(trip_daily_summary)

    return snap


if __name__ == "__main__":
    snap = snapshot()

    # Materialize snapshot into sink catchment and update snapshot registry.
    #
    # Expected behavior for materialize():
    # - Creates/updates SNAPSHOT_JSON (registry) in the pond repo
    # - Writes/updates sink catchment.json under sink.root_dir
    # - Copies only tables declared via snap.sink(...)
    # - Validates Ibis op allowlist; emits warnings for disallowed ops (default),
    #   with a future strict=True mode to error.
    # - Sets this snapshot as active in the registry unless activate=False.
    snap.materialize(registry_path=SNAPSHOT_JSON, activate=True, verbose=True)
