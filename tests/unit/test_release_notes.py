from pathlib import Path
from subprocess import CalledProcessError

import pytest

from scripts.release_notes import categorize, main, render


def test_categorize_conventional_and_unknown_commits():
    assert categorize("feat(auth): add login") == ("Features", "add login")
    assert categorize("fix: handle timeout") == ("Fixes", "handle timeout")
    assert categorize("miscellaneous change") == ("Other", "miscellaneous change")


def test_render_groups_commits_and_includes_metadata():
    notes = render(
        ["feat: add search", "fix: handle timeout", "chore: update tooling"],
        "1.2.0",
        "abc123",
        "2026-09-13T00:00:00Z",
    )
    assert "# Release 1.2.0" in notes
    assert "## Features" in notes
    assert "- add search" in notes
    assert "## Fixes" in notes
    assert "- chore: update tooling" not in notes


def test_release_notes_main_writes_file(tmp_path, monkeypatch):
    output = Path(tmp_path) / "notes.md"
    monkeypatch.setattr(
        "scripts.release_notes.git_subjects", lambda from_ref, to_ref: ["feat: new thing"]
    )
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: type("Result", (), {"stdout": "deadbeef\n"})(),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["release_notes.py", "--version", "1.0.0", "--output", str(output)],
    )
    assert main() == 0
    assert "deadbeef" in output.read_text()


def test_release_notes_main_rejects_wrong_arguments(monkeypatch):
    monkeypatch.setattr("sys.argv", ["release_notes.py", "--bad"])
    with pytest.raises(SystemExit):
        main()


def test_release_notes_main_reports_missing_git_ref(monkeypatch, tmp_path):
    def missing_ref(*args, **kwargs):
        raise CalledProcessError(128, args[0])

    monkeypatch.setattr("subprocess.run", missing_ref)
    monkeypatch.setattr(
        "sys.argv", ["release_notes.py", "--from-ref", "v0.1.0", "--output", str(tmp_path / "x")]
    )
    assert main() == 2
