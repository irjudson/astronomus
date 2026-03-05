"""JPL Horizons integration for fetching comet data."""

from datetime import datetime
from typing import List, Optional

from astropy.time import Time
from astroquery.jplhorizons import Horizons

from app.models import CometTarget, OrbitalElements


class HorizonsService:
    """Service for fetching comet data from JPL Horizons."""

    def __init__(self):
        """Initialize Horizons service."""
        pass

    def fetch_comet_by_designation(self, designation: str, epoch: Optional[datetime] = None) -> Optional[CometTarget]:
        """
        Fetch comet orbital elements from JPL Horizons.

        Args:
            designation: Comet designation (e.g., "C/2020 F3")
            epoch: Epoch for orbital elements (defaults to current time)

        Returns:
            CometTarget with orbital elements, or None if not found
        """
        try:
            # Use current time if epoch not specified
            if epoch is None:
                epoch = datetime.utcnow()

            # Convert to astropy Time
            epoch_time = Time(epoch)

            # Query Horizons for orbital elements
            # For comets, we need to use the designation as the target ID
            # Horizons uses specific formats, so we may need to adjust
            obj = Horizons(id=designation, location="@sun", epochs=epoch_time.jd)  # Heliocentric

            # Get orbital elements
            elements = obj.elements()

            if len(elements) == 0:
                return None

            # Extract first (and usually only) result
            elem = elements[0]

            # Parse comet type from eccentricity
            e = float(elem["e"])
            if e < 1.0:
                # Elliptical orbit
                period_years = float(elem["P"]) if "P" in elem.colnames else None
                if period_years and period_years < 20:
                    comet_type = "short-period"
                else:
                    comet_type = "long-period"
            else:
                # Hyperbolic orbit
                comet_type = "hyperbolic"

            # Create orbital elements
            orbital_elements = OrbitalElements(
                epoch_jd=float(elem["datetime_jd"]),
                perihelion_distance_au=float(elem["q"]),
                eccentricity=e,
                inclination_deg=float(elem["incl"]),
                arg_perihelion_deg=float(elem["w"]),
                ascending_node_deg=float(elem["Omega"]),
                perihelion_time_jd=float(elem["Tp_jd"]),
            )

            # Extract magnitude parameters if available
            absolute_mag = None
            mag_slope = 4.0  # Default for comets

            # Try to get magnitude from element set
            if "M1" in elem.colnames:  # Absolute magnitude
                absolute_mag = float(elem["M1"])
            if "K1" in elem.colnames:  # Magnitude slope
                mag_slope = float(elem["K1"])

            # Estimate current magnitude if available
            current_mag = None
            if "V" in elem.colnames:
                current_mag = float(elem["V"])

            # Create comet target
            comet = CometTarget(
                designation=designation,
                name=None,  # Could be extracted from designation or looked up separately
                orbital_elements=orbital_elements,
                absolute_magnitude=absolute_mag,
                magnitude_slope=mag_slope,
                current_magnitude=current_mag,
                comet_type=comet_type,
                activity_status="unknown",
                discovery_date=None,  # Not typically in elements
                data_source="JPL Horizons",
                notes=f"Orbital elements from JPL Horizons, epoch JD {orbital_elements.epoch_jd}",
            )

            return comet

        except Exception as e:
            print(f"Error fetching comet {designation} from Horizons: {e}")
            return None

    def fetch_bright_comets(self, max_magnitude: float = 12.0, epoch: Optional[datetime] = None) -> List[CometTarget]:
        """
        Fetch list of currently bright comets using MPC data.

        First attempts to use the MPC comet catalog (active comets near perihelion).
        Falls back to a curated list of well-known periodic comets if MPC is unavailable.

        Args:
            max_magnitude: Maximum (faintest) magnitude to include
            epoch: Epoch for orbital elements

        Returns:
            List of bright comets
        """
        # Try MPC first (live data, includes newly discovered comets)
        try:
            mpc_comets = self.fetch_active_comets_from_mpc(max_years_from_perihelion=2.0)
            if mpc_comets:
                if max_magnitude is not None:
                    mpc_comets = [
                        c for c in mpc_comets if c.current_magnitude is None or c.current_magnitude <= max_magnitude
                    ]
                return sorted(
                    mpc_comets, key=lambda c: c.current_magnitude if c.current_magnitude is not None else 99.0
                )
        except Exception as e:
            print(f"MPC fetch failed, falling back to curated list: {e}")

        # Fallback: curated list of periodic comets + recent notable comets
        known_comets = [
            "2P/Encke",
            "9P/Tempel 1",
            "46P/Wirtanen",
            "67P/Churyumov-Gerasimenko",
            "73P/Schwassmann-Wachmann",
            "103P/Hartley",
            "12P/Pons-Brooks",
            "13P/Olbers",
            "C/2023 A3",  # Tsuchinshan-ATLAS
            "C/2024 G3",  # ATLAS
            "C/2022 E3",  # ZTF
        ]

        bright_comets = []
        for designation in known_comets:
            try:
                comet = self.fetch_comet_by_designation(designation, epoch)
                if comet and (comet.current_magnitude is None or comet.current_magnitude <= max_magnitude):
                    bright_comets.append(comet)
            except Exception as e:
                print(f"Skipping {designation}: {e}")
                continue

        return bright_comets

    def fetch_active_comets_from_mpc(self, max_years_from_perihelion: float = 2.0) -> List[CometTarget]:
        """
        Fetch currently active comets from the Minor Planet Center.

        Queries MPC for comet orbital elements and filters to those near perihelion
        (and therefore likely to be currently observable).

        Args:
            max_years_from_perihelion: Include comets within this many years of perihelion

        Returns:
            List of CometTarget objects for active comets
        """
        from astropy.time import Time
        from astroquery.mpc import MPC

        now_jd = Time.now().jd
        max_dt_days = max_years_from_perihelion * 365.25

        elements = MPC.get_elements("comet")  # Returns astropy Table with all comets

        results = []
        for row in elements:
            try:
                # Perihelion time as JD — column is 'Tp_jd' in astroquery MPC table
                tp_jd = float(row["Tp_jd"]) if "Tp_jd" in elements.colnames else None
                if tp_jd is None or abs(tp_jd - now_jd) > max_dt_days:
                    continue

                designation = str(row["Designation_and_name"]).strip()
                # Split name from designation (MPC combines them)
                name = None
                if "(" in designation:
                    name = designation[designation.index("(") + 1 : designation.rindex(")")]
                    designation = designation[: designation.index("(")].strip()

                e = float(row["e"])
                if e < 1.0:
                    period_years = float(row["P"]) if "P" in elements.colnames and row["P"] else None
                    comet_type = "short-period" if period_years and period_years < 20 else "long-period"
                else:
                    comet_type = "hyperbolic"

                orbital_elements = OrbitalElements(
                    epoch_jd=float(row["Epoch_jd"]) if "Epoch_jd" in elements.colnames else now_jd,
                    perihelion_distance_au=float(row["q"]),
                    eccentricity=e,
                    inclination_deg=float(row["i"]),
                    arg_perihelion_deg=float(row["w"]),
                    ascending_node_deg=float(row["Node"]),
                    perihelion_time_jd=tp_jd,
                )

                absolute_mag = float(row["M1"]) if "M1" in elements.colnames and row["M1"] else None
                mag_slope = float(row["K1"]) if "K1" in elements.colnames and row["K1"] else 4.0

                results.append(
                    CometTarget(
                        designation=designation,
                        name=name,
                        orbital_elements=orbital_elements,
                        absolute_magnitude=absolute_mag,
                        magnitude_slope=mag_slope,
                        current_magnitude=None,  # Will be calculated from ephemeris
                        comet_type=comet_type,
                        activity_status="active",
                        data_source="MPC",
                        notes=f"Near perihelion (Tp JD {tp_jd:.1f})",
                    )
                )
            except Exception:
                continue

        return results

    def fetch_ephemeris(
        self,
        designation: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        step: str = "1d",
        location: str = "500",  # Geocentric
    ) -> dict:
        """
        Fetch ephemeris (positions) for a comet over a time range.

        Args:
            designation: Comet designation
            start_time: Start time for ephemeris
            end_time: End time (if None, only compute for start_time)
            step: Time step (e.g., '1d', '1h')
            location: Observer location (default: '500' = geocentric)

        Returns:
            Dictionary with ephemeris data including RA, Dec, distance, magnitude
        """
        try:
            # Convert to astropy Time
            start_t = Time(start_time)

            if end_time:
                end_t = Time(end_time)
                epochs = {"start": start_t.iso, "stop": end_t.iso, "step": step}
            else:
                epochs = start_t.jd

            # Query Horizons
            obj = Horizons(id=designation, location=location, epochs=epochs)

            # Get ephemeris
            eph = obj.ephemerides()

            # Convert to dictionary format
            result = {"designation": designation, "data": []}

            for row in eph:
                result["data"].append(
                    {
                        "datetime_jd": float(row["datetime_jd"]),
                        "datetime_str": row["datetime_str"],
                        "ra_deg": float(row["RA"]),
                        "dec_deg": float(row["DEC"]),
                        "ra_hours": float(row["RA"]) / 15.0,
                        "dec_degrees": float(row["DEC"]),
                        "delta_au": float(row["delta"]),  # Earth distance
                        "r_au": float(row["r"]),  # Sun distance
                        "elongation_deg": float(row["elong"]) if "elong" in row.colnames else None,
                        "magnitude": float(row["V"]) if "V" in row.colnames else None,
                    }
                )

            return result

        except Exception as e:
            print(f"Error fetching ephemeris for {designation}: {e}")
            return {"designation": designation, "data": [], "error": str(e)}
