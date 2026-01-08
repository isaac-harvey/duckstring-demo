duckstring-demo
===============

A runnable demo repo for duckstring's v1 local Catchment/Basin/Pond + pulse execution.

Quick start
-----------

1) Install duckstring from your main repo (editable), then install demo deps:

    uv pip install -e ../duckstring
    uv pip install -e .

(or use pip)

2) (Optional) regenerate specs (JSONs are included already):

    python create_catchment.py
    python basins/main/create_basin.py

3) Hydrate basin (build DAG metadata into basin.json):

    python basins/main/hydrate.py

4) Pulse:

    python basins/main/pulse.py

Outputs
-------

- catchment/state/duckstring.duckdb
- catchment/data/base/pulse.parquet
- catchment/data/derived/pulse_stats.parquet
- catchment/state/demo_pulses.sqlite  (persistent pulse log backing base.pulse)

Notes
-----

This demo implements "append" semantics for base.pulse by persisting pulse timestamps to SQLite
and rebuilding the full history into DuckDB on each run. This is a deliberate workaround for
duckstring v1's "replace materialization" behavior; later versions can make this native.
