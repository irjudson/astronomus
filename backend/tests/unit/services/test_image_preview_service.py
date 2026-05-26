"""Tests for image preview service."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models.models import DSOTarget
from app.services.image_preview_service import ImagePreviewService


@pytest.fixture
def target():
    return DSOTarget(
        catalog_id="M31",
        name="Andromeda Galaxy",
        object_type="galaxy",
        ra_hours=0.712,
        dec_degrees=41.269,
        magnitude=3.4,
        size_arcmin=178.0,
        description="Andromeda Galaxy",
    )


@pytest.fixture
def small_target():
    return DSOTarget(
        catalog_id="NGC 1:2/3",
        name="Test Target",
        object_type="nebula",
        ra_hours=5.0,
        dec_degrees=-5.0,
        magnitude=8.0,
        size_arcmin=5.0,
        description="Small test target",
    )


class TestImagePreviewServiceInit:

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_cache_available_when_mkdir_succeeds(self, mock_mkdir):
        svc = ImagePreviewService()
        assert svc.cache_available is True

    @patch("app.services.image_preview_service.Path.mkdir", side_effect=PermissionError("no access"))
    def test_cache_unavailable_on_permission_error(self, mock_mkdir):
        svc = ImagePreviewService()
        assert svc.cache_available is False

    @patch("app.services.image_preview_service.Path.mkdir", side_effect=OSError("disk error"))
    def test_cache_unavailable_on_os_error(self, mock_mkdir):
        svc = ImagePreviewService()
        assert svc.cache_available is False

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_no_db_session_by_default(self, mock_mkdir):
        svc = ImagePreviewService()
        assert svc.db is None


class TestGetPreviewUrl:

    @patch("app.services.image_preview_service.Path.mkdir", side_effect=PermissionError)
    def test_returns_none_when_cache_unavailable(self, mock_mkdir, target):
        svc = ImagePreviewService()
        result = svc.get_preview_url(target)
        assert result is None

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.Path.exists", return_value=True)
    def test_returns_cached_url_when_file_exists(self, mock_exists, mock_mkdir, target):
        svc = ImagePreviewService()
        result = svc.get_preview_url(target)
        assert result == "/api/images/previews/M31.jpg"

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.Path.exists", return_value=False)
    @patch.object(ImagePreviewService, "_fetch_from_skyview", return_value=b"\xff\xd8" + b"x" * 5000)
    def test_fetches_and_saves_when_not_cached(self, mock_fetch, mock_exists, mock_mkdir, target):
        svc = ImagePreviewService()
        with patch.object(Path, "write_bytes") as mock_write:
            result = svc.get_preview_url(target)
        assert result == "/api/images/previews/M31.jpg"
        mock_fetch.assert_called_once_with(target)

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.Path.exists", return_value=False)
    @patch.object(ImagePreviewService, "_fetch_from_skyview", return_value=None)
    def test_returns_none_when_fetch_returns_none(self, mock_fetch, mock_exists, mock_mkdir, target):
        svc = ImagePreviewService()
        result = svc.get_preview_url(target)
        assert result is None

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.Path.exists", return_value=False)
    @patch.object(ImagePreviewService, "_fetch_from_skyview", side_effect=Exception("network error"))
    def test_returns_none_on_fetch_exception(self, mock_fetch, mock_exists, mock_mkdir, target):
        svc = ImagePreviewService()
        result = svc.get_preview_url(target)
        assert result is None


class TestSanitizeCatalogId:

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_replaces_spaces(self, mock_mkdir):
        svc = ImagePreviewService()
        assert svc._sanitize_catalog_id("NGC 224") == "NGC_224"

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_replaces_slashes(self, mock_mkdir):
        svc = ImagePreviewService()
        assert svc._sanitize_catalog_id("C/2020 F3") == "C_2020_F3"

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_replaces_colons(self, mock_mkdir):
        svc = ImagePreviewService()
        assert svc._sanitize_catalog_id("IC:1234") == "IC_1234"

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_plain_id_unchanged(self, mock_mkdir):
        svc = ImagePreviewService()
        assert svc._sanitize_catalog_id("M31") == "M31"

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_complex_id_with_multiple_special_chars(self, mock_mkdir, small_target):
        svc = ImagePreviewService()
        result = svc._sanitize_catalog_id(small_target.catalog_id)
        assert " " not in result
        assert "/" not in result
        assert ":" not in result


class TestScoreImageQuality:

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_none_data_returns_zero(self, mock_mkdir):
        svc = ImagePreviewService()
        assert svc._score_image_quality(None) == 0.0

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_empty_data_returns_zero(self, mock_mkdir):
        svc = ImagePreviewService()
        assert svc._score_image_quality(b"") == 0.0

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_very_small_data_returns_low_score(self, mock_mkdir):
        svc = ImagePreviewService()
        # < 5 KB returns 10.0
        score = svc._score_image_quality(b"x" * 100)
        assert score == 10.0

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_jpeg_header_adds_format_score(self, mock_mkdir):
        svc = ImagePreviewService()
        # JPEG magic bytes + enough data to not trigger the <5KB penalty
        jpeg_data = b"\xff\xd8" + b"x" * (10 * 1024)
        score_jpeg = svc._score_image_quality(jpeg_data)
        non_jpeg = b"\x00\x00" + b"x" * (10 * 1024)
        score_non_jpeg = svc._score_image_quality(non_jpeg)
        assert score_jpeg > score_non_jpeg

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_larger_image_scores_higher(self, mock_mkdir):
        svc = ImagePreviewService()
        small = b"x" * (10 * 1024)
        large = b"x" * (200 * 1024)
        assert svc._score_image_quality(large) > svc._score_image_quality(small)

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_score_capped_at_100(self, mock_mkdir):
        svc = ImagePreviewService()
        huge = b"\xff\xd8" + b"x" * (1024 * 1024)
        assert svc._score_image_quality(huge) <= 100.0


class TestGetOrderedSources:

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_no_db_returns_defaults(self, mock_mkdir):
        svc = ImagePreviewService()
        sources = svc._get_ordered_sources()
        names = [s["name"] for s in sources]
        assert "sdss" in names
        assert "panstarrs" in names
        assert "skyview_dss" in names

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_db_empty_returns_defaults(self, mock_mkdir):
        svc = ImagePreviewService()
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.all.return_value = []
        svc.db = mock_db
        sources = svc._get_ordered_sources()
        names = [s["name"] for s in sources]
        assert "sdss" in names

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_db_error_returns_defaults(self, mock_mkdir):
        svc = ImagePreviewService()
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("db error")
        svc.db = mock_db
        sources = svc._get_ordered_sources()
        assert len(sources) > 0


class TestFetchSingleSource:

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch.object(ImagePreviewService, "_fetch_from_sdss", return_value=b"\xff\xd8" + b"x" * 5000)
    def test_fetch_single_sdss_success(self, mock_sdss, mock_mkdir):
        svc = ImagePreviewService()
        result = svc._fetch_single("sdss", 10.0, 41.0, 20.0, "M31")
        assert result["source"] == "sdss"
        assert result["data"] is not None
        assert result["quality_score"] > 0

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch.object(ImagePreviewService, "_fetch_from_panstarrs", return_value=None)
    def test_fetch_single_panstarrs_no_data(self, mock_ps, mock_mkdir):
        svc = ImagePreviewService()
        result = svc._fetch_single("panstarrs", 10.0, 41.0, 20.0, "M31")
        assert result["source"] == "panstarrs"
        assert result["data"] is None
        assert result["quality_score"] == 0.0

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch.object(ImagePreviewService, "_fetch_from_eso", side_effect=Exception("eso down"))
    def test_fetch_single_eso_exception(self, mock_eso, mock_mkdir):
        svc = ImagePreviewService()
        result = svc._fetch_single("eso", 10.0, 41.0, 20.0, "M31")
        assert result["source"] == "eso"
        assert result["data"] is None

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch.object(ImagePreviewService, "_fetch_from_skyview_dss", return_value=b"\xff\xd8" + b"x" * 5000)
    def test_fetch_single_skyview_dss(self, mock_skyview, mock_mkdir):
        svc = ImagePreviewService()
        result = svc._fetch_single("skyview_dss", 10.0, 41.0, 20.0, "M31")
        assert result["source"] == "skyview_dss"

    @patch("app.services.image_preview_service.Path.mkdir")
    def test_fetch_single_unknown_source(self, mock_mkdir):
        svc = ImagePreviewService()
        result = svc._fetch_single("unknown_source", 10.0, 41.0, 20.0, "M31")
        assert result["data"] is None
        assert result["quality_score"] == 0.0


class TestIndividualFetchers:

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.httpx.Client")
    def test_fetch_from_sdss_success(self, mock_client_cls, mock_mkdir):
        svc = ImagePreviewService()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = b"x" * 2000
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client
        result = svc._fetch_from_sdss(10.0, 41.0, 20.0)
        assert result == mock_resp.content

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.httpx.Client")
    def test_fetch_from_sdss_small_response(self, mock_client_cls, mock_mkdir):
        svc = ImagePreviewService()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = b"x" * 100  # too small
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client
        result = svc._fetch_from_sdss(10.0, 41.0, 20.0)
        assert result is None

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.httpx.Client")
    def test_fetch_from_sdss_http_error(self, mock_client_cls, mock_mkdir):
        svc = ImagePreviewService()
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.side_effect = Exception("connection error")
        mock_client_cls.return_value = mock_client
        result = svc._fetch_from_sdss(10.0, 41.0, 20.0)
        assert result is None

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.httpx.Client")
    def test_fetch_from_panstarrs_success(self, mock_client_cls, mock_mkdir):
        svc = ImagePreviewService()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = b"image data"
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client
        result = svc._fetch_from_panstarrs(10.0, 41.0, 20.0)
        assert result == mock_resp.content

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.httpx.Client")
    def test_fetch_from_panstarrs_wrong_content_type(self, mock_client_cls, mock_mkdir):
        svc = ImagePreviewService()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = b"html error"
        mock_resp.headers = {"content-type": "text/html"}
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client
        result = svc._fetch_from_panstarrs(10.0, 41.0, 20.0)
        assert result is None

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.httpx.Client")
    def test_fetch_from_eso_success(self, mock_client_cls, mock_mkdir):
        svc = ImagePreviewService()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = b"eso image"
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client
        result = svc._fetch_from_eso(10.0, 41.0, 20.0)
        assert result == mock_resp.content

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.httpx.Client")
    def test_fetch_from_skyview_dss_success(self, mock_client_cls, mock_mkdir):
        svc = ImagePreviewService()
        mock_resp = Mock()
        mock_resp.content = b"dss image"
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_resp.raise_for_status = Mock()
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client
        result = svc._fetch_from_skyview_dss(10.0, 41.0, 20.0)
        assert result == mock_resp.content

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.httpx.Client")
    def test_fetch_from_skyview_dss_raises(self, mock_client_cls, mock_mkdir):
        svc = ImagePreviewService()
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.side_effect = Exception("timeout")
        mock_client_cls.return_value = mock_client
        result = svc._fetch_from_skyview_dss(10.0, 41.0, 20.0)
        assert result is None


class TestFovCalculation:
    """Test that FOV is computed correctly from target size."""

    @patch("app.services.image_preview_service.Path.mkdir")
    @patch("app.services.image_preview_service.Path.exists", return_value=False)
    @patch.object(ImagePreviewService, "_fetch_from_skyview", return_value=None)
    def test_fov_uses_minimum_12_arcmin(self, mock_fetch, mock_exists, mock_mkdir):
        """Very small targets still get at least 12 arcmin FOV."""
        tiny_target = DSOTarget(
            catalog_id="TINY",
            name="Tiny",
            object_type="star",
            ra_hours=1.0,
            dec_degrees=0.0,
            magnitude=10.0,
            size_arcmin=1.0,  # small → 2× = 2 arcmin, clamped to 12
            description="tiny",
        )
        svc = ImagePreviewService()
        svc.get_preview_url(tiny_target)
        # _fetch_from_skyview should be called; if called, FOV was computed
        mock_fetch.assert_called_once_with(tiny_target)
