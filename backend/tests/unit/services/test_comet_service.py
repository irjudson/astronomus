"""Tests for comet service.

These tests require database services (PostgreSQL) to run.
They are marked as integration tests and skipped on macOS CI.
"""

from datetime import datetime

import pytest

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

from app.models import CometTarget, Location, OrbitalElements
from app.services.comet_service import CometService


@pytest.fixture
def comet_service(override_get_db):
    """Create comet service instance with isolated test database."""
    return CometService(override_get_db)


@pytest.fixture
def test_comet():
    """Create a test comet (NEOWISE)."""
    return CometTarget(
        designation="C/2020 F3",
        name="NEOWISE",
        orbital_elements=OrbitalElements(
            epoch_jd=2459000.5,
            perihelion_distance_au=0.29,
            eccentricity=0.999,
            inclination_deg=128.9,
            arg_perihelion_deg=37.3,
            ascending_node_deg=61.0,
            perihelion_time_jd=2459034.0,
        ),
        absolute_magnitude=3.0,
        magnitude_slope=4.0,
        current_magnitude=7.0,
        comet_type="long-period",
        activity_status="active",
        discovery_date=None,
        data_source="Test",
        notes="Test comet",
    )


@pytest.fixture
def test_location():
    """Create a test location."""
    return Location(
        latitude=45.9183, longitude=-111.5433, elevation_meters=1234, timezone="America/Denver", name="Three Forks, MT"
    )


def test_add_comet(comet_service, test_comet, override_get_db):
    """Test adding a comet to the catalog."""
    comet_id = comet_service.add_comet(test_comet)
    assert comet_id is not None
    assert comet_id > 0


def test_get_comet_by_designation(comet_service, test_comet, override_get_db):
    """Test retrieving a comet by designation."""
    # Add comet first
    comet_service.add_comet(test_comet)

    # Retrieve it
    retrieved = comet_service.get_comet_by_designation("C/2020 F3")
    assert retrieved is not None
    assert retrieved.designation == "C/2020 F3"
    assert retrieved.name == "NEOWISE"
    assert retrieved.comet_type == "long-period"


def test_get_all_comets(comet_service, test_comet, override_get_db):
    """Test retrieving all comets."""
    # Add comet
    comet_service.add_comet(test_comet)

    # Retrieve all
    comets = comet_service.get_all_comets(limit=10)
    assert len(comets) > 0
    assert any(c.designation == "C/2020 F3" for c in comets)


def test_compute_ephemeris(comet_service, test_comet):
    """Test computing ephemeris for a comet."""
    time_utc = datetime(2020, 7, 15, 0, 0, 0)
    ephemeris = comet_service.compute_ephemeris(test_comet, time_utc)

    assert ephemeris is not None
    assert ephemeris.designation == "C/2020 F3"
    assert ephemeris.ra_hours is not None
    assert ephemeris.dec_degrees is not None
    assert ephemeris.helio_distance_au > 0
    assert ephemeris.geo_distance_au > 0
    assert ephemeris.magnitude is not None


def test_compute_visibility(comet_service, test_comet, test_location):
    """Test computing visibility for a comet."""
    time_utc = datetime(2020, 7, 15, 3, 0, 0)  # 9 PM local time
    visibility = comet_service.compute_visibility(test_comet, test_location, time_utc)

    assert visibility is not None
    assert visibility.comet.designation == "C/2020 F3"
    assert visibility.altitude_deg is not None
    assert visibility.azimuth_deg is not None
    assert isinstance(visibility.is_visible, bool)
    assert isinstance(visibility.is_dark_enough, bool)


def test_get_visible_comets(comet_service, test_comet, test_location, override_get_db):
    """Test getting all visible comets."""
    # Add comet
    comet_service.add_comet(test_comet)

    time_utc = datetime(2020, 7, 15, 3, 0, 0)
    visible = comet_service.get_visible_comets(
        location=test_location, time_utc=time_utc, min_altitude=0.0, max_magnitude=15.0
    )

    assert isinstance(visible, list)
    # Visibility depends on position and time, so just check structure
    for vis in visible:
        assert vis.comet is not None
        assert vis.ephemeris is not None
        assert vis.altitude_deg is not None


def test_upsert_comet_updates_existing(comet_service, test_comet, override_get_db):
    """Test upsert updates an existing comet."""
    comet_id_1, was_created = comet_service.upsert_comet(test_comet)
    assert was_created is True

    # Upsert again — should update
    comet_id_2, was_created_2 = comet_service.upsert_comet(test_comet)
    assert was_created_2 is False
    assert comet_id_1 == comet_id_2


def test_upsert_comet_creates_new_if_missing(comet_service, override_get_db):
    """Test upsert creates a new comet when designation does not exist."""
    new_comet = CometTarget(
        designation="C/2099 Z1",
        name="FutureComet",
        orbital_elements=OrbitalElements(
            epoch_jd=2460000.5,
            perihelion_distance_au=1.0,
            eccentricity=0.95,
            inclination_deg=45.0,
            arg_perihelion_deg=100.0,
            ascending_node_deg=200.0,
            perihelion_time_jd=2460050.0,
        ),
        absolute_magnitude=6.0,
        magnitude_slope=3.0,
        current_magnitude=9.0,
        comet_type="short-period",
        activity_status="active",
        data_source="Test",
    )
    comet_id, was_created = comet_service.upsert_comet(new_comet)
    assert was_created is True
    assert comet_id > 0


def test_get_comet_by_designation_not_found(comet_service):
    """Test returning None when designation not in catalog."""
    result = comet_service.get_comet_by_designation("NOTEXIST/0000 X0")
    assert result is None


def test_get_all_comets_with_limit(comet_service, test_comet, override_get_db):
    """Test get_all_comets respects limit and offset."""
    comet_service.add_comet(test_comet)
    results = comet_service.get_all_comets(limit=1, offset=0)
    assert isinstance(results, list)
    assert len(results) <= 1


def test_get_visible_comets_filters_faint(comet_service, override_get_db):
    """Test get_visible_comets skips comets fainter than max_magnitude."""
    faint_comet = CometTarget(
        designation="C/2000 F1",
        name="FaintComet",
        orbital_elements=OrbitalElements(
            epoch_jd=2459000.5,
            perihelion_distance_au=2.0,
            eccentricity=0.9,
            inclination_deg=10.0,
            arg_perihelion_deg=30.0,
            ascending_node_deg=60.0,
            perihelion_time_jd=2459100.0,
        ),
        absolute_magnitude=5.0,
        magnitude_slope=4.0,
        current_magnitude=15.0,  # too faint
        comet_type="short-period",
        activity_status="active",
        data_source="Test",
    )
    comet_service.add_comet(faint_comet)
    location = Location(latitude=45.0, longitude=-111.0, elevation_meters=1000, timezone="America/Denver", name="Test")
    visible = comet_service.get_visible_comets(
        location=location,
        time_utc=datetime(2020, 7, 15, 3, 0, 0),
        max_magnitude=12.0,
    )
    # faint_comet (magnitude 15) should be filtered out
    designations = [v.comet.designation for v in visible]
    assert "C/2000 F1" not in designations


def test_compute_ephemeris_hyperbolic_orbit(comet_service):
    """Test ephemeris computation with hyperbolic orbit (e > 1)."""
    hyp_comet = CometTarget(
        designation="C/HYPER",
        name="HyperbolicComet",
        orbital_elements=OrbitalElements(
            epoch_jd=2459000.5,
            perihelion_distance_au=1.0,
            eccentricity=1.1,  # hyperbolic
            inclination_deg=30.0,
            arg_perihelion_deg=45.0,
            ascending_node_deg=90.0,
            perihelion_time_jd=2459000.0,
        ),
        absolute_magnitude=None,
        magnitude_slope=4.0,
        current_magnitude=None,
        comet_type="hyperbolic",
        activity_status="active",
        data_source="Test",
    )
    eph = comet_service.compute_ephemeris(hyp_comet, datetime(2020, 6, 1, 0, 0, 0))
    assert eph is not None
    assert eph.designation == "C/HYPER"
    assert eph.magnitude is None  # no absolute_magnitude → None


def test_orbital_elements_validation():
    """Test that orbital elements are properly validated."""
    # Test with valid eccentricity
    oe = OrbitalElements(
        epoch_jd=2459000.5,
        perihelion_distance_au=1.0,
        eccentricity=0.5,  # Elliptical
        inclination_deg=10.0,
        arg_perihelion_deg=45.0,
        ascending_node_deg=90.0,
        perihelion_time_jd=2459000.0,
    )
    assert oe.eccentricity < 1.0

    # Test with hyperbolic orbit
    oe_hyp = OrbitalElements(
        epoch_jd=2459000.5,
        perihelion_distance_au=1.0,
        eccentricity=1.1,  # Hyperbolic
        inclination_deg=10.0,
        arg_perihelion_deg=45.0,
        ascending_node_deg=90.0,
        perihelion_time_jd=2459000.0,
    )
    assert oe_hyp.eccentricity > 1.0


def test_comet_magnitude_calculation(comet_service):
    """Test that magnitude calculation works correctly."""
    # Create a comet with known magnitude parameters
    comet = CometTarget(
        designation="TEST",
        name="Test Comet",
        orbital_elements=OrbitalElements(
            epoch_jd=2459000.5,
            perihelion_distance_au=1.0,
            eccentricity=0.5,
            inclination_deg=10.0,
            arg_perihelion_deg=45.0,
            ascending_node_deg=90.0,
            perihelion_time_jd=2459000.0,
        ),
        absolute_magnitude=5.0,
        magnitude_slope=4.0,
        current_magnitude=None,
        comet_type="short-period",
        activity_status="active",
        data_source="Test",
    )

    # Compute ephemeris
    time_utc = datetime(2020, 1, 1, 0, 0, 0)
    ephemeris = comet_service.compute_ephemeris(comet, time_utc)

    # Check that magnitude was calculated
    assert ephemeris.magnitude is not None
    # Magnitude should be reasonable (not NaN or extreme values)
    assert -5.0 < ephemeris.magnitude < 30.0
