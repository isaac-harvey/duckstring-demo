from __future__ import annotations

import ibis

from duckstring import Pond


POND_VERSION = "2.0.0"


def pond(resolver=None) -> Pond:
    """
    Demo pond: enriched

    Adds derived fields to the raw NYC Taxi trip rows.
    """
    p = Pond(
        name="enriched",
        description="Enriched NYC Taxi trips with derived metrics.",
        version=POND_VERSION,
    )
    p.source({"ingest": "0.1.0"})
    if resolver is not None:
        p.attach_resolver(resolver)

    trips = p.upstream["ingest"].get(
        "trips_raw",
        {
            "vendor_id": "vendor_id",
            "pickup_at": "pickup_at",
            "dropoff_at": "dropoff_at",
            "passenger_count": "passenger_count",
            "trip_distance": "trip_distance",
            "rate_code_id": "rate_code_id",
            "pickup_location_id": "pickup_location_id",
            "dropoff_location_id": "dropoff_location_id",
            "payment_type": "payment_type",
            "fare_amount": "fare_amount",
            "extra": "extra",
            "tip_amount": "tip_amount",
            "tolls_amount": "tolls_amount",
            "improvement_surcharge": "improvement_surcharge",
            "total_amount": "total_amount",
            "congestion_surcharge": "congestion_surcharge",
            "airport_fee": "airport_fee",
        },
    )

    duration_sec = (
        trips.dropoff_at.epoch_seconds() - trips.pickup_at.epoch_seconds()
    ).name("duration_sec")
    duration_min = (duration_sec / 60.0).name("duration_min")
    speed_mph = ibis.ifelse(
        duration_sec > 0,
        trips.trip_distance / (duration_sec / 3600.0),
        ibis.literal(None, type="float64"),
    ).name("speed_mph")
    fare_per_mile = ibis.ifelse(
        trips.trip_distance > 0,
        trips.fare_amount / trips.trip_distance,
        ibis.literal(None, type="float64"),
    ).name("fare_per_mile")

    out = trips.mutate(
        trip_date=trips.pickup_at.date(),
        duration_sec=duration_sec,
        duration_min=duration_min,
        speed_mph=speed_mph,
        fare_per_mile=fare_per_mile,
    )

    p.sink({"trips_enriched": out}, description="NYC Taxi trips with derived metrics.")
    p.flow([None])
    return p
