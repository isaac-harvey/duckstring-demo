from __future__ import annotations

import ibis

from duckstring import Pond


POND_VERSION = "0.1.0"
SOURCE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"


def pond(resolver=None) -> Pond:
    """
    Demo pond: ingest

    Ingests NYC Taxi yellow trips for Jan 2023 from a public parquet file.
    """
    p = Pond(
        name="ingest",
        description="Ingest NYC Taxi trips (Jan 2023) from a public parquet source.",
        version=POND_VERSION,
    )
    if resolver is not None:
        p.attach_resolver(resolver)

    trips = ibis.read_parquet(SOURCE_URL)

    out = trips.select(
        vendor_id=trips.VendorID.cast("int64"),
        pickup_at=trips.tpep_pickup_datetime.cast("timestamp"),
        dropoff_at=trips.tpep_dropoff_datetime.cast("timestamp"),
        passenger_count=trips.passenger_count.cast("int64"),
        trip_distance=trips.trip_distance.cast("float64"),
        rate_code_id=trips.RatecodeID.cast("int64"),
        pickup_location_id=trips.PULocationID.cast("int64"),
        dropoff_location_id=trips.DOLocationID.cast("int64"),
        payment_type=trips.payment_type.cast("int64"),
        fare_amount=trips.fare_amount.cast("float64"),
        extra=trips.extra.cast("float64"),
        mta_tax=trips.mta_tax.cast("float64"),
        tip_amount=trips.tip_amount.cast("float64"),
        tolls_amount=trips.tolls_amount.cast("float64"),
        improvement_surcharge=trips.improvement_surcharge.cast("float64"),
        total_amount=trips.total_amount.cast("float64"),
        congestion_surcharge=trips.congestion_surcharge.cast("float64"),
        airport_fee=trips.airport_fee.cast("float64"),
    )

    p.sink({"trips_raw": out}, description="Raw NYC Taxi trip rows (Jan 2023).")
    p.flow([None])
    return p
