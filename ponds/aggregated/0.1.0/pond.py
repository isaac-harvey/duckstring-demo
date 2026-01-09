from __future__ import annotations

from duckstring import Pond


POND_VERSION = "0.1.0"


def pond(resolver=None) -> Pond:
    """
    Demo pond: aggregated

    Aggregates enriched NYC Taxi trip data to daily summaries.
    """
    p = Pond(
        name="aggregated",
        description="Daily aggregates of enriched NYC Taxi trips.",
        version=POND_VERSION,
    )
    p.source({"enriched": "0.1.0"})
    if resolver is not None:
        p.attach_resolver(resolver)

    trips = p.upstream["enriched"].get(
        "trips_enriched",
        {
            "trip_date": "trip_date",
            "passenger_count": "passenger_count",
            "trip_distance": "trip_distance",
            "fare_amount": "fare_amount",
            "speed_mph": "speed_mph",
        },
    )

    out = trips.group_by("trip_date").aggregate(
        trips=trips.count(),
        total_passengers=trips.passenger_count.sum(),
        avg_distance=trips.trip_distance.mean(),
        total_fare=trips.fare_amount.sum(),
        avg_fare=trips.fare_amount.mean(),
        avg_speed_mph=trips.speed_mph.mean(),
    )

    p.sink({"trip_daily_summary": out}, description="Daily summary metrics for NYC Taxi trips.")
    p.flow([None])
    return p
