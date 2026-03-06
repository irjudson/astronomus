"""Capture history database models."""

import enum
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class CaptureStatus(str, enum.Enum):
    """Canonical status values for CaptureHistory.status."""

    COMPLETE = "complete"
    NEEDS_MORE = "needs_more"
    NEEDS_MORE_DATA = "needs_more_data"  # Legacy alias (backend suggestion label)


class CaptureHistory(Base):
    """Aggregated capture statistics per catalog target."""

    __tablename__ = "capture_history"

    id = Column(Integer, primary_key=True)
    catalog_id = Column(String(50), unique=True, nullable=False, index=True)

    # Aggregate stats
    total_exposure_seconds = Column(Integer, default=0)
    total_frames = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    first_captured_at = Column(DateTime, nullable=True)
    last_captured_at = Column(DateTime, nullable=True)

    # User-controlled status: None = not reviewed, 'complete', 'needs_more'
    # Constrained to CaptureStatus values via CHECK constraint (see migration).
    status = Column(String(20), nullable=True)
    suggested_status = Column(String(20), nullable=True)  # Auto-calculated by service

    # Quality metrics (from best capture)
    best_fwhm = Column(Float, nullable=True)
    best_star_count = Column(Integer, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # OutputFiles are linked by catalog_id (not a hard FK — files may be scanned
    # before CaptureHistory exists).  viewonly=True prevents accidental mutations
    # through this relationship.
    output_files = relationship(
        "OutputFile",
        primaryjoin="CaptureHistory.catalog_id == foreign(OutputFile.catalog_id)",
        viewonly=True,
        lazy="select",
    )


class OutputFile(Base):
    """Links captured files to targets and executions."""

    __tablename__ = "output_files"

    id = Column(Integer, primary_key=True)
    file_path = Column(String(500), nullable=False, unique=True, index=True)
    file_type = Column(String(20), nullable=False)  # raw_fits, stacked_fits, jpg, png, tiff
    file_size_bytes = Column(BigInteger, nullable=False)

    # Target linking (no hard FK — files are scanned independently of capture tracking)
    catalog_id = Column(String(50), nullable=False, index=True)
    catalog_id_confidence = Column(Float, default=1.0)  # Fuzzy match score

    # Execution linking (nullable - files may exist before tracking)
    execution_id = Column(Integer, ForeignKey("telescope_executions.id"), nullable=True)
    execution_target_id = Column(Integer, ForeignKey("telescope_execution_targets.id"), nullable=True)

    # FITS metadata
    exposure_seconds = Column(Integer, nullable=True)
    filter_name = Column(String(20), nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    gain = Column(Integer, nullable=True)

    # Quality metrics
    fwhm = Column(Float, nullable=True)
    star_count = Column(Integer, nullable=True)

    # Timestamps
    observation_date = Column(DateTime, nullable=True)  # From FITS DATE-OBS
    created_at = Column(DateTime, default=datetime.utcnow)

    capture_history = relationship(
        "CaptureHistory",
        primaryjoin="OutputFile.catalog_id == foreign(CaptureHistory.catalog_id)",
        viewonly=True,
        lazy="select",
    )
