from pathlib import Path

import pytest

from loadtest.config import LoadTestConfig
from scripts.check_load_test import main


def test_loadtest_config_defaults(monkeypatch):
    monkeypatch.delenv("LOADTEST_TARGET_URL", raising=False)
    monkeypatch.delenv("LOADTEST_SOURCE_ID", raising=False)
    config = LoadTestConfig.from_env()
    assert config.target_url == "http://localhost:8000"
    assert config.source_id is None
    assert config.wait_min == 1


def test_loadtest_config_reads_environment(monkeypatch):
    monkeypatch.setenv("LOADTEST_TARGET_URL", "https://staging.example/")
    monkeypatch.setenv("LOADTEST_SOURCE_ID", "source-1")
    monkeypatch.setenv("LOADTEST_WAIT_MIN", "2")
    monkeypatch.setenv("LOADTEST_WAIT_MAX", "4")
    config = LoadTestConfig.from_env()
    assert config.target_url == "https://staging.example"
    assert config.source_id == "source-1"
    assert (config.wait_min, config.wait_max) == (2, 4)


def test_loadtest_config_rejects_invalid_wait_range(monkeypatch):
    monkeypatch.setenv("LOADTEST_WAIT_MIN", "4")
    monkeypatch.setenv("LOADTEST_WAIT_MAX", "2")
    with pytest.raises(ValueError, match="greater than or equal"):
        LoadTestConfig.from_env()


def test_loadtest_threshold_checker(tmp_path, monkeypatch):
    stats = Path(tmp_path) / "stats.csv"
    stats.write_text("Name,Failure%,95%\nAggregated,0.0,250\n")
    monkeypatch.setattr("sys.argv", ["check_load_test.py", str(stats), "0", "500"])
    assert main() == 0

    monkeypatch.setattr("sys.argv", ["check_load_test.py", str(stats), "0", "100"])
    assert main() == 1


def test_loadtest_threshold_checker_reports_bad_arguments(monkeypatch):
    monkeypatch.setattr("sys.argv", ["check_load_test.py"])
    assert main() == 2
