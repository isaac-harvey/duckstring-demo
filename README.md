duckstring-demo
===============

A runnable demo repo for duckstring's v1 local Catchment/Basin/Pond + pulse execution.

This version uses a three-layer pond stack:

- ingest: reads NYC Taxi Trips (Jan 2023) from a public parquet URL
- enriched: adds derived fields like duration and speed
- aggregated: daily summary metrics

Quick start
-----------

1) Install duckstring from your main repo (editable), then install demo deps:

    uv pip install -e ../duckstring
    uv pip install -e .

(or use pip)

2) (Optional) regenerate specs (JSONs are included already):

    python create_catchment_.py
    python basins/main/create_basin_.py

3) Hydrate basin (copies pond code into .duckstring/ponds/):

    python basins/main/hydrate_.py

4) Pulse:

    python basins/main/pulse_.py

Outputs
-------

- .duckstring/state/duckstring.duckdb
- .duckstring/data/ingest@0.1.0/trips_raw.parquet
- .duckstring/data/enriched@0.1.0/trips_enriched.parquet
- .duckstring/data/aggregated@0.1.0/trip_daily_summary.parquet
