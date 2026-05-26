"""Tests for horizon profile altitude interpolation."""


from app.models.models import HorizonPoint
from app.services.ephemeris_service import EphemerisService


def make_profile(points):
    return [HorizonPoint(az=az, alt=alt) for az, alt in points]


class TestHorizonInterpolation:

    def setup_method(self):
        self.svc = EphemerisService()

    def test_empty_profile_returns_zero(self):
        assert self.svc.interpolate_horizon_altitude(90.0, []) == 0.0

    def test_single_point_returns_its_altitude(self):
        profile = make_profile([(90.0, 15.0)])
        assert self.svc.interpolate_horizon_altitude(90.0, profile) == 15.0

    def test_exact_match_returns_altitude(self):
        profile = make_profile([(0.0, 5.0), (90.0, 15.0), (180.0, 25.0), (270.0, 10.0)])
        assert self.svc.interpolate_horizon_altitude(90.0, profile) == 15.0

    def test_interpolates_between_points(self):
        profile = make_profile([(0.0, 0.0), (90.0, 18.0)])
        result = self.svc.interpolate_horizon_altitude(45.0, profile)
        assert abs(result - 9.0) < 0.01

    def test_wraps_around_360(self):
        profile = make_profile([(350.0, 10.0), (10.0, 20.0)])
        result = self.svc.interpolate_horizon_altitude(0.0, profile)
        assert abs(result - 15.0) < 0.01

    def test_get_effective_min_altitude_no_profile(self):
        result = self.svc.get_effective_min_altitude(90.0, 30.0, None)
        assert result == 30.0

    def test_get_effective_min_altitude_uses_max(self):
        profile = make_profile([(90.0, 35.0)])
        result = self.svc.get_effective_min_altitude(90.0, 30.0, profile)
        assert result == 35.0

    def test_get_effective_min_altitude_flat_min_wins(self):
        profile = make_profile([(90.0, 5.0)])
        result = self.svc.get_effective_min_altitude(90.0, 30.0, profile)
        assert result == 30.0
