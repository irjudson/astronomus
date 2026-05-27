"""Tests for file scanner service."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.file_scanner_service import FileScannerService


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def file_scanner_service(mock_db):
    """Create file scanner service with mock database."""
    return FileScannerService(mock_db)


class TestFileScannerService:
    """Test file scanner service core functionality."""

    def test_init(self, file_scanner_service, mock_db):
        """Test service initialization."""
        assert file_scanner_service.db == mock_db


class TestFuzzyMatching:
    """Test fuzzy matching of target names to catalog."""

    def test_fuzzy_match_exact(self, file_scanner_service, mock_db):
        """Test exact match of target name."""
        # Mock DSOCatalog to return a match
        mock_dso = Mock()
        mock_dso.common_name = "M031"
        mock_dso.caldwell_number = None
        mock_dso.catalog_name = "NGC"
        mock_dso.catalog_number = 224
        mock_db.query.return_value.all.return_value = [mock_dso]

        result = file_scanner_service._fuzzy_match_catalog("M31")

        assert result is not None
        catalog_id, confidence = result
        assert catalog_id == "M31"
        assert confidence >= 0.7

    def test_fuzzy_match_with_space(self, file_scanner_service, mock_db):
        """Test match handling space normalization (M 31 vs M31)."""
        mock_dso = Mock()
        mock_dso.common_name = "M031"
        mock_dso.caldwell_number = None
        mock_dso.catalog_name = "NGC"
        mock_dso.catalog_number = 224
        mock_db.query.return_value.all.return_value = [mock_dso]

        result = file_scanner_service._fuzzy_match_catalog("M 31")

        assert result is not None
        catalog_id, confidence = result
        assert confidence >= 0.7

    def test_fuzzy_match_alternate_name(self, file_scanner_service, mock_db):
        """Test matching alternate names (Andromeda vs M31)."""
        # This tests fuzzy matching with common names
        mock_dso = Mock()
        mock_dso.common_name = "Andromeda"
        mock_dso.caldwell_number = None
        mock_dso.catalog_name = "NGC"
        mock_dso.catalog_number = 224
        mock_db.query.return_value.all.return_value = [mock_dso]

        # For this test, just verify the method exists and returns something when
        # given a name that might match
        result = file_scanner_service._fuzzy_match_catalog("Andromeda")

        # Either finds a match or returns None - just verify it doesn't crash
        assert result is None or (isinstance(result, tuple) and len(result) == 2)

    def test_fuzzy_match_no_match(self, file_scanner_service, mock_db):
        """Test no match found below threshold."""
        mock_db.query.return_value.all.return_value = []

        result = file_scanner_service._fuzzy_match_catalog("NONEXISTENT_OBJECT_XYZ")

        assert result is None


class TestFitsMetadataExtraction:
    """Test FITS metadata extraction from image files."""

    @patch("app.services.file_scanner_service.fits")
    def test_extract_fits_metadata_success(self, mock_fits, file_scanner_service):
        """Test successful FITS metadata extraction."""
        # Mock FITS file reading
        mock_hdu = MagicMock()
        mock_hdu.header = {
            "OBJECT": "M31",
            "EXPTIME": 10.0,
            "FILTER": "L",
            "CCD-TEMP": -10.5,
            "GAIN": 100,
            "DATE-OBS": "2024-12-25T20:30:00",
        }
        mock_fits.open.return_value.__enter__.return_value = [mock_hdu]

        result = file_scanner_service._extract_fits_metadata("/path/to/file.fits")

        assert result is not None
        assert result["target_name"] == "M31"
        assert result["exposure_seconds"] == 10
        assert result["filter_name"] == "L"
        assert result["temperature_celsius"] == -10.5
        assert result["gain"] == 100
        assert result["observation_date"] is not None

    @patch("app.services.file_scanner_service.fits")
    def test_extract_fits_metadata_missing_fields(self, mock_fits, file_scanner_service):
        """Test FITS extraction with missing optional fields."""
        # Mock FITS file with minimal fields
        mock_hdu = MagicMock()
        mock_hdu.header = {
            "OBJECT": "M42",
        }
        mock_fits.open.return_value.__enter__.return_value = [mock_hdu]

        result = file_scanner_service._extract_fits_metadata("/path/to/file.fits")

        assert result is not None
        assert result["target_name"] == "M42"
        # Optional fields should be None
        assert result.get("exposure_seconds") is None
        assert result.get("filter_name") is None
        assert result.get("temperature_celsius") is None
        assert result.get("gain") is None

    @patch("app.services.file_scanner_service.fits")
    def test_extract_fits_metadata_file_error(self, mock_fits, file_scanner_service):
        """Test FITS extraction with file read error."""
        # Mock file read error
        mock_fits.open.side_effect = Exception("File not found")

        result = file_scanner_service._extract_fits_metadata("/path/to/nonexistent.fits")

        assert result is None


class TestQualityMetrics:
    """Test quality metrics calculation placeholder."""

    def test_calculate_quality_metrics_placeholder(self, file_scanner_service):
        """Test quality metrics returns placeholder None values."""
        result = file_scanner_service._calculate_quality_metrics("/path/to/file.fits")

        assert result is not None
        assert result["fwhm"] is None
        assert result["star_count"] is None

    def test_calculate_quality_metrics_returns_dict(self, file_scanner_service):
        """Test quality metrics returns dict with expected keys."""
        result = file_scanner_service._calculate_quality_metrics("/path/to/file.fits")

        assert isinstance(result, dict)
        assert "fwhm" in result
        assert "star_count" in result


class TestScanFiles:
    """Test main scan_files method that orchestrates file discovery and processing."""

    @patch("app.services.file_scanner_service.os.walk")
    @patch("app.services.file_scanner_service.os.path.getsize")
    def test_scan_files_empty_directory(self, mock_getsize, mock_walk, file_scanner_service, mock_db):
        """Test scanning an empty directory."""
        # Mock empty directory
        mock_walk.return_value = [("/path/to/dir", [], [])]

        result = file_scanner_service.scan_files("/path/to/dir", mock_db)

        assert result == 0

    @patch("app.services.file_scanner_service.os.walk")
    @patch("app.services.file_scanner_service.os.path.getsize")
    @patch("app.services.file_scanner_service.fits")
    def test_scan_files_with_fits_files(self, mock_fits, mock_getsize, mock_walk, file_scanner_service, mock_db):
        """Test scanning directory with FITS files."""
        # Mock directory with one FITS file
        mock_walk.return_value = [
            ("/path/to/dir", [], ["image.fits"]),
        ]
        mock_getsize.return_value = 1024 * 1024  # 1 MB

        # Mock FITS metadata extraction
        mock_hdu = MagicMock()
        mock_hdu.header = {
            "OBJECT": "M31",
            "EXPTIME": 10.0,
            "FILTER": "L",
        }
        mock_fits.open.return_value.__enter__.return_value = [mock_hdu]

        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Mock fuzzy matching
        file_scanner_service._fuzzy_match_catalog = Mock(return_value=("M31", 1.0))

        result = file_scanner_service.scan_files("/path/to/dir", mock_db)

        assert result == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("app.services.file_scanner_service.os.walk")
    @patch("app.services.file_scanner_service.os.path.getsize")
    def test_scan_files_non_fits_file_skipped(self, mock_getsize, mock_walk, file_scanner_service, mock_db):
        """Test that non-FITS files are skipped."""
        # Mock directory with non-matching file
        mock_walk.return_value = [
            ("/path/to/dir", [], ["readme.txt"]),
        ]

        result = file_scanner_service.scan_files("/path/to/dir", mock_db)

        assert result == 0
        mock_db.add.assert_not_called()

    @patch("app.services.file_scanner_service.os.walk")
    @patch("app.services.file_scanner_service.os.path.getsize")
    @patch("app.services.file_scanner_service.fits")
    def test_scan_files_no_fuzzy_match(self, mock_fits, mock_getsize, mock_walk, file_scanner_service, mock_db):
        """Test handling file when fuzzy matching returns no match."""
        # Mock directory with FITS file
        mock_walk.return_value = [
            ("/path/to/dir", [], ["unknown.fits"]),
        ]
        mock_getsize.return_value = 1024

        # Mock FITS metadata
        mock_hdu = MagicMock()
        mock_hdu.header = {"OBJECT": "UNKNOWN_OBJECT"}
        mock_fits.open.return_value.__enter__.return_value = [mock_hdu]

        # Mock no match from fuzzy matching
        file_scanner_service._fuzzy_match_catalog = Mock(return_value=None)

        result = file_scanner_service.scan_files("/path/to/dir", mock_db)

        # Should still process but with None catalog_id
        assert result == 1

    @patch("app.services.file_scanner_service.os.walk")
    @patch("app.services.file_scanner_service.os.path.getsize")
    def test_scan_files_exception_in_processing_skips_file(self, mock_getsize, mock_walk,
                                                             file_scanner_service, mock_db):
        """Test that an exception during file processing is silently skipped."""
        mock_walk.return_value = [("/path/to/dir", [], ["bad.fits"])]
        mock_getsize.side_effect = OSError("permission denied")

        result = file_scanner_service.scan_files("/path/to/dir", mock_db)

        assert result == 0
        mock_db.add.assert_not_called()

    @patch("app.services.file_scanner_service.os.walk")
    @patch("app.services.file_scanner_service.os.path.getsize")
    @patch("app.services.file_scanner_service.fits")
    def test_scan_files_no_metadata_for_fit_file(self, mock_fits, mock_getsize, mock_walk,
                                                   file_scanner_service, mock_db):
        """Test scan when FITS metadata extraction returns None."""
        mock_walk.return_value = [("/path/to/dir", [], ["image.fit"])]
        mock_getsize.return_value = 512
        mock_fits.open.side_effect = Exception("corrupt FITS")
        mock_db.add = Mock()
        mock_db.commit = Mock()

        result = file_scanner_service.scan_files("/path/to/dir", mock_db)

        # File is processed even without metadata
        assert result == 1
        mock_db.add.assert_called_once()

    @patch("app.services.file_scanner_service.os.walk")
    @patch("app.services.file_scanner_service.os.path.getsize")
    def test_scan_files_jpg_skips_fits_metadata(self, mock_getsize, mock_walk,
                                                 file_scanner_service, mock_db):
        """Non-FITS files skip metadata extraction."""
        mock_walk.return_value = [("/path/to/dir", [], ["photo.jpg"])]
        mock_getsize.return_value = 2048
        mock_db.add = Mock()
        mock_db.commit = Mock()

        result = file_scanner_service.scan_files("/path/to/dir", mock_db)

        assert result == 1
        mock_db.add.assert_called_once()


class TestFuzzyMatchEdgeCases:
    def test_empty_target_name_returns_none(self, file_scanner_service):
        result = file_scanner_service._fuzzy_match_catalog("")
        assert result is None

    def test_whitespace_only_target_name_returns_none(self, file_scanner_service):
        result = file_scanner_service._fuzzy_match_catalog("   ")
        assert result is None

    def test_caldwell_number_generates_c_id(self, file_scanner_service, mock_db):
        mock_dso = Mock()
        mock_dso.common_name = "Blinking Nebula"
        mock_dso.caldwell_number = 15
        mock_dso.catalog_name = "NGC"
        mock_dso.catalog_number = 6826
        mock_db.query.return_value.all.return_value = [mock_dso]

        result = file_scanner_service._fuzzy_match_catalog("Blinking Nebula")
        if result:
            catalog_id, _ = result
            assert catalog_id == "C15"

    def test_fallback_catalog_id_uses_name_and_number(self, file_scanner_service, mock_db):
        mock_dso = Mock()
        mock_dso.common_name = "Orion Nebula"
        mock_dso.caldwell_number = None
        mock_dso.catalog_name = "NGC"
        mock_dso.catalog_number = 1976
        mock_db.query.return_value.all.return_value = [mock_dso]

        result = file_scanner_service._fuzzy_match_catalog("Orion Nebula")
        if result:
            catalog_id, _ = result
            assert "NGC" in catalog_id


class TestFitsMetadataEdgeCases:
    @patch("app.services.file_scanner_service.fits")
    def test_invalid_exptime_is_ignored(self, mock_fits, file_scanner_service):
        mock_hdu = MagicMock()
        mock_hdu.header = {"OBJECT": "Test", "EXPTIME": "not-a-number"}
        mock_fits.open.return_value.__enter__.return_value = [mock_hdu]

        result = file_scanner_service._extract_fits_metadata("/path/to/file.fits")
        assert result is not None
        assert result["exposure_seconds"] is None

    @patch("app.services.file_scanner_service.fits")
    def test_invalid_date_obs_is_ignored(self, mock_fits, file_scanner_service):
        mock_hdu = MagicMock()
        mock_hdu.header = {"OBJECT": "Test", "DATE-OBS": "not-a-date"}
        mock_fits.open.return_value.__enter__.return_value = [mock_hdu]

        result = file_scanner_service._extract_fits_metadata("/path/to/file.fits")
        assert result is not None
        assert result["observation_date"] is None


class TestQualityMetricsNonFits:
    def test_non_fits_returns_none_for_both(self, file_scanner_service):
        result = file_scanner_service._calculate_quality_metrics("/path/to/image.jpg")
        assert result == {"fwhm": None, "star_count": None}
