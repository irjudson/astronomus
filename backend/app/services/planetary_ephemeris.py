"""Planetary ephemeris service for calculating real-time positions of planets and moons."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from skyfield.api import Topos, load
from skyfield.searchlib import find_discrete
from skyfield.timelib import Time

logger = logging.getLogger(__name__)


class PlanetaryEphemeris:
    """Calculate positions of planets, moons, and the Sun using Skyfield."""

    def __init__(self):
        """Initialize ephemeris with DE421 planetary data."""
        self.eph = load("de421.bsp")
        self.ts = load.timescale()

        # Define celestial bodies
        self.bodies = {
            "sun": self.eph["sun"],
            "moon": self.eph["moon"],
            "mercury": self.eph["mercury"],
            "venus": self.eph["venus"],
            "mars": self.eph["mars"],
            "jupiter": self.eph["jupiter barycenter"],
            "saturn": self.eph["saturn barycenter"],
            "uranus": self.eph["uranus barycenter"],
            "neptune": self.eph["neptune barycenter"],
        }

        # Display names
        self.display_names = {
            "sun": "Sun",
            "moon": "Moon",
            "mercury": "Mercury",
            "venus": "Venus",
            "mars": "Mars",
            "jupiter": "Jupiter",
            "saturn": "Saturn",
            "uranus": "Uranus",
            "neptune": "Neptune",
        }

    def get_position(
        self, body_name: str, latitude: float, longitude: float, elevation: float = 0.0, time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get position of a celestial body from observer location.

        Args:
            body_name: Name of body ('sun', 'moon', 'mercury', etc.)
            latitude: Observer latitude in degrees
            longitude: Observer longitude in degrees
            elevation: Observer elevation in meters
            time: Observation time (UTC), defaults to now

        Returns:
            Dict with:
                - ra_hours: Right ascension in hours
                - dec_degrees: Declination in degrees
                - altitude: Altitude above horizon in degrees
                - azimuth: Azimuth in degrees
                - distance_au: Distance in astronomical units
                - magnitude: Visual magnitude (if available)
                - phase: Phase angle for moon (0-1)
                - illumination: Illumination percentage (0-100)
        """
        if body_name not in self.bodies:
            raise ValueError(f"Unknown body: {body_name}. Valid: {list(self.bodies.keys())}")

        # Create observer location
        observer = self.eph["earth"] + Topos(
            latitude_degrees=latitude, longitude_degrees=longitude, elevation_m=elevation
        )

        # Get current time or use provided
        if time is None:
            time = datetime.now(timezone.utc)
        t = self.ts.from_datetime(time)

        # Calculate position
        body = self.bodies[body_name]
        astrometric = observer.at(t).observe(body)

        # Get RA/Dec
        ra, dec, distance = astrometric.radec()

        # Get Alt/Az
        alt, az, distance = astrometric.apparent().altaz()

        result = {
            "name": self.display_names[body_name],
            "ra_hours": ra.hours,
            "dec_degrees": dec.degrees,
            "altitude": alt.degrees,
            "azimuth": az.degrees,
            "distance_au": distance.au,
            "visible": alt.degrees > 0,  # Above horizon
        }

        # Add magnitude if available
        try:
            result["magnitude"] = astrometric.apparent().magnitude()
        except Exception:
            result["magnitude"] = None

        # Add moon-specific data
        if body_name == "moon":
            sun = self.bodies["sun"]
            moon_phase_data = self._calculate_moon_phase(observer, t, body, sun)
            result.update(moon_phase_data)

        return result

    def _calculate_moon_phase(self, observer: any, time: Time, moon: any, sun: any) -> Dict[str, float]:
        """Calculate moon phase and illumination.

        Args:
            observer: Observer location
            time: Observation time
            moon: Moon body
            sun: Sun body

        Returns:
            Dict with phase, illumination percentage, and phase name
        """
        # Get positions
        moon_pos = observer.at(time).observe(moon)
        sun_pos = observer.at(time).observe(sun)

        # Calculate phase angle
        moon_apparent = moon_pos.apparent()
        sun_apparent = sun_pos.apparent()

        # Get elongation (angle between moon and sun)
        elongation = moon_apparent.separation_from(sun_apparent).degrees

        # Phase: 0 = new moon, 0.5 = full moon, 1.0 = new moon
        phase = elongation / 180.0

        # Illumination percentage
        illumination = (1 - abs(phase - 0.5) * 2) * 100

        # Phase name
        if phase < 0.125 or phase >= 0.875:
            phase_name = "New Moon"
        elif phase < 0.375:
            phase_name = "Waxing Crescent"
        elif phase < 0.625:
            phase_name = "Full Moon"
        else:
            phase_name = "Waning Crescent"

        return {
            "phase": phase,
            "illumination": illumination,
            "phase_name": phase_name,
        }

    def get_all_visible(
        self,
        latitude: float,
        longitude: float,
        elevation: float = 0.0,
        time: Optional[datetime] = None,
        min_altitude: float = 0.0,
    ) -> List[Dict[str, float]]:
        """Get all visible celestial bodies above the horizon.

        Args:
            latitude: Observer latitude in degrees
            longitude: Observer longitude in degrees
            elevation: Observer elevation in meters
            time: Observation time (UTC), defaults to now
            min_altitude: Minimum altitude in degrees

        Returns:
            List of position dicts for visible bodies
        """
        visible = []

        for body_name in self.bodies.keys():
            try:
                position = self.get_position(body_name, latitude, longitude, elevation, time)

                if position["altitude"] >= min_altitude:
                    visible.append(position)
            except Exception as e:
                logger.error(f"Error calculating position for {body_name}: {e}")

        # Sort by altitude (highest first)
        visible.sort(key=lambda x: x["altitude"], reverse=True)

        return visible

    def get_rise_set_times(
        self, body_name: str, latitude: float, longitude: float, elevation: float = 0.0, date: Optional[datetime] = None
    ) -> Dict[str, Optional[datetime]]:
        """Calculate rise and set times for a celestial body.

        Args:
            body_name: Name of body
            latitude: Observer latitude in degrees
            longitude: Observer longitude in degrees
            elevation: Observer elevation in meters
            date: Date to calculate for (defaults to today)

        Returns:
            Dict with 'rise' and 'set' datetime objects (UTC), or None if circumpolar
        """
        if body_name not in self.bodies:
            raise ValueError(f"Unknown body: {body_name}")

        # Create observer
        observer = self.eph["earth"] + Topos(
            latitude_degrees=latitude, longitude_degrees=longitude, elevation_m=elevation
        )

        # Set time range (24 hours from date)
        if date is None:
            date = datetime.now(timezone.utc)

        t0 = self.ts.from_datetime(date.replace(hour=0, minute=0, second=0))
        t1 = self.ts.from_datetime(date.replace(hour=23, minute=59, second=59))

        # Find rise/set events
        body = self.bodies[body_name]
        f = (observer + body).at

        def is_above_horizon(t):
            """Check if body is above horizon."""
            alt, _, _ = f(t).apparent().altaz()
            return alt.degrees > 0

        times, events = find_discrete(t0, t1, is_above_horizon)

        # Parse events: True = rise, False = set
        rise_time = None
        set_time = None

        for t, event in zip(times, events):
            dt = t.utc_datetime()
            if event:  # Rising
                rise_time = dt
            else:  # Setting
                set_time = dt

        return {
            "rise": rise_time,
            "set": set_time,
        }


# Global instance
_ephemeris = None


def get_ephemeris() -> PlanetaryEphemeris:
    """Get global ephemeris instance (singleton)."""
    global _ephemeris
    if _ephemeris is None:
        _ephemeris = PlanetaryEphemeris()
    return _ephemeris
