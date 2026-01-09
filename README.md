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

    python create_catchment.py
    python basins/main/create_basin.py

3) Hydrate basin (copies pond code into .duckstring/ponds/):

    python basins/main/hydrate.py

4) Pulse:

    python basins/main/pulse.py

Outputs
-------

- .duckstring/state/duckstring.duckdb
- .duckstring/data/ingest@0.1.0/trips_raw.parquet
- .duckstring/data/enriched@0.1.0/trips_enriched.parquet
- .duckstring/data/aggregated@0.1.0/trip_daily_summary.parquet

Versioning demo
---------------

This repo includes multiple pond versions and basins to show how dependency
resolution behaves across minor/major changes. The sequence below depends on
prior runs because the resolver will auto-upgrade dependencies within the same
major based on the last successful version in catchment state.

Setup once
~~~~~~~~~~

    python create_catchment.py
    python basins/base/create_basin.py
    python basins/minor/create_basin.py
    python basins/upstream_major/create_basin.py
    python basins/downstream_major/create_basin.py

Then hydrate each basin before the first pulse:

    python basins/base/hydrate.py
    python basins/minor/hydrate.py
    python basins/upstream_major/hydrate.py
    python basins/downstream_major/hydrate.py

Run sequence with expectations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1) base
   Command:
     python basins/base/pulse.py
   Expected resolution:
     ingest@0.1.0 > enriched@0.1.0 > aggregated@0.1.0

2) minor
   Command:
     python basins/minor/pulse.py
   Expected resolution:
     ingest@0.1.0 > enriched@0.2.0 > aggregated@0.2.0

3) base (auto-upgrade within major 0)
   Command:
     python basins/base/pulse.py
   Expected resolution:
     ingest@0.1.0 > enriched@0.2.0 > aggregated@0.1.0

4) upstream_major
   Command:
     python basins/upstream_major/pulse.py
   Expected resolution:
     ingest@0.1.0 > enriched@2.0.0 > aggregated@0.3.0

5) base (major 0 stays on its last minor)
   Command:
     python basins/base/pulse.py
   Expected resolution:
     ingest@0.1.0 > enriched@0.2.0 > aggregated@0.1.0

6) minor
   Command:
     python basins/minor/pulse.py
   Expected resolution:
     ingest@0.1.0 > enriched@0.2.0 > aggregated@0.2.0

7) downstream_major (breaking change in aggregated)
   Command:
     python basins/downstream_major/pulse.py
   Expected resolution:
     ingest@0.1.0 > enriched@2.0.0 > aggregated@1.0.0

8) upstream_major (unchanged vs step 4)
   Command:
     python basins/upstream_major/pulse.py
   Expected resolution:
     ingest@0.1.0 > enriched@2.0.0 > aggregated@0.3.0

9) base (major 0 still on last minor)
   Command:
     python basins/base/pulse.py
   Expected resolution:
     ingest@0.1.0 > enriched@0.2.0 > aggregated@0.1.0

10) minor
    Command:
      python basins/minor/pulse.py
    Expected resolution:
      ingest@0.1.0 > enriched@0.2.0 > aggregated@0.2.0
