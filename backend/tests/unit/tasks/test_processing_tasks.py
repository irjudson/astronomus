"""Unit tests for processing_tasks."""

from unittest.mock import MagicMock, patch


def test_cleanup_old_jobs_success():
    from app.tasks.processing_tasks import cleanup_old_jobs_task

    with patch("app.tasks.processing_tasks.ProcessingService") as mock_ps:
        mock_ps.return_value.cleanup_old_jobs.return_value = None
        result = cleanup_old_jobs_task(days=7)

    assert result == {"success": True, "days": 7}
    mock_ps.return_value.cleanup_old_jobs.assert_called_once_with(days=7)


def test_cleanup_old_jobs_exception_returns_false():
    from app.tasks.processing_tasks import cleanup_old_jobs_task

    with patch("app.tasks.processing_tasks.ProcessingService") as mock_ps:
        mock_ps.return_value.cleanup_old_jobs.side_effect = OSError("disk full")
        result = cleanup_old_jobs_task(days=7)

    assert result["success"] is False
    assert "disk full" in result["error"]


def test_process_file_delegates_to_service():
    from app.tasks.processing_tasks import process_file_task

    mock_loop = MagicMock()
    mock_loop.run_until_complete.return_value = {"status": "done"}

    with (
        patch("app.tasks.processing_tasks.ProcessingService") as mock_ps,
        patch("app.tasks.processing_tasks.asyncio.new_event_loop", return_value=mock_loop),
        patch("app.tasks.processing_tasks.asyncio.set_event_loop"),
    ):
        result = process_file_task(file_id=1, pipeline_id=2, job_id=3)

    assert result == {"status": "done"}
    mock_loop.run_until_complete.assert_called_once()
    mock_loop.close.assert_called_once()


def test_cancel_job_delegates_to_service():
    from app.tasks.processing_tasks import cancel_job_task

    mock_loop = MagicMock()
    mock_loop.run_until_complete.return_value = True

    with (
        patch("app.tasks.processing_tasks.ProcessingService") as mock_ps,
        patch("app.tasks.processing_tasks.asyncio.new_event_loop", return_value=mock_loop),
        patch("app.tasks.processing_tasks.asyncio.set_event_loop"),
    ):
        result = cancel_job_task(job_id=5)

    assert result is True
    mock_loop.run_until_complete.assert_called_once()
    mock_loop.close.assert_called_once()


def test_auto_process_raises_when_job_not_found():
    import pytest

    from app.tasks.processing_tasks import auto_process_task

    with patch("app.tasks.processing_tasks.SessionLocal") as mock_sl:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = db

        with pytest.raises(ValueError, match="not found"):
            auto_process_task(file_path="/tmp/test.fit", formats=["jpg"], job_id=99)


def test_auto_process_happy_path_sets_complete():
    from app.tasks.processing_tasks import auto_process_task

    mock_result = MagicMock()
    mock_result.output_files = [MagicMock()]
    mock_result.output_files[0].__str__ = lambda self: "/tmp/out.jpg"
    mock_result.input_shape = (1080, 1920)
    mock_result.params.stretch_factor = 1.5
    mock_result.params.black_point = 0.01
    mock_result.params.white_point = 0.99

    with (
        patch("app.tasks.processing_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.processing_tasks.AutoStretchService") as mock_as,
    ):
        db = MagicMock()
        job = MagicMock()
        job.status = "queued"
        db.query.return_value.filter.return_value.first.return_value = job
        mock_sl.return_value = db

        mock_as.return_value.auto_process.return_value = mock_result

        result = auto_process_task(file_path="/tmp/test.fit", formats=["jpg"], job_id=1)

    assert result["status"] == "complete"
    assert job.status == "complete"


def test_auto_process_marks_failed_on_exception():
    import pytest

    from app.tasks.processing_tasks import auto_process_task

    with (
        patch("app.tasks.processing_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.processing_tasks.AutoStretchService") as mock_as,
    ):
        db = MagicMock()
        job = MagicMock()
        job.status = "queued"
        db.query.return_value.filter.return_value.first.return_value = job
        mock_sl.return_value = db

        mock_as.return_value.auto_process.side_effect = RuntimeError("FITS corrupt")

        with pytest.raises(RuntimeError):
            auto_process_task(file_path="/tmp/bad.fit", formats=["jpg"], job_id=2)

    assert job.status == "failed"
    assert "FITS corrupt" in job.error_message


def test_stack_and_stretch_raises_when_job_not_found():
    import pytest

    from app.tasks.processing_tasks import stack_and_stretch_task

    with patch("app.tasks.processing_tasks.SessionLocal") as mock_sl:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = db

        with pytest.raises(ValueError, match="not found"):
            stack_and_stretch_task(
                folder_path="/tmp/subs", pattern="Light_*.fit", sigma=3.0, formats=["jpg"], job_id=77
            )


def test_stack_and_stretch_happy_path():
    from app.tasks.processing_tasks import stack_and_stretch_task

    stack_result = MagicMock()
    stack_result.num_frames = 10
    stack_result.stacked_file = MagicMock()
    stack_result.stacked_file.__str__ = lambda self: "/tmp/stacked.fit"
    stack_result.rejected_frames = 1
    stack_result.input_shape = (1080, 1920)
    stack_result.output_shape = (1080, 1920)

    stretch_result = MagicMock()
    stretch_result.output_files = []
    stretch_result.params.stretch_factor = 2.0
    stretch_result.params.black_point = 0.02
    stretch_result.params.white_point = 0.98

    with (
        patch("app.tasks.processing_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.processing_tasks.StackingService") as mock_ss,
        patch("app.tasks.processing_tasks.AutoStretchService") as mock_as,
    ):
        db = MagicMock()
        job = MagicMock()
        job.status = "queued"
        db.query.return_value.filter.return_value.first.return_value = job
        mock_sl.return_value = db

        mock_ss.return_value.stack_folder.return_value = stack_result
        mock_as.return_value.auto_process.return_value = stretch_result

        result = stack_and_stretch_task(
            folder_path="/tmp/subs", pattern="Light_*.fit", sigma=3.0, formats=["jpg"], job_id=10
        )

    assert result["status"] == "complete"
    assert result["num_frames"] == 10
    assert job.status == "complete"


def test_stack_and_stretch_marks_failed_on_exception():
    import pytest

    from app.tasks.processing_tasks import stack_and_stretch_task

    with (
        patch("app.tasks.processing_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.processing_tasks.StackingService") as mock_ss,
    ):
        db = MagicMock()
        job = MagicMock()
        job.status = "queued"
        db.query.return_value.filter.return_value.first.return_value = job
        mock_sl.return_value = db

        mock_ss.return_value.stack_folder.side_effect = IOError("no frames found")

        with pytest.raises(IOError):
            stack_and_stretch_task(
                folder_path="/tmp/empty", pattern="Light_*.fit", sigma=3.0, formats=["jpg"], job_id=11
            )

    assert job.status == "failed"
    assert "no frames found" in job.error_message
