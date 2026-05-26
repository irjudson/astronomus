"""Tests for planetary ephemeris service."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest


def _make_mock_eph():
    """Return a mock ephemeris object that supports body lookup."""
    bodies = ["sun", "moon", "mercury", "venus", "mars",
              "jupiter barycenter", "saturn barycenter",
              "uranus barycenter", "neptune barycenter", "earth"]

    mock_eph = MagicMock()

    def getitem(key):
        body = MagicMock(name=key)
        return body

    mock_eph.__getitem__ = Mock(side_effect=getitem)
    return mock_eph


def _make_astrometric_mock(alt_deg=45.0, az_deg=180.0, ra_hours=6.0, dec_deg=20.0, dist_au=1.0):
    """Return a mock astrometric object with the given position values."""
    mock_ra = MagicMock()
    mock_ra.hours = ra_hours
    mock_dec = MagicMock()
    mock_dec.degrees = dec_deg
    mock_dist = MagicMock()
    mock_dist.au = dist_au

    mock_alt = MagicMock()
    mock_alt.degrees = alt_deg
    mock_az = MagicMock()
    mock_az.degrees = az_deg

    mock_apparent = MagicMock()
    mock_apparent.altaz.return_value = (mock_alt, mock_az, mock_dist)
    mock_apparent.magnitude.return_value = -4.5

    mock_sep = MagicMock()
    mock_sep.degrees = 90.0
    mock_apparent.separation_from.return_value = mock_sep

    mock_astrometric = MagicMock()
    mock_astrometric.radec.return_value = (mock_ra, mock_dec, mock_dist)
    mock_astrometric.apparent.return_value = mock_apparent

    return mock_astrometric


def _patch_load(mock_eph=None):
    """Context-manager patch for skyfield load and timescale."""
    if mock_eph is None:
        mock_eph = _make_mock_eph()

    mock_ts = MagicMock()
    mock_t = MagicMock()
    mock_ts.from_datetime.return_value = mock_t

    mock_load_fn = MagicMock(return_value=mock_eph)
    mock_load_fn.timescale.return_value = mock_ts

    return mock_load_fn, mock_eph, mock_ts, mock_t


class TestPlanetaryEphemerisInit:

    @patch("app.services.planetary_ephemeris.load")
    def test_init_loads_de421(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_load.return_value = mock_eph
        mock_load.timescale = Mock(return_value=MagicMock())

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()

        mock_load.assert_called_with("de421.bsp")
        assert svc.eph is not None

    @patch("app.services.planetary_ephemeris.load")
    def test_all_nine_bodies_defined(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_load.return_value = mock_eph
        mock_load.timescale = Mock(return_value=MagicMock())

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()

        expected = {"sun", "moon", "mercury", "venus", "mars",
                    "jupiter", "saturn", "uranus", "neptune"}
        assert expected == set(svc.bodies.keys())


class TestGetPosition:

    @patch("app.services.planetary_ephemeris.load")
    def test_returns_dict_with_required_keys(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_t = MagicMock()
        mock_ts.from_datetime.return_value = mock_t
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        astrometric = _make_astrometric_mock()
        mock_observer = MagicMock()
        mock_observer.at.return_value.observe.return_value = astrometric

        # Patch the earth + Topos addition to return mock_observer
        earth = MagicMock()
        earth.__add__ = Mock(return_value=mock_observer)
        mock_eph.__getitem__ = Mock(return_value=earth)

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()
        svc.ts = mock_ts
        svc.bodies["mars"] = MagicMock()

        # Patch Topos to avoid real computation
        with patch("app.services.planetary_ephemeris.Topos", return_value=MagicMock()):
            result = svc.get_position("mars", 45.0, -111.0, 1000.0,
                                      time=datetime(2025, 1, 15, 22, 0, tzinfo=timezone.utc))

        required_keys = {"name", "ra_hours", "dec_degrees", "altitude", "azimuth", "distance_au", "visible"}
        assert required_keys.issubset(set(result.keys()))

    @patch("app.services.planetary_ephemeris.load")
    def test_raises_for_unknown_body(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()

        with pytest.raises(ValueError, match="Unknown body"):
            svc.get_position("pluto", 45.0, -111.0)

    @patch("app.services.planetary_ephemeris.load")
    def test_visible_true_when_altitude_positive(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_t = MagicMock()
        mock_ts.from_datetime.return_value = mock_t
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        astrometric = _make_astrometric_mock(alt_deg=30.0)
        mock_observer = MagicMock()
        mock_observer.at.return_value.observe.return_value = astrometric

        earth = MagicMock()
        earth.__add__ = Mock(return_value=mock_observer)
        mock_eph.__getitem__ = Mock(return_value=earth)

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()
        svc.ts = mock_ts
        svc.bodies["venus"] = MagicMock()

        with patch("app.services.planetary_ephemeris.Topos", return_value=MagicMock()):
            result = svc.get_position("venus", 45.0, -111.0,
                                      time=datetime(2025, 1, 15, 22, 0, tzinfo=timezone.utc))

        assert result["visible"] is True

    @patch("app.services.planetary_ephemeris.load")
    def test_visible_false_when_altitude_negative(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_t = MagicMock()
        mock_ts.from_datetime.return_value = mock_t
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        astrometric = _make_astrometric_mock(alt_deg=-10.0)
        mock_observer = MagicMock()
        mock_observer.at.return_value.observe.return_value = astrometric

        earth = MagicMock()
        earth.__add__ = Mock(return_value=mock_observer)
        mock_eph.__getitem__ = Mock(return_value=earth)

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()
        svc.ts = mock_ts
        svc.bodies["mercury"] = MagicMock()

        with patch("app.services.planetary_ephemeris.Topos", return_value=MagicMock()):
            result = svc.get_position("mercury", 45.0, -111.0,
                                      time=datetime(2025, 1, 15, 22, 0, tzinfo=timezone.utc))

        assert result["visible"] is False

    @patch("app.services.planetary_ephemeris.load")
    def test_defaults_time_to_now_when_none(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_t = MagicMock()
        mock_ts.from_datetime.return_value = mock_t
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        astrometric = _make_astrometric_mock()
        mock_observer = MagicMock()
        mock_observer.at.return_value.observe.return_value = astrometric

        earth = MagicMock()
        earth.__add__ = Mock(return_value=mock_observer)
        mock_eph.__getitem__ = Mock(return_value=earth)

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()
        svc.ts = mock_ts
        svc.bodies["saturn"] = MagicMock()

        with patch("app.services.planetary_ephemeris.Topos", return_value=MagicMock()):
            result = svc.get_position("saturn", 45.0, -111.0, time=None)

        assert "altitude" in result

    @patch("app.services.planetary_ephemeris.load")
    def test_moon_includes_phase_data(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_t = MagicMock()
        mock_ts.from_datetime.return_value = mock_t
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        astrometric = _make_astrometric_mock(alt_deg=45.0)
        mock_observer = MagicMock()
        mock_observer.at.return_value.observe.return_value = astrometric

        earth = MagicMock()
        earth.__add__ = Mock(return_value=mock_observer)
        mock_eph.__getitem__ = Mock(return_value=earth)

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()
        svc.ts = mock_ts
        svc.bodies["moon"] = MagicMock()
        svc.bodies["sun"] = MagicMock()

        with patch("app.services.planetary_ephemeris.Topos", return_value=MagicMock()):
            result = svc.get_position("moon", 45.0, -111.0,
                                      time=datetime(2025, 1, 15, 22, 0, tzinfo=timezone.utc))

        assert "phase" in result
        assert "illumination" in result
        assert "phase_name" in result

    @patch("app.services.planetary_ephemeris.load")
    def test_magnitude_none_when_not_available(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_t = MagicMock()
        mock_ts.from_datetime.return_value = mock_t
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        astrometric = _make_astrometric_mock()
        astrometric.apparent.return_value.magnitude.side_effect = Exception("no magnitude")

        mock_observer = MagicMock()
        mock_observer.at.return_value.observe.return_value = astrometric

        earth = MagicMock()
        earth.__add__ = Mock(return_value=mock_observer)
        mock_eph.__getitem__ = Mock(return_value=earth)

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()
        svc.ts = mock_ts
        svc.bodies["neptune"] = MagicMock()

        with patch("app.services.planetary_ephemeris.Topos", return_value=MagicMock()):
            result = svc.get_position("neptune", 45.0, -111.0,
                                      time=datetime(2025, 1, 15, 22, 0, tzinfo=timezone.utc))

        assert result["magnitude"] is None


class TestCalculateMoonPhase:

    @patch("app.services.planetary_ephemeris.load")
    def test_new_moon_phase(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()

        # elongation ~ 0° → new moon
        mock_observer = MagicMock()
        mock_t = MagicMock()

        moon_apparent = MagicMock()
        sun_apparent = MagicMock()
        sep = MagicMock()
        sep.degrees = 5.0  # near 0° → new moon
        moon_apparent.separation_from.return_value = sep

        mock_observer.at.return_value.observe.return_value.apparent.return_value = moon_apparent
        # For sun
        mock_observer.at.return_value.observe.side_effect = lambda b: MagicMock(
            apparent=Mock(return_value=sun_apparent)
        ) if b is svc.bodies.get("sun") else MagicMock(apparent=Mock(return_value=moon_apparent))

        result = svc._calculate_moon_phase(mock_observer, mock_t, MagicMock(), MagicMock())
        # Just verify keys exist and phase is a float
        assert "phase" in result
        assert "illumination" in result
        assert "phase_name" in result

    @patch("app.services.planetary_ephemeris.load")
    def test_phase_name_full_moon(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()

        mock_observer = MagicMock()
        mock_t = MagicMock()
        # elongation = 90° → phase = 0.5 → "Full Moon" (0.375 <= phase < 0.625)
        sep = MagicMock()
        sep.degrees = 90.0
        moon_apparent = MagicMock()
        moon_apparent.separation_from.return_value = sep
        sun_apparent = MagicMock()
        mock_observer.at.return_value.observe.return_value.apparent.return_value = moon_apparent

        result = svc._calculate_moon_phase(mock_observer, mock_t, MagicMock(), MagicMock())
        assert result["phase_name"] == "Full Moon"

    @patch("app.services.planetary_ephemeris.load")
    def test_phase_name_new_moon_zero_elongation(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()

        mock_observer = MagicMock()
        mock_t = MagicMock()
        sep = MagicMock()
        sep.degrees = 0.0
        moon_apparent = MagicMock()
        moon_apparent.separation_from.return_value = sep
        mock_observer.at.return_value.observe.return_value.apparent.return_value = moon_apparent

        result = svc._calculate_moon_phase(mock_observer, mock_t, MagicMock(), MagicMock())
        assert result["phase_name"] == "New Moon"


class TestGetAllVisible:

    @patch("app.services.planetary_ephemeris.load")
    def test_returns_only_bodies_above_min_altitude(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()
        svc.ts = mock_ts

        call_count = [0]

        def fake_get_position(body_name, lat, lon, elev=0.0, time=None):
            alt = 50.0 if call_count[0] % 2 == 0 else -10.0
            call_count[0] += 1
            return {"name": body_name, "altitude": alt, "azimuth": 180.0,
                    "ra_hours": 6.0, "dec_degrees": 20.0, "distance_au": 1.0,
                    "visible": alt > 0}

        with patch.object(svc, "get_position", side_effect=fake_get_position):
            result = svc.get_all_visible(45.0, -111.0, min_altitude=0.0)

        assert all(r["altitude"] >= 0 for r in result)

    @patch("app.services.planetary_ephemeris.load")
    def test_returns_sorted_by_altitude_descending(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()

        altitudes = iter([80.0, 45.0, 20.0, 60.0, 10.0, 55.0, 30.0, 70.0, 5.0])

        def fake_get_position(body_name, lat, lon, elev=0.0, time=None):
            alt = next(altitudes, 0.0)
            return {"name": body_name, "altitude": alt, "azimuth": 180.0,
                    "ra_hours": 6.0, "dec_degrees": 20.0, "distance_au": 1.0,
                    "visible": alt > 0}

        with patch.object(svc, "get_position", side_effect=fake_get_position):
            result = svc.get_all_visible(45.0, -111.0, min_altitude=0.0)

        alts = [r["altitude"] for r in result]
        assert alts == sorted(alts, reverse=True)

    @patch("app.services.planetary_ephemeris.load")
    def test_skips_body_on_exception(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()

        def fake_get_position(body_name, lat, lon, elev=0.0, time=None):
            if body_name == "mars":
                raise Exception("ephemeris error")
            return {"name": body_name, "altitude": 45.0, "azimuth": 180.0,
                    "ra_hours": 6.0, "dec_degrees": 20.0, "distance_au": 1.0,
                    "visible": True}

        with patch.object(svc, "get_position", side_effect=fake_get_position):
            result = svc.get_all_visible(45.0, -111.0)

        names = [r["name"] for r in result]
        assert "mars" not in names


class TestGetRiseSetTimes:

    @patch("app.services.planetary_ephemeris.load")
    def test_raises_for_unknown_body(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()

        with pytest.raises(ValueError, match="Unknown body"):
            svc.get_rise_set_times("pluto", 45.0, -111.0)

    @patch("app.services.planetary_ephemeris.load")
    @patch("app.services.planetary_ephemeris.find_discrete")
    def test_returns_rise_set_dict(self, mock_find_discrete, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_t_start = MagicMock()
        mock_t_end = MagicMock()
        mock_ts.from_datetime.side_effect = [mock_t_start, mock_t_end]
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        rise_t = MagicMock()
        rise_t.utc_datetime.return_value = datetime(2025, 1, 15, 6, 0, tzinfo=timezone.utc)
        set_t = MagicMock()
        set_t.utc_datetime.return_value = datetime(2025, 1, 15, 18, 0, tzinfo=timezone.utc)
        mock_find_discrete.return_value = ([rise_t, set_t], [True, False])

        # Patch the observer + body construction
        mock_observer_plus_body = MagicMock()
        mock_observer_plus_body.at = MagicMock()

        earth = MagicMock()
        earth.__add__ = Mock(return_value=mock_observer_plus_body)
        mock_eph.__getitem__ = Mock(return_value=earth)

        from app.services.planetary_ephemeris import PlanetaryEphemeris
        svc = PlanetaryEphemeris()
        svc.ts = mock_ts
        svc.bodies["mars"] = MagicMock()

        with patch("app.services.planetary_ephemeris.Topos", return_value=MagicMock()):
            result = svc.get_rise_set_times("mars", 45.0, -111.0,
                                            date=datetime(2025, 1, 15, tzinfo=timezone.utc))

        assert "rise" in result
        assert "set" in result


class TestGetEphemerisSingleton:

    @patch("app.services.planetary_ephemeris.load")
    def test_get_ephemeris_returns_instance(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        import app.services.planetary_ephemeris as mod
        mod._ephemeris = None  # reset singleton

        from app.services.planetary_ephemeris import get_ephemeris, PlanetaryEphemeris
        result = get_ephemeris()
        assert isinstance(result, PlanetaryEphemeris)

    @patch("app.services.planetary_ephemeris.load")
    def test_get_ephemeris_returns_same_instance(self, mock_load):
        mock_eph = _make_mock_eph()
        mock_ts = MagicMock()
        mock_load.return_value = mock_eph
        mock_load.timescale.return_value = mock_ts

        import app.services.planetary_ephemeris as mod
        mod._ephemeris = None  # reset singleton

        from app.services.planetary_ephemeris import get_ephemeris
        inst1 = get_ephemeris()
        inst2 = get_ephemeris()
        assert inst1 is inst2
