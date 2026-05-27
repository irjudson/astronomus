"""Tests for ProcessingService."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.processing_service import ProcessingService


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    return session


@pytest.fixture
def mock_file():
    f = Mock()
    f.id = 1
    f.file_path = "/data/test.fits"
    return f


@pytest.fixture
def mock_pipeline():
    p = Mock()
    p.id = 2
    p.name = "Basic Pipeline"
    p.pipeline_steps = [{"step": "histogram_stretch", "params": {}}]
    return p


@pytest.fixture
def mock_job():
    j = Mock()
    j.id = 3
    j.status = "pending"
    j.started_at = None
    j.completed_at = None
    j.progress_percent = 0
    j.current_step = ""
    j.processing_log = ""
    j.output_files = []
    j.gpu_used = False
    j.error_message = None
    return j


@patch("app.services.processing_service.DirectProcessor")
@patch("app.services.processing_service.Path.mkdir")
def test_init_creates_processor_and_dir(mock_mkdir, mock_dp_cls):
    svc = ProcessingService()
    assert svc.processor is mock_dp_cls.return_value
    mock_mkdir.assert_called()


@patch("app.services.processing_service.DirectProcessor")
@patch("app.services.processing_service.Path.mkdir")
@patch("app.services.processing_service.SessionLocal")
@pytest.mark.asyncio
async def test_execute_pipeline_file_not_found_in_db(mock_session_local, mock_mkdir, mock_dp_cls):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_session_local.return_value = mock_db

    svc = ProcessingService()
    with pytest.raises(Exception):
        await svc.execute_pipeline(file_id=999, pipeline_id=1, job_id=1)
    mock_db.close.assert_called_once()


@patch("app.services.processing_service.DirectProcessor")
@patch("app.services.processing_service.Path.mkdir")
@patch("app.services.processing_service.SessionLocal")
@pytest.mark.asyncio
async def test_execute_pipeline_input_file_missing(
    mock_session_local, mock_mkdir, mock_dp_cls, mock_file, mock_pipeline, mock_job
):
    mock_db = MagicMock()

    def query_side_effect(model_cls):
        q = MagicMock()
        from app.models.processing_models import ProcessingFile, ProcessingJob, ProcessingPipeline

        if model_cls is ProcessingFile:
            q.filter.return_value.first.return_value = mock_file
        elif model_cls is ProcessingPipeline:
            q.filter.return_value.first.return_value = mock_pipeline
        elif model_cls is ProcessingJob:
            q.filter.return_value.first.return_value = mock_job
        return q

    mock_db.query.side_effect = query_side_effect
    mock_session_local.return_value = mock_db

    # input file does not exist — the job should end up "failed" and an exception raised
    with patch("app.services.processing_service.Path.exists", return_value=False):
        with pytest.raises(Exception):
            svc = ProcessingService()
            await svc.execute_pipeline(file_id=1, pipeline_id=2, job_id=3)

    assert mock_job.status == "failed"


@patch("app.services.processing_service.shutil.copy2")
@patch("app.services.processing_service.DirectProcessor")
@patch("app.services.processing_service.Path.mkdir")
@patch("app.services.processing_service.SessionLocal")
@pytest.mark.asyncio
async def test_execute_pipeline_happy_path(
    mock_session_local, mock_mkdir, mock_dp_cls, mock_copy2, mock_file, mock_pipeline, mock_job
):
    mock_db = MagicMock()

    def query_side_effect(model_cls):
        q = MagicMock()
        from app.models.processing_models import ProcessingFile, ProcessingJob, ProcessingPipeline

        if model_cls is ProcessingFile:
            q.filter.return_value.first.return_value = mock_file
        elif model_cls is ProcessingPipeline:
            q.filter.return_value.first.return_value = mock_pipeline
        elif model_cls is ProcessingJob:
            q.filter.return_value.first.return_value = mock_job
        return q

    mock_db.query.side_effect = query_side_effect
    mock_session_local.return_value = mock_db

    # Processor returns one output file that "exists"
    output_path = Path("/app/data/processing/job_3/outputs/test.jpg")
    mock_dp_cls.return_value.process_fits.return_value = [output_path]

    with (
        patch("app.services.processing_service.Path.exists", return_value=True),
        patch.object(Path, "is_file", return_value=True),
        patch.object(Path, "suffix", new_callable=lambda: property(lambda self: ".jpg")),
    ):
        svc = ProcessingService()
        result = await svc.execute_pipeline(file_id=1, pipeline_id=2, job_id=3)

    assert result["status"] == "complete"
    assert result["gpu_used"] is False
    assert mock_job.status == "complete"
    mock_db.close.assert_called_once()


@patch("app.services.processing_service.DirectProcessor")
@patch("app.services.processing_service.Path.mkdir")
@patch("app.services.processing_service.SessionLocal")
@pytest.mark.asyncio
async def test_execute_pipeline_processor_exception_sets_failed(
    mock_session_local, mock_mkdir, mock_dp_cls, mock_file, mock_pipeline, mock_job
):
    mock_db = MagicMock()

    def query_side_effect(model_cls):
        q = MagicMock()
        from app.models.processing_models import ProcessingFile, ProcessingJob, ProcessingPipeline

        if model_cls is ProcessingFile:
            q.filter.return_value.first.return_value = mock_file
        elif model_cls is ProcessingPipeline:
            q.filter.return_value.first.return_value = mock_pipeline
        elif model_cls is ProcessingJob:
            q.filter.return_value.first.return_value = mock_job
        return q

    mock_db.query.side_effect = query_side_effect
    mock_session_local.return_value = mock_db

    mock_dp_cls.return_value.process_fits.side_effect = RuntimeError("boom")

    with patch("app.services.processing_service.Path.exists", return_value=True):
        svc = ProcessingService()
        with pytest.raises(Exception):
            await svc.execute_pipeline(file_id=1, pipeline_id=2, job_id=3)

    assert mock_job.status == "failed"
    mock_db.close.assert_called_once()


@patch("app.services.processing_service.DirectProcessor")
@patch("app.services.processing_service.Path.mkdir")
@patch("app.services.processing_service.SessionLocal")
@pytest.mark.asyncio
async def test_cancel_job_not_found_returns_false(mock_session_local, mock_mkdir, mock_dp_cls):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_session_local.return_value = mock_db

    svc = ProcessingService()
    result = await svc.cancel_job(job_id=9999)

    assert result is False
    mock_db.close.assert_called_once()


@patch("app.services.processing_service.DirectProcessor")
@patch("app.services.processing_service.Path.mkdir")
@patch("app.services.processing_service.SessionLocal")
@pytest.mark.asyncio
async def test_cancel_job_running_job_sets_cancelled(mock_session_local, mock_mkdir, mock_dp_cls):
    mock_db = MagicMock()
    mock_job = Mock()
    mock_job.id = 1
    mock_job.status = "running"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_job
    mock_session_local.return_value = mock_db

    svc = ProcessingService()
    result = await svc.cancel_job(job_id=1)

    assert result is True
    assert mock_job.status == "cancelled"
    assert mock_job.completed_at is not None
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()


@patch("app.services.processing_service.shutil.rmtree")
@patch("app.services.processing_service.DirectProcessor")
@patch("app.services.processing_service.Path.mkdir")
def test_cleanup_old_jobs_removes_old_dirs(mock_mkdir, mock_dp_cls, mock_rmtree):
    svc = ProcessingService()

    # Create mock job directories
    old_dir = MagicMock(spec=Path)
    old_dir.is_dir.return_value = True
    old_dir.stat.return_value.st_mtime = 0  # epoch — definitely old

    new_dir = MagicMock(spec=Path)
    new_dir.is_dir.return_value = True
    import time

    new_dir.stat.return_value.st_mtime = time.time()  # now — not old

    with patch.object(Path, "glob", return_value=[old_dir, new_dir]):
        svc.cleanup_old_jobs(days=7)

    mock_rmtree.assert_called_once_with(old_dir, ignore_errors=True)


@patch("app.services.processing_service.shutil.rmtree")
@patch("app.services.processing_service.DirectProcessor")
@patch("app.services.processing_service.Path.mkdir")
def test_cleanup_old_jobs_skips_files(mock_mkdir, mock_dp_cls, mock_rmtree):
    svc = ProcessingService()

    # Non-directory entry — should be skipped
    not_a_dir = MagicMock(spec=Path)
    not_a_dir.is_dir.return_value = False
    not_a_dir.stat.return_value.st_mtime = 0

    with patch.object(Path, "glob", return_value=[not_a_dir]):
        svc.cleanup_old_jobs(days=7)

    mock_rmtree.assert_not_called()
