from __future__ import annotations

from duckstring import Pond, Snapshot


POND_VERSION = "0.2.0"
SNAPSHOT_JSON = "snapshot.json"


def pond() -> Pond:
    """
    Demo pond: aggregated

    Aggregates enriched NYC Taxi trip data to daily summaries.
    """
    p = Pond(
        name="aggregated",
        description="Daily aggregates of enriched NYC Taxi trips.",
        version=POND_VERSION,
    )
    p.source({"enriched": "0.2.0"})

    trips = p.upstream["enriched"].get(
        "trips_enriched",
        {
            "trip_date": "trip_date",
            "passenger_count": "passenger_count",
            "trip_distance": "trip_distance",
            "fare_amount": "fare_amount",
            "speed_mph": "speed_mph",
            "fare_per_mile": "fare_per_mile",
        },
    )

    out = trips.group_by("trip_date").aggregate(
        trips=trips.count(),
        total_passengers=trips.passenger_count.sum(),
        avg_distance=trips.trip_distance.mean(),
        total_fare=trips.fare_amount.sum(),
        avg_fare=trips.fare_amount.mean(),
        avg_speed_mph=trips.speed_mph.mean(),
        avg_fare_per_mile=trips.fare_per_mile.mean(),
    )

    p.sink({"trip_daily_summary": out}, description="Daily summary metrics for NYC Taxi trips.")
    return p


def run() -> None:
    """
    Run the pond to materialize its outputs.
    """
    # Load active snapshot
    snap = Snapshot.load_active(SNAPSHOT_JSON)

    # Run against the snapshot
    # Ducks can be selected from the species specified against the snapshot's sink
    # The default is an instance of the default species
    # in_place (default True) modifies the sinks directly, while False creates a copy before modifying - useful for verifying incremental logic
    snap.flow(in_place=False)

    # Alternatively if a specific duck species needs to be used:
    # snap.flow(duck="local", in_place=False)

    # Optionally do something with the output tables
    out = snap.get("trip_daily_summary")
    print(out)


if __name__ == "__main__":
    run()
