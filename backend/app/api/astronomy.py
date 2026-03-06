"""Astronomy-specific API endpoints."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import pytz
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models import DSOTarget, Location
from app.services.ephemeris_service import EphemerisService
from app.services.local_weather_service import LocalWeatherService
from app.services.satellite_service import SatelliteService
from app.services.seven_timer_service import SevenTimerService
from app.services.viewing_months_service import ViewingMonthsService
from app.services.weather_service import WeatherService

router = APIRouter(tags=["astronomy"])


# Request/Response Models
class AstronomyWeatherResponse(BaseModel):
    """Response model for astronomy weather forecast."""

    forecast: List[dict]
    location: dict


class SatellitePassResponse(BaseModel):
    """Response model for satellite passes."""

    passes: List[dict]
    satellite_name: str
    location: dict
    days: int


class ViewingMonthsResponse(BaseModel):
    """Response model for viewing months."""

    months: List[dict]
    object_name: Optional[str] = None
    coordinates: dict


# ========================================================================
# ClearDarkSky Weather Endpoint
# ========================================================================


@router.get("/weather/astronomy")
async def get_astronomy_weather(
    lat: float = Query(..., description="Latitude in decimal degrees", ge=-90, le=90),
    lon: float = Query(..., description="Longitude in decimal degrees", ge=-180, le=180),
    hours: int = Query(48, description="Forecast period in hours", ge=1, le=120),
):
    """
    Get astronomy-specific weather forecast for a location.

    This endpoint provides astronomy-focused weather information including:
    - Cloud cover (clear, mostly clear, partly cloudy, etc.)
    - Atmospheric transparency (excellent to poor)
    - Astronomical seeing conditions (excellent to poor)
    - Temperature and wind speed
    - Overall astronomy quality score (0-1)

    Data is sourced from 7Timer API which provides astronomy-specific forecasts.

    Args:
        lat: Latitude in decimal degrees (-90 to +90)
        lon: Longitude in decimal degrees (-180 to +180)
        hours: Forecast period in hours (default: 48, max: 120)

    Returns:
        Astronomy weather forecast with conditions and quality scores
    """
    try:
        # Validate coordinates
        if not (-90 <= lat <= 90):
            raise HTTPException(status_code=400, detail=f"Invalid latitude: {lat}. Must be between -90 and +90.")
        if not (-180 <= lon <= 180):
            raise HTTPException(status_code=400, detail=f"Invalid longitude: {lon}. Must be between -180 and +180.")

        # Use 7Timer service for astronomy-specific forecasts
        location = Location(
            name="Forecast Location",
            latitude=lat,
            longitude=lon,
            elevation=0.0,
            timezone="UTC",
        )

        service = SevenTimerService()
        now = datetime.now(timezone.utc)
        end_time = now + timedelta(hours=hours)

        forecasts = service.get_astronomy_forecast(location, now, end_time)

        # Convert forecast objects to dicts with astronomy scores
        weather_service = WeatherService()
        forecast_data = []
        for entry in forecasts:
            # Calculate astronomy score (0-1 scale, multiply by 100 for frontend)
            score = weather_service.calculate_weather_score(entry)

            forecast_data.append(
                {
                    "time": entry.timestamp.isoformat(),
                    "cloud_cover": entry.cloud_cover,  # Direct percentage from 7Timer
                    "transparency": entry.transparency_magnitude,
                    "seeing": entry.seeing_arcseconds,
                    "temperature_c": entry.temperature,
                    "wind_speed_kmh": entry.wind_speed * 3.6,  # Convert m/s to km/h
                    "conditions": entry.conditions,
                    "astronomy_score": score,  # 0-1 scale
                }
            )

        return {
            "forecast": forecast_data,
            "location": {"latitude": lat, "longitude": lon},
            "hours": hours,
            "count": len(forecast_data),
            "source": "7timer",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching astronomy weather: {str(e)}")


@router.get("/weather/local")
async def get_local_weather():
    """
    Get current conditions from the local Ambient Weather WS-2902 station.

    Returns real-time outdoor temperature, humidity, wind, rain, pressure,
    UV index, solar radiation, and an astronomy suitability assessment.
    Returns 503 if the station is unreachable.
    """
    reading = LocalWeatherService().get_current()
    if reading is None:
        raise HTTPException(status_code=503, detail="Local weather station unreachable")
    return reading.to_dict()


# ========================================================================
# Satellite Pass Prediction Endpoints
# ========================================================================


@router.get("/satellites/iss")
async def get_iss_passes(
    lat: float = Query(..., description="Latitude in decimal degrees", ge=-90, le=90),
    lon: float = Query(..., description="Longitude in decimal degrees", ge=-180, le=180),
    days: int = Query(10, description="Number of days to predict", ge=1, le=30),
    min_altitude: float = Query(0.0, description="Minimum altitude in degrees", ge=0, le=90),
):
    """
    Get ISS (International Space Station) pass predictions.

    This endpoint provides upcoming visible passes of the ISS for a specific
    location. Each pass includes:
    - Start and end times
    - Maximum altitude and time
    - Start and end azimuth directions
    - Visibility classification (excellent, good, fair, poor)
    - Apparent magnitude (brightness)
    - Quality score (0-1)

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        days: Number of days to predict (default: 10, max: 30)
        min_altitude: Minimum altitude threshold (default: 0)

    Returns:
        List of ISS pass predictions sorted by start time
    """
    try:
        # Validate coordinates
        if not (-90 <= lat <= 90):
            raise HTTPException(status_code=400, detail=f"Invalid latitude: {lat}. Must be between -90 and +90.")
        if not (-180 <= lon <= 180):
            raise HTTPException(status_code=400, detail=f"Invalid longitude: {lon}. Must be between -180 and +180.")

        service = SatelliteService()
        passes = service.get_iss_passes(latitude=lat, longitude=lon, days=days, min_altitude=min_altitude)

        # Convert pass objects to dicts
        passes_data = []
        for pass_obj in passes:
            passes_data.append(
                {
                    "satellite_name": pass_obj.satellite_name,
                    "start_time": pass_obj.start_time.isoformat(),
                    "end_time": pass_obj.end_time.isoformat(),
                    "max_altitude_deg": pass_obj.max_altitude_deg,
                    "max_altitude_time": pass_obj.max_altitude_time.isoformat(),
                    "start_azimuth_deg": pass_obj.start_azimuth_deg,
                    "end_azimuth_deg": pass_obj.end_azimuth_deg,
                    "visibility": pass_obj.visibility.name.lower(),
                    "magnitude": pass_obj.magnitude,
                    "duration_minutes": pass_obj.duration_minutes(),
                    "quality_score": pass_obj.quality_score(),
                }
            )

        return {
            "passes": passes_data,
            "satellite_name": "ISS (ZARYA)",
            "location": {"latitude": lat, "longitude": lon},
            "days": days,
            "count": len(passes_data),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ISS passes: {str(e)}")


@router.get("/satellites/passes")
async def get_satellite_passes(
    norad_id: int = Query(..., description="NORAD catalog ID"),
    lat: float = Query(..., description="Latitude in decimal degrees", ge=-90, le=90),
    lon: float = Query(..., description="Longitude in decimal degrees", ge=-180, le=180),
    days: int = Query(10, description="Number of days to predict", ge=1, le=30),
    satellite_name: str = Query("Satellite", description="Display name for satellite"),
    min_altitude: float = Query(0.0, description="Minimum altitude in degrees", ge=0, le=90),
):
    """
    Get pass predictions for any satellite by NORAD ID.

    Args:
        norad_id: NORAD catalog ID (e.g., 25544 for ISS, 20580 for Hubble)
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        days: Number of days to predict
        satellite_name: Display name for the satellite
        min_altitude: Minimum altitude threshold

    Returns:
        List of satellite pass predictions
    """
    try:
        # Validate coordinates
        if not (-90 <= lat <= 90):
            raise HTTPException(status_code=400, detail=f"Invalid latitude: {lat}. Must be between -90 and +90.")
        if not (-180 <= lon <= 180):
            raise HTTPException(status_code=400, detail=f"Invalid longitude: {lon}. Must be between -180 and +180.")

        service = SatelliteService()
        passes = service.get_satellite_passes(
            norad_id=norad_id,
            satellite_name=satellite_name,
            latitude=lat,
            longitude=lon,
            days=days,
            min_altitude=min_altitude,
        )

        # Convert pass objects to dicts
        passes_data = []
        for pass_obj in passes:
            passes_data.append(
                {
                    "satellite_name": pass_obj.satellite_name,
                    "start_time": pass_obj.start_time.isoformat(),
                    "end_time": pass_obj.end_time.isoformat(),
                    "max_altitude_deg": pass_obj.max_altitude_deg,
                    "max_altitude_time": pass_obj.max_altitude_time.isoformat(),
                    "start_azimuth_deg": pass_obj.start_azimuth_deg,
                    "end_azimuth_deg": pass_obj.end_azimuth_deg,
                    "visibility": pass_obj.visibility.name.lower(),
                    "magnitude": pass_obj.magnitude,
                    "duration_minutes": pass_obj.duration_minutes(),
                    "quality_score": pass_obj.quality_score(),
                }
            )

        return {
            "passes": passes_data,
            "satellite_name": satellite_name,
            "norad_id": norad_id,
            "location": {"latitude": lat, "longitude": lon},
            "days": days,
            "count": len(passes_data),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching satellite passes: {str(e)}")


# ========================================================================
# Best Viewing Months Endpoints
# ========================================================================


@router.get("/viewing-months")
async def get_viewing_months(
    ra_hours: float = Query(..., description="Right ascension in hours (0-24)", ge=0, lt=24),
    dec_degrees: float = Query(..., description="Declination in degrees (-90 to +90)", ge=-90, le=90),
    latitude: float = Query(..., description="Observer latitude", ge=-90, le=90),
    object_name: Optional[str] = Query(None, description="Optional object name for reference"),
):
    """
    Calculate best viewing months for a celestial object.

    This endpoint calculates month-by-month viewing conditions based on:
    - Object coordinates (RA and Dec)
    - Observer latitude
    - Seasonal night length variations
    - Object altitude at transit
    - Evening visibility

    Each month receives:
    - Rating (excellent, good, fair, poor, not visible)
    - Visibility hours (time above minimum altitude)
    - Best observation time
    - Notes about conditions

    Args:
        ra_hours: Right ascension in hours (0-24)
        dec_degrees: Declination in degrees (-90 to +90)
        latitude: Observer latitude in degrees
        object_name: Optional name for display

    Returns:
        12 months of viewing data with ratings and recommendations
    """
    try:
        # Validate astronomical coordinates
        if not (0 <= ra_hours < 24):
            raise HTTPException(status_code=400, detail=f"Invalid right ascension: {ra_hours}. Must be 0-24 hours.")
        if not (-90 <= dec_degrees <= 90):
            raise HTTPException(
                status_code=400, detail=f"Invalid declination: {dec_degrees}. Must be -90 to +90 degrees."
            )
        if not (-90 <= latitude <= 90):
            raise HTTPException(status_code=400, detail=f"Invalid latitude: {latitude}. Must be -90 to +90 degrees.")

        service = ViewingMonthsService()
        months = service.calculate_viewing_months(
            ra_hours=ra_hours, dec_degrees=dec_degrees, latitude=latitude, object_name=object_name
        )

        # Convert month objects to dicts
        months_data = []
        for month in months:
            months_data.append(
                {
                    "month": month.month,
                    "month_name": month.month_name,
                    "rating": month.rating.name.lower(),
                    "rating_value": month.rating.value,
                    "visibility_hours": month.visibility_hours,
                    "best_time": month.best_time,
                    "notes": month.notes,
                    "is_good_month": month.is_good_month(),
                }
            )

        return {
            "months": months_data,
            "object_name": object_name,
            "coordinates": {"ra_hours": ra_hours, "dec_degrees": dec_degrees},
            "observer_latitude": latitude,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating viewing months: {str(e)}")


@router.get("/viewing-months/summary")
async def get_viewing_months_summary(
    ra_hours: float = Query(..., description="Right ascension in hours (0-24)", ge=0, lt=24),
    dec_degrees: float = Query(..., description="Declination in degrees (-90 to +90)", ge=-90, le=90),
    latitude: float = Query(..., description="Observer latitude", ge=-90, le=90),
    object_name: Optional[str] = Query(None, description="Optional object name"),
):
    """
    Get summary of best viewing months for an object.

    Returns a concise summary including:
    - Best 3 months for observation
    - Peak viewing month
    - Total number of good viewing months
    - Visibility date ranges

    Args:
        ra_hours: Right ascension in hours (0-24)
        dec_degrees: Declination in degrees (-90 to +90)
        latitude: Observer latitude
        object_name: Optional object name

    Returns:
        Summary of viewing conditions across the year
    """
    try:
        # Validate astronomical coordinates
        if not (0 <= ra_hours < 24):
            raise HTTPException(status_code=400, detail=f"Invalid right ascension: {ra_hours}. Must be 0-24 hours.")
        if not (-90 <= dec_degrees <= 90):
            raise HTTPException(
                status_code=400, detail=f"Invalid declination: {dec_degrees}. Must be -90 to +90 degrees."
            )

        service = ViewingMonthsService()
        months = service.calculate_viewing_months(
            ra_hours=ra_hours, dec_degrees=dec_degrees, latitude=latitude, object_name=object_name
        )

        summary = service.get_viewing_summary(months)

        return {
            **summary,
            "object_name": object_name,
            "coordinates": {"ra_hours": ra_hours, "dec_degrees": dec_degrees},
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating viewing summary: {str(e)}")


@router.get("/altitude-curve")
async def get_altitude_curve(
    lat: float = Query(..., description="Observer latitude", ge=-90, le=90),
    lon: float = Query(..., description="Observer longitude", ge=-180, le=180),
    imaging_start: str = Query(..., description="Session start as ISO 8601 string"),
    imaging_end: str = Query(..., description="Session end as ISO 8601 string"),
    ra_hours: Optional[float] = Query(None, description="Right ascension in hours (fixed objects)", ge=0, lt=24),
    dec_degrees: Optional[float] = Query(None, description="Declination in degrees (fixed objects)", ge=-90, le=90),
    body_name: Optional[str] = Query(None, description="Solar system body name (e.g. Mars, Moon, Sun)"),
):
    """
    Return altitude sampled every 15 minutes across a session window.

    Supports both fixed sky objects (via ra_hours + dec_degrees) and moving
    solar system bodies (via body_name). Used by plan and discovery cards.

    Returns:
        { points: [[iso_str, altitude_deg], ...] }
    """
    try:
        import astropy.units as u
        from astropy.coordinates import AltAz, EarthLocation, get_body, get_sun
        from astropy.time import Time

        start_dt = datetime.fromisoformat(imaging_start)
        end_dt = datetime.fromisoformat(imaging_end)

        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        if end_dt <= start_dt:
            raise HTTPException(status_code=400, detail="imaging_end must be after imaging_start")

        interval = timedelta(minutes=15)
        times = []
        t = start_dt
        while t <= end_dt:
            times.append(t)
            t += interval
        if times[-1] != end_dt:
            times.append(end_dt)

        points = []

        if body_name:
            # Solar system body — recompute RA/Dec at each sample time
            name = body_name.strip().title()
            earth_location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
            for dt in times:
                t_ast = Time(dt.astimezone(timezone.utc))
                altaz_frame = AltAz(obstime=t_ast, location=earth_location)
                if name == "Sun":
                    body_coord = get_sun(t_ast)
                else:
                    body_coord = get_body(name.lower(), t_ast)
                alt_deg = body_coord.transform_to(altaz_frame).alt.degree
                points.append([dt.isoformat(), round(alt_deg, 2)])

        elif ra_hours is not None and dec_degrees is not None:
            # Fixed DSO — use EphemerisService
            location = Location(latitude=lat, longitude=lon, elevation=0, name="observer", timezone="UTC")
            target = DSOTarget(
                catalog_id="_curve",
                name="_curve",
                ra_hours=ra_hours,
                dec_degrees=dec_degrees,
                object_type="galaxy",
                magnitude=0.0,
                size_arcmin=0.0,
            )
            ephemeris = EphemerisService()
            for dt in times:
                alt, _ = ephemeris.calculate_position(target, location, dt)
                points.append([dt.isoformat(), round(alt, 2)])

        else:
            raise HTTPException(status_code=400, detail="Provide either ra_hours+dec_degrees or body_name")

        return {"points": points}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing altitude curve: {str(e)}")
