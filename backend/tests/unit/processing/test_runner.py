"""Tests for PipelineRunner and main() in app/processing/runner.py."""

import json
from unittest.mock import patch

import pytest

BASE_CONFIG = {
    "job_id": "42",
    "input_file": "/data/input.fits",
    "output_dir": "/data/output",
    "working_dir": "/data/working",
    "pipeline_steps": [],
}


# ---------------------------------------------------------------------------
# PipelineRunner.__init__
# ---------------------------------------------------------------------------


class TestPipelineRunnerInit:
    def test_stores_config_fields(self):
        with patch("app.processing.runner.gpu_ops") as mock_gpu, patch("app.processing.runner.Path.mkdir"):
            mock_gpu.check_gpu_available.return_value = {"available": False}
            from app.processing.runner import PipelineRunner

            runner = PipelineRunner(BASE_CONFIG.copy())
        assert runner.job_id == "42"
        assert runner.input_file == "/data/input.fits"

    def test_directories_created(self):
        with (
            patch("app.processing.runner.gpu_ops") as mock_gpu,
            patch("app.processing.runner.Path.mkdir") as mock_mkdir,
        ):
            mock_gpu.check_gpu_available.return_value = {"available": False}
            from app.processing.runner import PipelineRunner

            PipelineRunner(BASE_CONFIG.copy())
        assert mock_mkdir.call_count >= 2

    def test_gpu_flag_true_when_available(self):
        with patch("app.processing.runner.gpu_ops") as mock_gpu, patch("app.processing.runner.Path.mkdir"):
            mock_gpu.check_gpu_available.return_value = {"available": True}
            from app.processing.runner import PipelineRunner

            runner = PipelineRunner(BASE_CONFIG.copy())
        assert runner.use_gpu is True

    def test_gpu_flag_false_when_unavailable(self):
        with patch("app.processing.runner.gpu_ops") as mock_gpu, patch("app.processing.runner.Path.mkdir"):
            mock_gpu.check_gpu_available.return_value = {"available": False}
            from app.processing.runner import PipelineRunner

            runner = PipelineRunner(BASE_CONFIG.copy())
        assert runner.use_gpu is False


# ---------------------------------------------------------------------------
# PipelineRunner.run
# ---------------------------------------------------------------------------


class TestPipelineRunnerRun:
    def _run_with_steps(self, steps, gpu_side_effects=None):
        config = BASE_CONFIG.copy()
        config["pipeline_steps"] = steps
        with patch("app.processing.runner.gpu_ops") as mock_gpu, patch("app.processing.runner.Path.mkdir"):
            mock_gpu.check_gpu_available.return_value = {"available": False}
            if gpu_side_effects:
                for attr, value in gpu_side_effects.items():
                    getattr(mock_gpu, attr).return_value = value
            from app.processing.runner import PipelineRunner

            runner = PipelineRunner(config)
            result = runner.run()
        return result, mock_gpu

    def test_empty_steps_returns_success(self):
        result, _ = self._run_with_steps([])
        assert result["status"] == "success"
        assert result["output_files"] == []

    def test_histogram_stretch_step_calls_gpu_ops(self):
        steps = [{"step": "histogram_stretch", "params": {"algorithm": "auto"}}]
        result, mock_gpu = self._run_with_steps(
            steps,
            gpu_side_effects={"histogram_stretch": "/data/working/stretched.fit"},
        )
        assert result["status"] == "success"
        mock_gpu.histogram_stretch.assert_called_once()

    def test_export_step_jpeg(self):
        steps = [{"step": "export", "params": {"format": "jpeg"}}]
        result, mock_gpu = self._run_with_steps(
            steps,
            gpu_side_effects={"export_image": "/data/output/final.jpg"},
        )
        assert result["status"] == "success"
        assert any("final.jpg" in f for f in result["output_files"])

    def test_export_step_tiff(self):
        steps = [{"step": "export", "params": {"format": "tiff"}}]
        result, _ = self._run_with_steps(steps)
        assert result["status"] == "success"
        assert any("final.tif" in f for f in result["output_files"])

    def test_export_step_png(self):
        steps = [{"step": "export", "params": {"format": "png"}}]
        result, _ = self._run_with_steps(steps)
        assert result["status"] == "success"
        assert any("final.png" in f for f in result["output_files"])

    def test_export_step_unknown_format_uses_extension(self):
        steps = [{"step": "export", "params": {"format": "raw"}}]
        result, _ = self._run_with_steps(steps)
        assert result["status"] == "success"
        assert any("final.raw" in f for f in result["output_files"])

    def test_unknown_step_is_skipped(self):
        steps = [{"step": "mystery_op", "params": {}}]
        result, _ = self._run_with_steps(steps)
        assert result["status"] == "success"

    def test_exception_returns_error_status(self):
        steps = [{"step": "histogram_stretch", "params": {}}]
        config = BASE_CONFIG.copy()
        config["pipeline_steps"] = steps
        with patch("app.processing.runner.gpu_ops") as mock_gpu, patch("app.processing.runner.Path.mkdir"):
            mock_gpu.check_gpu_available.return_value = {"available": False}
            mock_gpu.histogram_stretch.side_effect = RuntimeError("GPU exploded")
            from app.processing.runner import PipelineRunner

            runner = PipelineRunner(config)
            result = runner.run()
        assert result["status"] == "error"
        assert "GPU exploded" in result["error"]

    def test_multiple_steps_chained(self):
        steps = [
            {"step": "histogram_stretch", "params": {}},
            {"step": "export", "params": {"format": "jpeg"}},
        ]
        config = BASE_CONFIG.copy()
        config["pipeline_steps"] = steps
        with patch("app.processing.runner.gpu_ops") as mock_gpu, patch("app.processing.runner.Path.mkdir"):
            mock_gpu.check_gpu_available.return_value = {"available": False}
            mock_gpu.histogram_stretch.return_value = "/data/working/stretched.fit"
            mock_gpu.export_image.return_value = "/data/output/final.jpg"
            from app.processing.runner import PipelineRunner

            runner = PipelineRunner(config)
            result = runner.run()
        assert result["status"] == "success"
        mock_gpu.histogram_stretch.assert_called_once()
        mock_gpu.export_image.assert_called_once()


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


class TestMain:
    def test_main_exits_1_when_config_missing(self):
        with (
            patch("sys.argv", ["runner.py", "--config", "/nonexistent.json"]),
            patch("app.processing.runner.Path.exists", return_value=False),
            patch("app.processing.runner.gpu_ops"),
            patch("app.processing.runner.Path.mkdir"),
            pytest.raises(SystemExit) as exc_info,
        ):
            # Force reimport to pick up fresh state
            import importlib

            import app.processing.runner as runner_mod

            importlib.reload(runner_mod)
            runner_mod.main()
        assert exc_info.value.code == 1

    def test_main_success_pipeline_writes_result(self, tmp_path):
        config = BASE_CONFIG.copy()
        config["output_dir"] = str(tmp_path)
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))

        with (
            patch("sys.argv", ["runner.py", "--config", str(config_file)]),
            patch("app.processing.runner.gpu_ops") as mock_gpu,
            patch("app.processing.runner.Path.mkdir"),
            patch("json.dump"),
            pytest.raises(SystemExit) as exc_info,
        ):
            mock_gpu.check_gpu_available.return_value = {"available": False}
            import importlib

            import app.processing.runner as runner_mod

            importlib.reload(runner_mod)
            runner_mod.main()
        assert exc_info.value.code == 0

    def test_main_exits_1_on_pipeline_error(self, tmp_path):
        config = BASE_CONFIG.copy()
        config["output_dir"] = str(tmp_path)
        config["pipeline_steps"] = [{"step": "histogram_stretch", "params": {}}]
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))

        with (
            patch("sys.argv", ["runner.py", "--config", str(config_file)]),
            patch("app.processing.runner.gpu_ops") as mock_gpu,
            patch("app.processing.runner.Path.mkdir"),
            patch("json.dump"),
            pytest.raises(SystemExit) as exc_info,
        ):
            mock_gpu.check_gpu_available.return_value = {"available": False}
            mock_gpu.histogram_stretch.side_effect = RuntimeError("boom")
            import importlib

            import app.processing.runner as runner_mod

            importlib.reload(runner_mod)
            runner_mod.main()
        assert exc_info.value.code == 1
