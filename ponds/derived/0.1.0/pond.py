from __future__ import annotations

from duckstring import Pond


POND_VERSION = "0.1.0"


def pond(resolver=None) -> Pond:
    """
    Demo pond: derived

    Produces a 1-row table with:
      - n_pulses: total number of rows in base.pulse
      - span: seconds between first and last pulse
      - mean_pulse_separation: span / n_pulses
    """
    p = Pond(
        name="derived",
        description="Pulse metrics derived from base.pulse history.",
        version=POND_VERSION,
    )
    p.source({"base": "0.1.0"})
    if resolver is not None:
        p.attach_resolver(resolver)

    pulses = p.upstream["base"].get("pulse", {"ts": "ts"})

    agg = pulses.aggregate(
        n_pulses=pulses.count(),
        ts_min=pulses.ts.min(),
        ts_max=pulses.ts.max(),
    )

    # epoch_seconds() exists on many ibis timestamp expressions; adjust if your ibis version differs.
    span = (agg.ts_max.epoch_seconds() - agg.ts_min.epoch_seconds()).name("span")

    out = (
        agg.mutate(
            span=span,
            mean_pulse_separation=(span / agg.n_pulses).name("mean_pulse_separation"),
        )
        .select("n_pulses", "span", "mean_pulse_separation")
    )

    p.sink({"pulse_stats": out})
    p.flow([None])
    return p
