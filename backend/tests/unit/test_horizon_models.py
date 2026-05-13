"""Tests for horizon profile model."""

import pytest
from app.models.models import HorizonPoint, ObservingConstraints


def test_horizon_point_valid():
    pt = HorizonPoint(az=90.0, alt=15.0)
    assert pt.az == 90.0
    assert pt.alt == 15.0


def test_horizon_point_rejects_invalid_az():
    with pytest.raises(Exception):
        HorizonPoint(az=400.0, alt=10.0)


def test_observing_constraints_accepts_horizon_profile():
    profile = [HorizonPoint(az=0.0, alt=5.0), HorizonPoint(az=180.0, alt=20.0)]
    c = ObservingConstraints(horizon_profile=profile)
    assert len(c.horizon_profile) == 2


def test_observing_constraints_horizon_profile_defaults_none():
    c = ObservingConstraints()
    assert c.horizon_profile is None
