"""
Sun position calculation for Melbourne CBD (Epic 4).

Azimuth convention: clockwise from North (N=0, E=90, S=180, W=270).
Matches frontend sun-direction-line rendering. pysolar.get_azimuth already
uses this convention for the Southern Hemisphere.

Sanity check values (Melbourne noon):
  Dec 21:  altitude ~76°, azimuth ~0-10°
  Mar 21:  altitude ~52°, azimuth ~0°
  Jun 21:  altitude ~29°, azimuth ~0°
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from pysolar.solar import get_altitude, get_azimuth

# Melbourne CBD reference point
MELBOURNE_LAT = -37.8136
MELBOURNE_LNG = 144.9631
MELBOURNE_TZ = ZoneInfo("Australia/Melbourne")


def get_sun_position(date_iso: str, hour: float) -> dict:
    """
    Return sun altitude and azimuth above Melbourne CBD.

    Args:
        date_iso: local date as 'YYYY-MM-DD'
        hour:     decimal hour 0-24 (e.g. 13.5 = 13:30)

    Returns:
        altitude_deg:  clamped to >= 0 (below horizon → 0)
        azimuth_deg:   [0, 360), N=0 clockwise
        shadow_factor: 90 / altitude_deg, capped. None when below horizon.
    """
    h = int(hour)
    m = int(round((hour - h) * 60))
    if m == 60:
        h += 1
        m = 0

    dt = datetime.fromisoformat(date_iso).replace(
        hour=h, minute=m, second=0, microsecond=0, tzinfo=MELBOURNE_TZ
    )
    altitude = get_altitude(MELBOURNE_LAT, MELBOURNE_LNG, dt)
    azimuth = get_azimuth(MELBOURNE_LAT, MELBOURNE_LNG, dt)

    altitude_clamped = max(0.0, altitude)
    return {
        "altitude_deg": round(altitude_clamped, 2),
        "azimuth_deg": round(azimuth % 360, 2),
        "shadow_factor": (
            round(90.0 / max(altitude_clamped, 0.01), 2)
            if altitude_clamped > 0
            else None
        ),
    }