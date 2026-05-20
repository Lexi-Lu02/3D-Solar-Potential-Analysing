"""
Melbourne CBD solar yield constants.

Single source of truth for all kWh calculations. The data pipeline
(Data wrangling/build_geojson.py) also embeds these values directly.

Monthly kWh formula:

    kwh_monthly[i] = usable_roof_area
                     × PANEL_EFFICIENCY
                     × PERFORMANCE_RATIO
                     × MONTHLY_PSH[i]
                     × DAYS_IN_MONTH[i]

    kwh_annual = sum(kwh_monthly)   # guarantees monthly totals match the annual figure exactly

Data source:

MONTHLY_PSH is derived from the NASA POWER climatology API (20-year mean, 2001–2020),
coordinates: lat=-37.818, lng=144.968, parameter: ALLSKY_SFC_SW_DWN, unit: kWh/m²/day.

The raw NASA annual mean is 4.51 PSH/day, roughly 10% higher than the ground-measured
value from BOM station 086338 (Melbourne Observatory). To remove the systematic high
bias that satellite data shows for overcast coastal cities, all 12 monthly values are
scaled proportionally (factor = 4.1 / 4.51 = 0.9090…) so the annual mean equals the
BOM-validated reference value of 4.1:

    sum(MONTHLY_PSH[i] × DAYS_IN_MONTH[i]) / 365 ≈ 4.10 ✓

Scaling preserves the seasonal shape from NASA POWER (higher in summer, lower in winter)
while anchoring to the BOM annual baseline.

To update (e.g. when the 30-year climate baseline refreshes around 2030), re-fetch from:
    https://power.larc.nasa.gov/api/temporal/climatology/point
        ?parameters=ALLSKY_SFC_SW_DWN&community=RE
        &longitude=144.968&latitude=-37.818&format=JSON
Then recalculate the scaling factor using the new annual mean.
"""

from __future__ import annotations

from typing import Final

# --- Annual constants -------------------------------------------------------

PANEL_EFFICIENCY: Final[float] = 0.20
"""Solar panel conversion efficiency (20%), typical commercial crystalline silicon."""

PERFORMANCE_RATIO: Final[float] = 0.75
"""System performance ratio: accounts for inverter losses, dust, wiring, and temperature."""

PEAK_SUN_HOURS: Final[float] = 4.1
"""Annual average daily peak sun hours for Melbourne CBD, from BOM station 086338."""

DAYS_PER_YEAR: Final[int] = 365

# --- Monthly PSH (NASA POWER × BOM scaling factor 0.9090) -------------------
# Index 0 = January, index 11 = December.

MONTHLY_PSH: Final[tuple[float, ...]] = (
    6.56,  # Jan  (raw 7.22 × 0.909)
    5.71,  # Feb  (raw 6.28 × 0.909)
    4.59,  # Mar  (raw 5.05 × 0.909)
    3.18,  # Apr  (raw 3.50 × 0.909)
    2.16,  # May  (raw 2.38 × 0.909)
    1.69,  # Jun  (raw 1.86 × 0.909)
    1.86,  # Jul  (raw 2.04 × 0.909)
    2.61,  # Aug  (raw 2.87 × 0.909)
    3.72,  # Sep  (raw 4.09 × 0.909)
    4.92,  # Oct  (raw 5.42 × 0.909)
    5.78,  # Nov  (raw 6.36 × 0.909)
    6.49,  # Dec  (raw 7.14 × 0.909)
)
# Verify: sum(psh[i] * days[i]) / 365 ≈ 4.10

DAYS_IN_MONTH: Final[tuple[int, ...]] = (
    31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
)

MONTH_NAMES: Final[tuple[str, ...]] = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)
