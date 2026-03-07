"""API routes for the Astro Planner."""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.asteroids import router as asteroid_router
from app.api.astronomy import router as astronomy_router
from app.api.captures import router as captures_router

# Import comet, asteroid, planet, processing, plans, astronomy, and settings routers
from app.api.comets import router as comet_router
from app.api.planets import router as planet_router
from app.api.plans import router as plans_router
from app.api.processing import router as processing_router
from app.api.settings import router as settings_router
from app.api.telescope import router as telescope_router
from app.api.telescope_features import router as telescope_features_router
from app.api.user_preferences import router as user_preferences_router
from app.database import get_db
from app.models import DSOTarget, ExportFormat, Location, ObservingPlan, PlanRequest
from app.services.catalog_service import CatalogService
from app.services.light_pollution_service import LightPollutionService
from app.services.planner_service import PlannerService

router = APIRouter()

router.include_router(comet_router)
router.include_router(asteroid_router)
router.include_router(planet_router)
router.include_router(processing_router)
router.include_router(plans_router)
router.include_router(astronomy_router)
router.include_router(settings_router)
router.include_router(captures_router)
router.include_router(telescope_router)
router.include_router(telescope_features_router, prefix="/telescope/features", tags=["telescope-features"])
router.include_router(user_preferences_router, prefix="/user", tags=["user"])

# Short-lived in-memory store for shareable plan links (plan_id -> (plan, expiry_time))
# Plans expire after 24 h to prevent unbounded memory growth.
import time as _time

shared_plans: Dict[str, tuple[ObservingPlan, float]] = {}
SHARED_PLAN_TTL = 86400  # 24 hours

# Simple TTL cache for catalog queries (cache_key -> (result, expiry_time))
catalog_cache: Dict[str, tuple[Any, float]] = {}
CATALOG_CACHE_TTL = 60  # seconds


@router.post("/plan", response_model=ObservingPlan)
async def generate_plan(request: PlanRequest, db: Session = Depends(get_db)):
    """
    Generate a complete observing plan.

    This endpoint orchestrates the entire planning process:
    - Calculates twilight times
    - Filters targets by type
    - Fetches weather forecast
    - Schedules targets using greedy algorithm
    - Returns complete plan

    Args:
        request: Plan request with location, date, and constraints

    Returns:
        Complete observing plan with scheduled targets
    """
    try:
        planner = PlannerService(db)
        plan = planner.generate_plan(request)
        return plan
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating plan: {str(e)}")


@router.get("/targets", response_model=List[DSOTarget])
async def list_targets(
    db: Session = Depends(get_db),
    object_types: Optional[List[str]] = Query(None, description="Filter by object types (can specify multiple)"),
    min_magnitude: Optional[float] = Query(None, description="Minimum magnitude (brighter objects have lower values)"),
    max_magnitude: Optional[float] = Query(None, description="Maximum magnitude (fainter limit)"),
    constellation: Optional[str] = Query(None, description="Filter by constellation (3-letter abbreviation)"),
    limit: Optional[int] = Query(100, description="Maximum number of results (default: 100, max: 1000)", le=1000),
    offset: int = Query(0, description="Offset for pagination (default: 0)", ge=0),
    include_visibility: bool = Query(True, description="Include real-time visibility calculations"),
    sort_by: str = Query("magnitude", description="Sort order: magnitude|size|name|visibility"),
):
    """
    List available DSO targets with advanced filtering, sorting, and optional visibility.

    Supports filtering by:
    - Object type (galaxy, nebula, cluster, planetary_nebula)
    - Magnitude range (brightness)
    - Constellation
    - Pagination (limit/offset)

    Examples:
    - /targets?limit=20 - Get 20 brightest objects
    - /targets?object_types=galaxy&object_types=nebula - Get galaxies and nebulae
    - /targets?max_magnitude=10&limit=50 - Get 50 objects brighter than magnitude 10
    - /targets?constellation=Ori - Get all objects in Orion
    - /targets?sort_by=visibility&include_visibility=true - Get objects sorted by visibility

    Args:
        object_types: Filter by one or more object types
        min_magnitude: Filter by minimum magnitude (brighter)
        max_magnitude: Filter by maximum magnitude (fainter)
        constellation: Filter by constellation
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
        include_visibility: Calculate real-time visibility (requires location in settings)
        sort_by: Sort order (magnitude, size, name, visibility)

    Returns:
        List of DSO targets matching filters with optional visibility info
    """
    try:
        from datetime import datetime

        import pytz

        from app.services.ephemeris_service import EphemerisService
        from app.services.settings_service import SettingsService

        catalog_service = CatalogService(db)

        # For visibility sort, DB already orders by magnitude ASC — limit to 500 at the DB level.
        # For other sorts we need all records in Python first, then paginate.
        db_limit = 500 if sort_by == "visibility" else None
        targets = catalog_service.filter_targets(
            object_types=object_types,
            min_magnitude=min_magnitude,
            max_magnitude=max_magnitude,
            constellation=constellation,
            limit=db_limit,
            offset=0,
        )

        # Performance optimization: Only calculate visibility for ALL targets if sorting by visibility
        # Otherwise, sort first, paginate, then calculate visibility only for paginated results
        if sort_by == "visibility" and include_visibility:
            # DB already returned the 500 brightest sorted by magnitude — no Python sort needed
            targets_for_visibility = targets

            try:
                settings_service = SettingsService(db)
                location = settings_service.get_location()

                if location:
                    ephemeris = EphemerisService()
                    current_time = datetime.now(pytz.timezone(location.timezone))

                    # Add visibility to each target (only brightest 500)
                    targets_for_visibility = [
                        catalog_service.add_visibility_info(target, location, ephemeris, current_time)
                        for target in targets_for_visibility
                    ]
            except Exception as e:
                # If visibility fails, continue without it
                logger.warning("Could not calculate visibility: %s", e)

            # Sort by: optimal now > visible > rising > setting > below horizon
            # Within each group, sort by altitude
            def visibility_sort_key(t):
                if not t.visibility:
                    return (999, -999)  # No visibility - sort last

                status_order = {"visible": 0, "rising": 1, "setting": 2, "below_horizon": 3}
                status_rank = status_order.get(t.visibility.status, 999)

                # Within status, prefer higher altitude
                alt = t.visibility.current_altitude

                return (status_rank, -alt)

            targets_for_visibility.sort(key=visibility_sort_key)

            # Apply pagination after sorting by visibility
            paginated = targets_for_visibility[offset : offset + limit] if limit else targets_for_visibility[offset:]

        else:
            # Sort by non-visibility fields first (no visibility calculation needed)
            if sort_by == "magnitude":
                targets.sort(key=lambda t: t.magnitude)
            elif sort_by == "size":
                targets.sort(key=lambda t: t.size_arcmin, reverse=True)
            elif sort_by == "name":
                targets.sort(key=lambda t: t.catalog_id)

            # Apply pagination BEFORE calculating visibility (performance optimization)
            paginated = targets[offset : offset + limit] if limit else targets[offset:]

            # Now add visibility only to the paginated results
            if include_visibility:
                try:
                    settings_service = SettingsService(db)
                    location = settings_service.get_location()

                    if location:
                        ephemeris = EphemerisService()
                        current_time = datetime.now(pytz.timezone(location.timezone))

                        # Add visibility to each paginated target
                        paginated = [
                            catalog_service.add_visibility_info(target, location, ephemeris, current_time)
                            for target in paginated
                        ]
                except Exception as e:
                    # If visibility fails, continue without it
                    logger.warning("Could not calculate visibility: %s", e)

        # Add capture history for all paginated targets (single efficient query)
        try:
            from app.models.capture_models import CaptureHistory

            # Extract catalog IDs from paginated targets
            catalog_ids = [target.catalog_id for target in paginated]

            # Fetch all capture history in ONE query (not N+1)
            if catalog_ids:
                try:
                    capture_histories = (
                        db.query(CaptureHistory).filter(CaptureHistory.catalog_id.in_(catalog_ids)).all()
                    )

                    # Create a dictionary mapping catalog_id -> capture history data
                    capture_dict = {
                        ch.catalog_id: {
                            "total_exposure_seconds": ch.total_exposure_seconds,
                            "total_frames": ch.total_frames,
                            "total_sessions": ch.total_sessions,
                            "first_captured_at": ch.first_captured_at.isoformat() if ch.first_captured_at else None,
                            "last_captured_at": ch.last_captured_at.isoformat() if ch.last_captured_at else None,
                            "status": ch.status,
                            "suggested_status": ch.suggested_status,
                            "best_fwhm": ch.best_fwhm,
                            "best_star_count": ch.best_star_count,
                        }
                        for ch in capture_histories
                    }

                    # Merge capture history into each target using model_copy for immutability
                    paginated = [
                        (
                            target.model_copy(update={"capture_history": capture_dict[target.catalog_id]})
                            if target.catalog_id in capture_dict
                            else target
                        )
                        for target in paginated
                    ]
                except Exception as query_error:
                    # If session is in failed transaction, just continue without capture history
                    # This can happen if visibility calculation fails first
                    logger.warning("Could not fetch capture history: %s", query_error)
        except Exception as e:
            # Outer exception handler
            logger.warning("Capture history processing failed: %s", e)

        return paginated
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching targets: {str(e)}")


@router.get("/targets/scored", response_model=List[DSOTarget])
async def list_scored_targets(
    db: Session = Depends(get_db),
    context: str = Query("tonight", description="Context for scoring: 'tonight' or 'plan'"),
    plan_id: Optional[int] = Query(None, description="Plan ID (required if context='plan')"),
    object_types: Optional[List[str]] = Query(None, description="Filter by object types"),
    limit: int = Query(100, description="Maximum number of results", le=1000),
    offset: int = Query(0, description="Offset for pagination", ge=0),
):
    """
    Get catalog targets scored and sorted by scheduler algorithm.

    This endpoint uses the same scoring logic as the planner to rank targets
    by their suitability for observation. Supports two context modes:

    - 'tonight': Score targets for tonight's observing window at saved location
    - 'plan': Score targets using parameters from a saved plan

    Args:
        context: Scoring context ('tonight' or 'plan')
        plan_id: Saved plan ID (required if context='plan')
        object_types: Filter by object types
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        List of targets sorted by scheduler score (best first)
    """
    try:
        from datetime import datetime, timedelta

        import pytz

        from app.models.plan_models import SavedPlan
        from app.services.ephemeris_service import EphemerisService
        from app.services.scheduler_service import SchedulerService
        from app.services.settings_service import SettingsService
        from app.services.weather_service import WeatherService

        # Validate context
        if context not in ["tonight", "plan"]:
            raise HTTPException(status_code=400, detail="context must be 'tonight' or 'plan'")

        if context == "plan" and not plan_id:
            raise HTTPException(status_code=400, detail="plan_id required when context='plan'")

        catalog_service = CatalogService(db)
        settings_service = SettingsService(db)
        scheduler = SchedulerService()

        # Build scoring context based on mode
        if context == "tonight":
            # Use saved location + tonight's window
            location = settings_service.get_location()
            if not location:
                raise HTTPException(status_code=400, detail="No location configured in settings")

            tz = pytz.timezone(location.timezone)
            now = datetime.now(tz)

            # Calculate tonight's twilight times
            ephemeris = EphemerisService()
            twilight_times = ephemeris.calculate_twilight_times(location, now)

            scoring_start = twilight_times["astronomical_twilight_end"]
            scoring_end = twilight_times["astronomical_twilight_start"]

            # Use default constraints
            from app.models import ObservingConstraints

            constraints = ObservingConstraints()

        else:  # context == "plan"
            # Load plan and extract context
            plan_record = db.query(SavedPlan).filter(SavedPlan.id == plan_id).first()
            if not plan_record:
                raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

            # Reconstruct plan from saved data
            from app.models import ObservingPlan

            plan = ObservingPlan(**plan_record.plan_data)

            location = plan.location
            scoring_start = plan.session.imaging_start
            scoring_end = plan.session.imaging_end

            # Use constraints stored in the plan (fall back to defaults if plan predates this field)
            from app.models import ObservingConstraints

            constraints = plan.constraints if plan.constraints is not None else ObservingConstraints()

        # Get candidate targets with filters
        targets = catalog_service.filter_targets(
            object_types=object_types,
            max_magnitude=12.0,  # Same limit as planner
            limit=500,  # Reasonable pool for scoring
            offset=0,
        )

        # Score each target using scheduler algorithm
        weather_service = WeatherService()
        weather_forecasts = weather_service.get_forecast(location, scoring_start, scoring_end)

        scored_targets = []
        for target in targets:
            # Check if visible during scoring window
            mid_time = scoring_start + (scoring_end - scoring_start) / 2
            if not scheduler.ephemeris.is_target_visible(
                target, location, mid_time, constraints.min_altitude, constraints.max_altitude
            ):
                continue

            # Calculate visibility duration
            duration = scheduler._calculate_visibility_duration(
                target, location, scoring_start, scoring_end, constraints
            )

            if duration < timedelta(minutes=scheduler.settings.min_target_duration_minutes):
                continue

            # Get weather score
            weather_score = scheduler._get_weather_score_for_time(mid_time, weather_forecasts)

            # Score the target
            score_data = scheduler._score_target(target, location, mid_time, duration, constraints, weather_score)

            # Store score in target (for sorting)
            target_with_score = target.model_copy()
            # We can't add a score field to DSOTarget, so we'll just sort by the score
            scored_targets.append((target_with_score, score_data.total_score))

        # Sort by score descending
        scored_targets.sort(key=lambda x: x[1], reverse=True)

        # Apply pagination
        paginated = [t for t, _ in scored_targets[offset : offset + limit]]

        return paginated

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error scoring targets: {str(e)}")


@router.get("/targets/{catalog_id}", response_model=DSOTarget)
async def get_target(catalog_id: str, db: Session = Depends(get_db)):
    """
    Get details for a specific target.

    Args:
        catalog_id: Catalog identifier (e.g., M31, NGC7000, C80)

    Returns:
        Target details
    """
    catalog = CatalogService(db)
    target = catalog.get_target_by_id(catalog_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"Target not found: {catalog_id}")
    return target


@router.get("/caldwell", response_model=List[DSOTarget])
async def list_caldwell_targets(
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(
        109, description="Maximum number of results (default: all 109 Caldwell objects)", le=109
    ),
    offset: int = Query(0, description="Offset for pagination (default: 0)", ge=0),
):
    """
    List all Caldwell catalog targets.

    The Caldwell Catalog is a collection of 109 deep sky objects compiled by
    Sir Patrick Caldwell-Moore for amateur astronomers. These are bright, large
    objects not included in the Messier catalog.

    Args:
        limit: Maximum number of results to return (default: all 109)
        offset: Number of results to skip (for pagination)

    Returns:
        List of Caldwell targets ordered by Caldwell number (C1-C109)
    """
    try:
        catalog = CatalogService(db)
        targets = catalog.get_caldwell_targets(limit=limit, offset=offset)
        return targets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Caldwell targets: {str(e)}")


@router.get("/search/unified")
async def unified_search(
    db: Session = Depends(get_db),
    query: str = Query(..., description="Search query (object name, catalog ID, or planet name)"),
    object_types: Optional[str] = Query(
        None, description="Comma-separated list of object types: dso, star, planet (default: all)"
    ),
    max_results: int = Query(20, description="Maximum results per type", ge=1, le=100),
):
    """
    Unified search across all catalogs: DSOs, stars, and planets.

    Search for celestial objects by name or catalog identifier across all available catalogs.
    Returns results grouped by object type (DSOs, stars, planets).

    Args:
        query: Search query string
        object_types: Filter by type (comma-separated: dso,star,planet)
        max_results: Maximum results per object type

    Returns:
        Dict with keys: dsos, stars, planets (lists of matching objects)
    """
    try:
        from sqlalchemy import func, or_

        from app.models.catalog_models import DSOCatalog, StarCatalog
        from app.services.planet_service import PlanetService

        results = {"dsos": [], "stars": [], "planets": []}

        # Parse object types filter
        if object_types:
            enabled_types = {t.strip().lower() for t in object_types.split(",")}
        else:
            enabled_types = {"dso", "star", "planet"}

        search_pattern = f"%{query}%"

        # Search DSOs
        if "dso" in enabled_types:
            dso_query = db.query(DSOCatalog).filter(
                or_(
                    DSOCatalog.common_name.ilike(search_pattern),
                    func.concat(DSOCatalog.catalog_name, DSOCatalog.catalog_number).ilike(search_pattern),
                )
            )
            dso_query = dso_query.order_by(DSOCatalog.magnitude.asc().nullslast())
            dsos = dso_query.limit(max_results).all()

            results["dsos"] = [
                {
                    "type": "dso",
                    "name": dso.common_name or f"{dso.catalog_name}{dso.catalog_number}",
                    "catalog_id": f"{dso.catalog_name}{dso.catalog_number}",
                    "object_type": dso.object_type,
                    "ra_hours": dso.ra_hours,
                    "dec_degrees": dso.dec_degrees,
                    "magnitude": dso.magnitude,
                    "size_arcmin": dso.size_arcmin,
                    "constellation": dso.constellation,
                }
                for dso in dsos
            ]

        # Search stars
        if "star" in enabled_types:
            star_query = db.query(StarCatalog).filter(
                or_(
                    StarCatalog.common_name.ilike(search_pattern),
                    StarCatalog.bayer_designation.ilike(search_pattern),
                    func.concat(StarCatalog.catalog_name, StarCatalog.catalog_number).ilike(search_pattern),
                )
            )
            star_query = star_query.order_by(StarCatalog.magnitude.asc().nullslast())
            stars = star_query.limit(max_results).all()

            results["stars"] = [
                {
                    "type": "star",
                    "name": star.common_name or star.bayer_designation or f"{star.catalog_name}{star.catalog_number}",
                    "catalog_id": f"{star.catalog_name}{star.catalog_number}",
                    "bayer_designation": star.bayer_designation,
                    "ra_hours": star.ra_hours,
                    "dec_degrees": star.dec_degrees,
                    "magnitude": star.magnitude,
                    "spectral_type": star.spectral_type,
                    "constellation": star.constellation,
                    "distance_ly": star.distance_ly,
                }
                for star in stars
            ]

        # Search planets
        if "planet" in enabled_types:
            planet_service = PlanetService()
            all_planets = planet_service.get_all_planets()

            # Filter planets by name match
            matching_planets = [p for p in all_planets if query.lower() in p.name.lower()]

            results["planets"] = [
                {
                    "type": "planet",
                    "name": planet.name,
                    "planet_type": planet.planet_type,
                    "diameter_km": planet.diameter_km,
                    "orbital_period_days": planet.orbital_period_days,
                    "has_rings": planet.has_rings,
                    "num_moons": planet.num_moons,
                    "notes": planet.notes,
                }
                for planet in matching_planets[:max_results]
            ]

        # Count total results
        total = len(results["dsos"]) + len(results["stars"]) + len(results["planets"])

        return {
            "query": query,
            "total_results": total,
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error in unified search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching catalogs: {str(e)}")


@router.get("/catalog/search")
async def search_catalog(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by object name or catalog ID"),
    type: Optional[str] = Query(None, description="Filter by object type"),
    constellation: Optional[str] = Query(None, description="Filter by constellation"),
    max_magnitude: Optional[float] = Query(None, description="Maximum magnitude (fainter limit)"),
    visible_now: bool = Query(False, description="Only show targets visible now (altitude > 30°)"),
    sort_by: str = Query("name", description="Sort by: name, magnitude, type, or score"),
    use_scoring: bool = Query(
        False, description="Use comprehensive scoring algorithm (location, coverage, brightness)"
    ),
    page: int = Query(1, description="Page number (1-indexed)", ge=1),
    page_size: int = Query(20, description="Items per page", ge=1, le=100),
):
    """
    Search and filter catalog objects for discovery workflow.

    This endpoint is specifically designed for the catalog search interface,
    providing paginated results with search and filter capabilities.

    Args:
        search: Free text search (matches object name or catalog ID)
        type: Object type filter (galaxy, nebula, cluster, etc.)
        constellation: Constellation filter (3-letter abbreviation)
        max_magnitude: Maximum magnitude filter
        visible_now: Only show targets visible now (altitude > 30°)
        sort_by: Sort field (name, magnitude, type, or score)
        use_scoring: Use comprehensive scoring algorithm including location, coverage, brightness, size, and field rotation
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated catalog search results with optional scoring
    """
    try:
        import time
        from datetime import datetime, timedelta

        import pytz
        from sqlalchemy import func, or_

        from app.models.catalog_models import DSOCatalog
        from app.models.models import DSOTarget, Location
        from app.models.settings_models import ObservingLocation
        from app.services.ephemeris_service import EphemerisService

        # Create cache key from query parameters
        cache_key = (
            f"catalog:{search}:{type}:{constellation}:{max_magnitude}:{visible_now}:{sort_by}:{page}:{page_size}"
        )

        # Check cache (skip cache for visible_now since it changes with time)
        if not visible_now and cache_key in catalog_cache:
            cached_result, expiry = catalog_cache[cache_key]
            if time.time() < expiry:
                return cached_result
            else:
                # Remove expired entry
                del catalog_cache[cache_key]

        # Build query with filters (do NOT call .all() yet!)
        query = db.query(DSOCatalog)

        # Apply type filter
        if type:
            query = query.filter(DSOCatalog.object_type == type)

        # Apply constellation filter
        if constellation:
            query = query.filter(DSOCatalog.constellation == constellation)

        # Apply magnitude filter
        if max_magnitude:
            query = query.filter(DSOCatalog.magnitude <= max_magnitude)

        # Apply search filter using SQL ILIKE for case-insensitive search
        # If searching for specific object, check for exact match first
        exact_match_objects = []
        if search:
            import re as _re

            # If user types "M31", also try zero-padded "M031" to match common_name storage format
            _m = _re.match(r"^([A-Za-z]+)(\d+)$", search.strip(), _re.IGNORECASE)
            padded_search = f"{_m.group(1)}{_m.group(2).zfill(3)}" if _m else search

            # Check for exact matches (case-insensitive) - these bypass all filters
            exact_query = db.query(DSOCatalog).filter(
                or_(
                    DSOCatalog.common_name.ilike(search),
                    DSOCatalog.common_name.ilike(padded_search),
                    func.concat(DSOCatalog.catalog_name, DSOCatalog.catalog_number).ilike(search),
                )
            )
            exact_match_objects = exact_query.all()

            # Apply partial search filter for remaining results
            search_pattern = f"%{search}%"
            padded_pattern = f"%{padded_search}%"
            query = query.filter(
                or_(
                    DSOCatalog.common_name.ilike(search_pattern),
                    DSOCatalog.common_name.ilike(padded_pattern),
                    func.concat(DSOCatalog.catalog_name, DSOCatalog.catalog_number).ilike(search_pattern),
                )
            )

        # Apply sorting using SQL ORDER BY
        if sort_by == "magnitude":
            query = query.order_by(DSOCatalog.magnitude.asc().nullslast())
        elif sort_by == "type":
            query = query.order_by(DSOCatalog.object_type.asc())
        else:  # name (default)
            query = query.order_by(DSOCatalog.catalog_name.asc(), DSOCatalog.catalog_number.asc())

        # Initialize score details map (used when comprehensive scoring is enabled)
        score_details = {}

        # Handle visibility filtering
        if visible_now:
            # Optimization: Sort by brightness and size first (using DB indexes),
            # take top candidates, THEN calculate visibility for only those
            # This is much faster than calculating visibility for all results

            # Sort by magnitude (brightness) first to get best candidates
            query = query.order_by(DSOCatalog.magnitude.asc().nullslast())

            # Get top candidates for visibility checking
            # Check top 100 brightest to have good chance of finding visible ones
            # This is still fast (< 1 second) and much better than checking all results
            candidate_limit = max(100, page_size * 10)
            candidates = query.limit(candidate_limit).all()

            # Get default location for visibility calculations
            default_location_db = db.query(ObservingLocation).filter(ObservingLocation.is_default == True).first()

            # Create Location object for ephemeris calculations
            if default_location_db:
                location = Location(
                    name=default_location_db.name,
                    latitude=default_location_db.latitude,
                    longitude=default_location_db.longitude,
                    elevation=default_location_db.elevation,
                    timezone=default_location_db.timezone,
                )
            else:
                # Fall back to app settings default location
                from app.core import get_settings as _get_settings

                _settings = _get_settings()
                location = Location(
                    name=_settings.default_location_name,
                    latitude=_settings.default_lat,
                    longitude=_settings.default_lon,
                    elevation=_settings.default_elevation,
                    timezone=_settings.default_timezone,
                )

            # Initialize ephemeris service
            ephemeris = EphemerisService()
            current_time = datetime.now(pytz.timezone(location.timezone))

            # Check if sun is up - if so, calculate for tonight instead of now
            from skyfield.api import wgs84

            observer = ephemeris.earth + wgs84.latlon(
                location.latitude, location.longitude, elevation_m=location.elevation
            )
            t = ephemeris.ts.from_datetime(current_time.astimezone(pytz.UTC))
            sun_apparent = observer.at(t).observe(ephemeris.sun).apparent()
            sun_alt, _, _ = sun_apparent.altaz()

            # If sun is above -18° (before astronomical twilight), use tonight's observing time
            if sun_alt.degrees > -18.0:
                # Calculate tonight's astronomical twilight
                twilight_times = ephemeris.calculate_twilight_times(location, current_time)
                # Use astronomical twilight end (when deep sky observing starts)
                if "astronomical_twilight_end" in twilight_times:
                    observing_time = twilight_times["astronomical_twilight_end"]
                else:
                    # Fallback to 2 hours after sunset
                    observing_time = twilight_times.get("sunset", current_time) + timedelta(hours=2)
            else:
                # It's already dark, use current time
                observing_time = current_time

            # Filter candidates by visibility (altitude > 30°)
            # Calculate visibility score for final sorting
            visible_results = []  # List of tuples: (dso, visibility_score)

            # Use comprehensive scoring if requested
            if use_scoring or sort_by == "score":
                from app.models import ObservingConstraints
                from app.services.scheduler_service import SchedulerService
                from app.services.weather_service import WeatherService

                scheduler = SchedulerService()
                weather_service = WeatherService()
                constraints = ObservingConstraints()

                # Get weather forecast for scoring
                twilight_times = ephemeris.calculate_twilight_times(location, current_time)
                scoring_start = twilight_times.get("astronomical_twilight_end", observing_time)
                scoring_end = twilight_times.get("astronomical_twilight_start", observing_time + timedelta(hours=8))
                weather_forecasts = weather_service.get_forecast(location, scoring_start, scoring_end)

            for dso in candidates:
                # Create DSOTarget for ephemeris calculation
                # Use defaults for None values (99.0 for magnitude = very faint, 1.0 for size)
                target = DSOTarget(
                    catalog_id=f"{dso.catalog_name}{dso.catalog_number}",
                    name=dso.common_name or f"{dso.catalog_name} {dso.catalog_number}",
                    ra_hours=dso.ra_hours,
                    dec_degrees=dso.dec_degrees,
                    object_type=dso.object_type,
                    magnitude=dso.magnitude if dso.magnitude is not None else 99.0,
                    size_arcmin=dso.size_major_arcmin if dso.size_major_arcmin is not None else 1.0,
                )

                # Calculate altitude at observing time (current time or tonight's twilight)
                try:
                    altitude, _ = ephemeris.calculate_position(target, location, observing_time)
                    if altitude > 30.0:  # Minimum altitude threshold
                        if use_scoring or sort_by == "score":
                            # Use comprehensive scheduler scoring
                            duration = scheduler._calculate_visibility_duration(
                                target, location, scoring_start, scoring_end, constraints
                            )
                            weather_score = scheduler._get_weather_score_for_time(observing_time, weather_forecasts)
                            score_data = scheduler._score_target(
                                target, location, observing_time, duration, constraints, weather_score
                            )
                            # Store score as tuple: (dso, score, detailed_scores)
                            # Higher score is better, so negate for sorting (we want highest first)
                            visible_results.append((dso, -score_data.total_score, score_data))
                        else:
                            # Calculate simple visibility score (lower is better):
                            # - Brighter objects (lower magnitude) are better
                            # - Bigger objects are better (subtract size bonus)
                            # - Higher altitude is better (subtract altitude bonus)
                            magnitude = dso.magnitude if dso.magnitude is not None else 99.0
                            size = dso.size_major_arcmin if dso.size_major_arcmin is not None else 0.0
                            visibility_score = magnitude - (size / 10.0) - (altitude / 20.0)
                            visible_results.append((dso, visibility_score, None))
                except Exception:
                    # Skip targets that fail calculation
                    continue

            # Sort by visibility score
            # (for simple score: lower is better; for comprehensive score: already negated so lower means higher score)
            visible_results.sort(key=lambda x: x[1])

            # Extract DSO objects and detailed scores
            visible_dsos = []
            score_details = {}  # Map catalog_id to score details
            for dso, _, score_data in visible_results:
                visible_dsos.append(dso)
                if score_data:  # If comprehensive scoring was used
                    catalog_id = f"{dso.catalog_name}{dso.catalog_number}"
                    score_details[catalog_id] = {
                        "total_score": score_data.total_score,
                        "visibility_score": score_data.visibility_score,
                        "weather_score": score_data.weather_score,
                        "object_score": score_data.object_score,
                    }

            # Prepend exact matches even if not visible (user specifically searched for them)
            if exact_match_objects:
                exact_ids = {obj.id for obj in exact_match_objects}
                visible_dsos = [obj for obj in visible_dsos if obj.id not in exact_ids]
                visible_dsos = exact_match_objects + visible_dsos

            # Use filtered results for pagination
            total = len(visible_dsos)
            offset = (page - 1) * page_size
            paginated_results = visible_dsos[offset : offset + page_size]
        else:
            # Get total count BEFORE pagination (efficient - just counts, doesn't fetch rows)
            total = query.count()

            # Apply pagination using SQL LIMIT/OFFSET
            offset = (page - 1) * page_size
            paginated_results = query.limit(page_size).offset(offset).all()

        # Prepend exact matches to results (they bypass all filters)
        if exact_match_objects:
            # Remove exact matches from paginated_results to avoid duplicates
            exact_ids = {obj.id for obj in exact_match_objects}
            paginated_results = [obj for obj in paginated_results if obj.id not in exact_ids]
            # Add exact matches at the beginning
            paginated_results = exact_match_objects + paginated_results
            # Limit to page_size
            paginated_results = paginated_results[:page_size]

        # Convert ONLY the paginated results to response format
        catalog_service = CatalogService(db)
        items = []
        for dso in paginated_results:
            target = catalog_service._db_row_to_target(dso)
            # Get constellation details
            constellation_details = catalog_service._get_constellation_details(dso.constellation)

            item = {
                "id": target.catalog_id,
                "name": target.name,
                "common_name": dso.common_name,  # Include common_name from database
                "type": target.object_type,
                "constellation": dso.constellation,
                "constellation_full": (
                    constellation_details["full_name"] if constellation_details else dso.constellation
                ),
                "constellation_common": constellation_details["common_name"] if constellation_details else None,
                "magnitude": target.magnitude,
                "ra": target.ra_hours * 15,  # Convert hours to degrees
                "dec": target.dec_degrees,
                "size": f"{target.size_arcmin:.1f}'" if target.size_arcmin and target.size_arcmin > 1 else None,
            }

            # Add score details if comprehensive scoring was used
            if visible_now and (use_scoring or sort_by == "score"):
                catalog_id = target.catalog_id
                if catalog_id in score_details:
                    item["score"] = score_details[catalog_id]

            items.append(item)

        result = {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

        # Cache the result
        catalog_cache[cache_key] = (result, time.time() + CATALOG_CACHE_TTL)

        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error searching catalog: {str(e)}")


@router.get("/catalog/stats")
async def get_catalog_stats(db: Session = Depends(get_db)):
    """
    Get statistics about the DSO catalog.

    Returns summary information about the catalog including:
    - Total number of objects
    - Count by object type
    - Count by catalog (Messier, NGC, IC, Caldwell)
    - Magnitude distribution

    Returns:
        Catalog statistics dictionary
    """
    try:
        from sqlalchemy import case, func

        from app.models.catalog_models import DSOCatalog

        # Total objects
        total = db.query(func.count(DSOCatalog.id)).scalar()

        # By object type
        by_type_query = (
            db.query(DSOCatalog.object_type, func.count(DSOCatalog.id))
            .group_by(DSOCatalog.object_type)
            .order_by(func.count(DSOCatalog.id).desc())
            .all()
        )
        by_type = {row[0]: row[1] for row in by_type_query}

        # By catalog
        by_catalog_query = (
            db.query(DSOCatalog.catalog_name, func.count(DSOCatalog.id))
            .group_by(DSOCatalog.catalog_name)
            .order_by(func.count(DSOCatalog.id).desc())
            .all()
        )
        by_catalog = {row[0]: row[1] for row in by_catalog_query}

        # Count Caldwell objects
        caldwell_count = db.query(func.count(DSOCatalog.id)).filter(DSOCatalog.caldwell_number.isnot(None)).scalar()
        by_catalog["Caldwell"] = caldwell_count

        # Count Messier objects (stored with common_name starting with M)
        messier_count = db.query(func.count(DSOCatalog.id)).filter(DSOCatalog.common_name.like("M%")).scalar()
        by_catalog["Messier"] = messier_count

        # Magnitude ranges
        mag_query = (
            db.query(
                func.count(case((DSOCatalog.magnitude <= 5, 1))).label("very_bright"),
                func.count(case(((DSOCatalog.magnitude > 5) & (DSOCatalog.magnitude <= 10), 1))).label("bright"),
                func.count(case(((DSOCatalog.magnitude > 10) & (DSOCatalog.magnitude <= 15), 1))).label("moderate"),
                func.count(case((DSOCatalog.magnitude > 15, 1))).label("faint"),
            )
            .filter(DSOCatalog.magnitude.isnot(None), DSOCatalog.magnitude < 99)
            .one()
        )

        magnitude_ranges = {
            "<=5.0 (Very Bright)": mag_query.very_bright,
            "5.0-10.0 (Bright)": mag_query.bright,
            "10.0-15.0 (Moderate)": mag_query.moderate,
            ">15.0 (Faint)": mag_query.faint,
        }

        return {"total_objects": total, "by_type": by_type, "by_catalog": by_catalog, "by_magnitude": magnitude_ranges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching catalog stats: {str(e)}")


@router.post("/twilight")
async def calculate_twilight(
    location: Location, date: str = Query(..., description="ISO date (YYYY-MM-DD)"), db: Session = Depends(get_db)
):
    """
    Calculate twilight times for a specific location and date.

    Args:
        location: Observer location
        date: ISO date string
        db: Database session

    Returns:
        Dictionary of twilight times
    """
    try:
        planner = PlannerService(db)
        twilight_times = planner.calculate_twilight(location, date)
        return twilight_times
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating twilight: {str(e)}")


@router.post("/export")
async def export_plan(
    plan: ObservingPlan,
    format: str = Query(..., description="Export format: json, seestar_plan, seestar_alp, text, csv"),
    db: Session = Depends(get_db),
):
    """
    Export an observing plan in various formats.

    Args:
        plan: Observing plan to export
        format: Export format type
        db: Database session

    Returns:
        Exported plan data
    """
    try:
        planner = PlannerService(db)
        exported_data = planner.exporter.export(plan, format)
        return ExportFormat(format_type=format, data=exported_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting plan: {str(e)}")


@router.post("/share")
async def share_plan(plan: ObservingPlan):
    """
    Save a plan and return a shareable ID.

    Args:
        plan: Observing plan to share

    Returns:
        Shareable plan ID and URL
    """
    try:
        # Generate a short, unique ID
        plan_id = str(uuid.uuid4())[:8]

        # Evict expired entries on each write (amortised cleanup)
        now = _time.time()
        expired = [k for k, (_, exp) in shared_plans.items() if now > exp]
        for k in expired:
            del shared_plans[k]

        # Ensure uniqueness
        while plan_id in shared_plans:
            plan_id = str(uuid.uuid4())[:8]

        # Store with expiry timestamp
        shared_plans[plan_id] = (plan, now + SHARED_PLAN_TTL)

        return {
            "plan_id": plan_id,
            "share_url": f"/plan/{plan_id}",
            "api_url": f"/api/shared-plans/{plan_id}",
            "message": "Plan saved successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sharing plan: {str(e)}")


@router.get("/shared-plans/{plan_id}")
async def get_shared_plan(plan_id: str):
    """
    Retrieve a shared plan by ID (temporary in-memory storage).

    This is for sharing plans via short-lived links, not for persistent storage.
    Use /plans endpoints for persistent plan storage.

    Args:
        plan_id: Shareable plan ID

    Returns:
        Observing plan
    """
    entry = shared_plans.get(plan_id)
    if entry is None or _time.time() > entry[1]:
        shared_plans.pop(plan_id, None)
        raise HTTPException(status_code=404, detail="Plan not found or expired")

    return entry[0]


@router.get("/sky-quality/{lat}/{lon}")
async def get_sky_quality(lat: float, lon: float, location_name: str = Query("Unknown Location")):
    """
    Get sky quality and light pollution data for a location.

    This endpoint provides comprehensive information about sky quality including:
    - Bortle scale classification (1-9)
    - Sky Quality Meter (SQM) estimate
    - Light pollution level
    - Observing recommendations
    - Suitable target types
    - Naked eye limiting magnitude

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        location_name: Optional location name

    Returns:
        Complete sky quality information
    """
    try:
        # Create location object
        location = Location(
            name=location_name,
            latitude=lat,
            longitude=lon,
            elevation=0.0,  # Not needed for light pollution
            timezone="UTC",  # Not needed for light pollution
        )

        # Get sky quality data
        service = LightPollutionService()
        sky_quality = service.get_sky_quality(location)

        # Get observing recommendations
        recommendations = service.get_observing_recommendations(sky_quality)

        # Return combined data
        return {
            "location": {"name": location_name, "latitude": lat, "longitude": lon},
            "bortle_class": sky_quality.bortle_class,
            "bortle_name": sky_quality.bortle_name,
            "sqm_estimate": sky_quality.sqm_estimate,
            "light_pollution_level": sky_quality.light_pollution_level,
            "visibility_description": sky_quality.visibility_description,
            "suitable_for": sky_quality.suitable_for,
            "limiting_magnitude": sky_quality.limiting_magnitude,
            "milky_way_visibility": sky_quality.milky_way_visibility,
            "data_source": sky_quality.light_pollution_source,
            "recommendations": recommendations,
        }

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching sky quality: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Status information
    """
    from app.api.telescope import seestar_client as _seestar_client

    return {
        "status": "healthy",
        "service": "astronomus-api",
        "version": "1.0.0",
        "telescope_connected": _seestar_client is not None and _seestar_client.connected,
    }


@router.get("/wishlist/defaults")
async def get_wishlist_defaults():
    """
    Get default solar system objects for wish list.

    Returns 19 solar system objects:
    - 8 planets including Pluto (Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto)
    - Moon
    - Sun
    - Jupiter's Galilean moons (Io, Europa, Ganymede, Callisto)
    - Saturn's major moons (Titan, Rhea, Tethys, Dione, Enceladus)

    Returns:
        List of default targets with name and type
    """
    return [
        # Planets
        {"name": "Mercury", "type": "planet"},
        {"name": "Venus", "type": "planet"},
        {"name": "Mars", "type": "planet"},
        {"name": "Jupiter", "type": "planet"},
        {"name": "Saturn", "type": "planet"},
        {"name": "Uranus", "type": "planet"},
        {"name": "Neptune", "type": "planet"},
        {"name": "Pluto", "type": "planet"},
        # Earth's Moon
        {"name": "Moon", "type": "moon"},
        # Sun
        {"name": "Sun", "type": "star"},
        # Jupiter's Galilean moons
        {"name": "Io", "type": "moon"},
        {"name": "Europa", "type": "moon"},
        {"name": "Ganymede", "type": "moon"},
        {"name": "Callisto", "type": "moon"},
        # Saturn's major moons
        {"name": "Titan", "type": "moon"},
        {"name": "Rhea", "type": "moon"},
        {"name": "Tethys", "type": "moon"},
        {"name": "Dione", "type": "moon"},
        {"name": "Enceladus", "type": "moon"},
    ]


@router.get("/images/previews/{filename}")
async def get_preview_image(filename: str):
    """
    Serve cached preview image.

    Args:
        filename: Image filename

    Returns:
        Image file
    """
    try:
        cache_dir = Path(os.getenv("IMAGE_CACHE_DIR", "/app/data/previews"))
        image_path = cache_dir / filename

        # Sanitize path to prevent directory traversal
        image_path = image_path.resolve()
        if not str(image_path).startswith(str(cache_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")

        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")

        return FileResponse(
            path=str(image_path),
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=2592000"},  # Cache for 30 days
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get("/images/targets/{sanitized_catalog_id}")
async def get_target_preview(sanitized_catalog_id: str, db: Session = Depends(get_db)):
    """
    Fetch or serve preview image for a target by catalog ID.
    This endpoint fetches images on-demand to avoid blocking plan generation.

    Args:
        sanitized_catalog_id: Sanitized catalog ID (spaces/slashes replaced with underscores)
        db: Database session

    Returns:
        Image file (JPEG)
    """
    try:
        from app.services.catalog_service import CatalogService
        from app.services.image_preview_service import ImagePreviewService

        # Parse catalog ID to find target in database
        # Catalog IDs are like: M31, NGC224, IC434, C80
        catalog_service = CatalogService(db)

        target = None

        # Try to parse catalog ID format
        import logging
        import re

        logger = logging.getLogger(__name__)

        # Match patterns like M31, NGC224, IC434, C80
        match = re.match(r"([A-Z]+)(\d+)", sanitized_catalog_id)
        if match:
            catalog_name = match.group(1)
            catalog_number = int(match.group(2))

            logger.info(f"Looking up target: {catalog_name}{catalog_number}")

            # Query database for this specific catalog entry
            from app.models.catalog_models import DSOCatalog

            # Handle special cases
            if catalog_name == "M":
                # Messier objects - find by common_name starting with M
                dso = db.query(DSOCatalog).filter(DSOCatalog.common_name.like(f"M%{catalog_number:03d}")).first()
            elif catalog_name == "C":
                # Caldwell objects - find by caldwell_number
                dso = db.query(DSOCatalog).filter(DSOCatalog.caldwell_number == catalog_number).first()
            else:
                # NGC, IC, etc. - find by catalog_name and catalog_number
                dso = (
                    db.query(DSOCatalog)
                    .filter(DSOCatalog.catalog_name == catalog_name, DSOCatalog.catalog_number == catalog_number)
                    .first()
                )
                logger.info(f"DSO query result for {catalog_name}{catalog_number}: {dso is not None}")

            if dso:
                target = catalog_service._db_row_to_target(dso)
                logger.info(f"Successfully created target for {sanitized_catalog_id}")
        else:
            logger.warning(f"Failed to parse catalog ID: {sanitized_catalog_id}")

        if not target:
            logger.warning(f"Target not found: {sanitized_catalog_id}")
            raise HTTPException(status_code=404, detail=f"Target not found: {sanitized_catalog_id}")

        # Use image preview service to get or fetch image
        image_service = ImagePreviewService(db=db)
        cache_filename = f"{sanitized_catalog_id}.jpg"
        cache_dir = Path(os.getenv("IMAGE_CACHE_DIR", "/app/data/previews"))

        # Ensure cache directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_path = cache_dir / cache_filename

        # Check cache first
        if cache_path.exists():
            return FileResponse(
                path=str(cache_path),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=2592000"},
            )

        # Fetch from multi-source service (this will cache it)
        image_data = image_service._fetch_from_skyview(target)
        if image_data:
            cache_path.write_bytes(image_data)
            return FileResponse(
                path=str(cache_path),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=2592000"},
            )

        # If fetch failed, return 404
        raise HTTPException(status_code=404, detail="Image not available")

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching target image: {str(e)}")


def _compute_solar_system_objects_sync(lat: float, lon: float) -> list:
    """Fast sync computation of solar system objects — call via run_in_executor.

    Bypasses compute_visibility (which sweeps 24 h of rise/set times) and
    uses a single shared AltAz frame for all bodies instead.
    """
    # Prevent network calls to IERS servers that can block or fail
    try:
        from astropy.utils.iers import conf as iers_conf

        iers_conf.auto_download = False
        iers_conf.auto_max_age = None  # don't raise on stale data
    except Exception:
        pass

    from astropy import units as u
    from astropy.coordinates import AltAz, EarthLocation, get_body, get_sun
    from astropy.time import Time

    from app.services.planet_service import PlanetService

    planet_service = PlanetService()
    now_utc = datetime.utcnow()
    t = Time(now_utc)

    earth_loc = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
    altaz_frame = AltAz(obstime=t, location=earth_loc)

    MAIN_BODIES = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Moon", "Sun"]
    MOON_PARENTS = {
        "Io": "Jupiter",
        "Europa": "Jupiter",
        "Ganymede": "Jupiter",
        "Callisto": "Jupiter",
        "Titan": "Saturn",
        "Rhea": "Saturn",
        "Tethys": "Saturn",
        "Dione": "Saturn",
        "Enceladus": "Saturn",
    }

    results = []
    parent_visible: dict = {}

    for name in MAIN_BODIES:
        try:
            eph = planet_service.compute_ephemeris(name, now_utc)
            # Single AltAz transform — no 24-hour rise/set sweep
            body_coord = get_sun(t) if name == "Sun" else get_body(name.lower(), t)
            altaz = body_coord.transform_to(altaz_frame)
            altitude_deg = float(altaz.alt.degree)
            is_visible = altitude_deg > 0
            parent_visible[name] = is_visible
            obj_type = "moon" if name == "Moon" else ("star" if name == "Sun" else "planet")
            planet = planet_service.get_planet_by_name(name)
            results.append(
                {
                    "name": name,
                    "type": obj_type,
                    "magnitude": round(eph.magnitude, 1),
                    "angular_diameter_arcsec": round(eph.angular_diameter_arcsec, 1),
                    "altitude_deg": round(altitude_deg, 1),
                    "is_visible": is_visible,
                    "constellation": eph.constellation,
                    "notes": planet.notes if planet else None,
                }
            )
        except Exception as exc:
            logger.warning("solar-system: failed to compute %s: %s", name, exc)
            obj_type = "moon" if name == "Moon" else ("star" if name == "Sun" else "planet")
            results.append({"name": name, "type": obj_type, "is_visible": False})

    for moon, parent in MOON_PARENTS.items():
        results.append(
            {
                "name": moon,
                "type": "moon",
                "parent": parent,
                "is_visible": parent_visible.get(parent, False),
                "magnitude": None,
                "altitude_deg": None,
                "angular_diameter_arcsec": None,
                "constellation": None,
                "notes": None,
            }
        )

    return results


@router.get("/solar-system/objects")
async def get_solar_system_objects(lat: Optional[float] = Query(None), lon: Optional[float] = Query(None)):
    """All solar system targets with current ephemeris, computed in a thread pool."""
    import asyncio

    loop = asyncio.get_running_loop()
    objects = await loop.run_in_executor(None, _compute_solar_system_objects_sync, lat or 0.0, lon or 0.0)
    return {"objects": objects}
