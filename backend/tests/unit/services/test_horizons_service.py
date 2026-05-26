"""Tests for JPL Horizons comet service."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models import CometTarget, OrbitalElements
from app.services.horizons_service import HorizonsService


def _make_elements_row(overrides=None):
    """Return a mock astropy Table row with default comet orbital element values."""
    defaults = {
        "e": 0.5,
        "datetime_jd": 2460000.5,
        "q": 1.2,
        "incl": 45.0,
        "w": 100.0,
        "Omega": 200.0,
        "Tp_jd": 2459900.0,
        "P": 10.0,
    }
    if overrides:
        defaults.update(overrides)

    row = MagicMock()
    row.__getitem__ = lambda self, key: defaults[key]
    row.colnames = list(defaults.keys())
    return row


def _make_elements_table(rows):
    """Return a mock astropy Table with the given rows."""
    table = MagicMock()
    table.__len__ = Mock(return_value=len(rows))
    table.__iter__ = Mock(return_value=iter(rows))
    table.__getitem__ = Mock(side_effect=lambda i: rows[i])
    table.colnames = rows[0].colnames if rows else []
    return table


class TestFetchCometByDesignation:

    @patch("app.services.horizons_service.Horizons")
    def test_returns_none_when_elements_empty(self, mock_horizons_cls):
        mock_obj = MagicMock()
        empty_table = MagicMock()
        empty_table.__len__ = Mock(return_value=0)
        mock_obj.elements.return_value = empty_table
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_comet_by_designation("C/2099 Z1")
        assert result is None

    @patch("app.services.horizons_service.Horizons")
    def test_returns_comet_target_on_success(self, mock_horizons_cls):
        row = _make_elements_row()
        table = _make_elements_table([row])
        mock_obj = MagicMock()
        mock_obj.elements.return_value = table
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_comet_by_designation("46P/Wirtanen")

        assert isinstance(result, CometTarget)
        assert result.designation == "46P/Wirtanen"
        assert result.data_source == "JPL Horizons"

    @patch("app.services.horizons_service.Horizons")
    def test_short_period_comet_type(self, mock_horizons_cls):
        row = _make_elements_row({"e": 0.5, "P": 5.0})
        table = _make_elements_table([row])
        mock_obj = MagicMock()
        mock_obj.elements.return_value = table
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_comet_by_designation("2P/Encke")
        assert result.comet_type == "short-period"

    @patch("app.services.horizons_service.Horizons")
    def test_long_period_comet_type(self, mock_horizons_cls):
        row = _make_elements_row({"e": 0.9, "P": 3000.0})
        table = _make_elements_table([row])
        mock_obj = MagicMock()
        mock_obj.elements.return_value = table
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_comet_by_designation("C/1997 L1")
        assert result.comet_type == "long-period"

    @patch("app.services.horizons_service.Horizons")
    def test_hyperbolic_comet_type(self, mock_horizons_cls):
        row = _make_elements_row({"e": 1.1})
        table = _make_elements_table([row])
        mock_obj = MagicMock()
        mock_obj.elements.return_value = table
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_comet_by_designation("1I/Oumuamua")
        assert result.comet_type == "hyperbolic"

    @patch("app.services.horizons_service.Horizons")
    def test_extracts_magnitude_m1(self, mock_horizons_cls):
        row = _make_elements_row({"M1": 7.5, "K1": 5.0})
        table = _make_elements_table([row])
        mock_obj = MagicMock()
        mock_obj.elements.return_value = table
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_comet_by_designation("C/2020 F3")
        assert result.absolute_magnitude == 7.5
        assert result.magnitude_slope == 5.0

    @patch("app.services.horizons_service.Horizons")
    def test_extracts_current_magnitude_v(self, mock_horizons_cls):
        row = _make_elements_row({"V": 9.2})
        table = _make_elements_table([row])
        mock_obj = MagicMock()
        mock_obj.elements.return_value = table
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_comet_by_designation("C/2020 F3")
        assert result.current_magnitude == 9.2

    @patch("app.services.horizons_service.Horizons")
    def test_handles_exception_gracefully(self, mock_horizons_cls):
        mock_horizons_cls.side_effect = Exception("network timeout")

        svc = HorizonsService()
        result = svc.fetch_comet_by_designation("C/2020 F3")
        assert result is None

    @patch("app.services.horizons_service.Horizons")
    def test_uses_default_epoch_when_none(self, mock_horizons_cls):
        row = _make_elements_row()
        table = _make_elements_table([row])
        mock_obj = MagicMock()
        mock_obj.elements.return_value = table
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_comet_by_designation("67P/Churyumov-Gerasimenko", epoch=None)
        assert result is not None

    @patch("app.services.horizons_service.Horizons")
    def test_uses_provided_epoch(self, mock_horizons_cls):
        row = _make_elements_row()
        table = _make_elements_table([row])
        mock_obj = MagicMock()
        mock_obj.elements.return_value = table
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        epoch = datetime(2025, 1, 15, 12, 0, 0)
        result = svc.fetch_comet_by_designation("C/2020 F3", epoch=epoch)
        assert result is not None

    @patch("app.services.horizons_service.Horizons")
    def test_orbital_elements_populated(self, mock_horizons_cls):
        row = _make_elements_row()
        table = _make_elements_table([row])
        mock_obj = MagicMock()
        mock_obj.elements.return_value = table
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_comet_by_designation("46P/Wirtanen")

        assert isinstance(result.orbital_elements, OrbitalElements)
        assert result.orbital_elements.eccentricity == 0.5
        assert result.orbital_elements.perihelion_distance_au == 1.2
        assert result.orbital_elements.inclination_deg == 45.0


class TestFetchBrightComets:

    @patch.object(HorizonsService, "fetch_active_comets_from_mpc")
    def test_returns_list(self, mock_mpc):
        mock_mpc.return_value = []
        svc = HorizonsService()
        with patch.object(svc, "fetch_comet_by_designation", return_value=None):
            result = svc.fetch_bright_comets(max_magnitude=12.0)
        assert isinstance(result, list)

    @patch.object(HorizonsService, "fetch_active_comets_from_mpc")
    def test_mpc_results_returned_directly(self, mock_mpc):
        comet = MagicMock(spec=CometTarget)
        comet.current_magnitude = 8.0
        mock_mpc.return_value = [comet]

        svc = HorizonsService()
        result = svc.fetch_bright_comets(max_magnitude=12.0)
        assert len(result) == 1

    @patch.object(HorizonsService, "fetch_active_comets_from_mpc")
    def test_mpc_filters_by_magnitude(self, mock_mpc):
        bright = MagicMock(spec=CometTarget)
        bright.current_magnitude = 9.0
        faint = MagicMock(spec=CometTarget)
        faint.current_magnitude = 15.0
        mock_mpc.return_value = [bright, faint]

        svc = HorizonsService()
        result = svc.fetch_bright_comets(max_magnitude=12.0)
        assert all(c.current_magnitude <= 12.0 for c in result)

    @patch.object(HorizonsService, "fetch_active_comets_from_mpc", side_effect=Exception("mpc down"))
    @patch.object(HorizonsService, "fetch_comet_by_designation", return_value=None)
    def test_falls_back_to_curated_list_on_mpc_failure(self, mock_fetch, mock_mpc):
        svc = HorizonsService()
        result = svc.fetch_bright_comets(max_magnitude=12.0)
        assert isinstance(result, list)
        # fetch_comet_by_designation called for each known comet
        assert mock_fetch.call_count > 0

    @patch.object(HorizonsService, "fetch_active_comets_from_mpc", side_effect=Exception("mpc down"))
    @patch.object(HorizonsService, "fetch_comet_by_designation")
    def test_fallback_includes_comets_within_magnitude(self, mock_fetch, mock_mpc):
        comet = MagicMock(spec=CometTarget)
        comet.current_magnitude = 10.0
        mock_fetch.return_value = comet

        svc = HorizonsService()
        result = svc.fetch_bright_comets(max_magnitude=12.0)
        assert len(result) > 0


class TestFetchEphemeris:

    @patch("app.services.horizons_service.Horizons")
    def test_returns_dict_with_data_key(self, mock_horizons_cls):
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, k: {
            "datetime_jd": 2460000.5,
            "datetime_str": "2026-01-01 00:00",
            "RA": 150.0,
            "DEC": 45.0,
            "delta": 1.5,
            "r": 2.0,
        }[k]
        mock_row.colnames = ["datetime_jd", "datetime_str", "RA", "DEC", "delta", "r"]

        mock_eph = MagicMock()
        mock_eph.__iter__ = Mock(return_value=iter([mock_row]))
        mock_obj = MagicMock()
        mock_obj.ephemerides.return_value = mock_eph
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_ephemeris("C/2020 F3", datetime(2026, 1, 1))
        assert "data" in result
        assert result["designation"] == "C/2020 F3"

    @patch("app.services.horizons_service.Horizons", side_effect=Exception("api error"))
    def test_returns_error_dict_on_exception(self, mock_horizons_cls):
        svc = HorizonsService()
        result = svc.fetch_ephemeris("C/2020 F3", datetime(2026, 1, 1))
        assert result["data"] == []
        assert "error" in result

    @patch("app.services.horizons_service.Horizons")
    def test_uses_time_range_when_end_time_provided(self, mock_horizons_cls):
        mock_eph = MagicMock()
        mock_eph.__iter__ = Mock(return_value=iter([]))
        mock_obj = MagicMock()
        mock_obj.ephemerides.return_value = mock_eph
        mock_horizons_cls.return_value = mock_obj

        svc = HorizonsService()
        result = svc.fetch_ephemeris(
            "C/2020 F3",
            datetime(2026, 1, 1),
            end_time=datetime(2026, 1, 3),
            step="1d",
        )
        # Should have called Horizons with epoch dict (start/stop/step)
        call_kwargs = mock_horizons_cls.call_args
        assert call_kwargs is not None
        assert result["designation"] == "C/2020 F3"
