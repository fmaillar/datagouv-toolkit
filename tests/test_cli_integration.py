from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_datagouv(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src = str(PROJECT_ROOT / "src")
    env["PYTHONPATH"] = (
        src
        if not env.get("PYTHONPATH")
        else os.pathsep.join((src, env["PYTHONPATH"]))
    )
    return subprocess.run(
        [sys.executable, "-m", "datagouv_toolkit.cli", *args],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_help_from_module_entrypoint() -> None:
    result = run_datagouv("--help")

    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert "download" in result.stdout
    assert "workflow" in result.stdout
    assert result.stderr == ""


def test_download_json_from_cli_entrypoint(tmp_path: Path) -> None:
    output = tmp_path / "downloads"

    result = run_datagouv(
        "download",
        "definitely-not-a-real-datagouv-dataset-id-for-integration-test",
        "--output",
        str(output),
        "--json",
    )

    # The subprocess must exercise the real command-line entry point. Network
    # resolution is intentionally allowed to fail: this test verifies that the
    # CLI converts that failure into a controlled non-zero exit instead of a
    # traceback.
    assert result.returncode in {0, 1}
    assert "Traceback" not in result.stderr
    if result.returncode == 0:
        payload = json.loads(result.stdout)
        assert set(payload) == {"dataset", "destination", "resources"}
    else:
        assert result.stderr.startswith(("Erreur HTTP :", "Erreur réseau :", "Erreur :"))


def test_workflow_help_exposes_json_option() -> None:
    result = run_datagouv("workflow", "--help")

    assert result.returncode == 0
    assert "--json" in result.stdout
    assert "--audit-dir" in result.stdout
    assert result.stderr == ""


@pytest.mark.parametrize("command", ["download", "workflow"])
def test_json_commands_require_output(command: str) -> None:
    result = run_datagouv(command, "example", "--json")

    assert result.returncode == 2
    assert "--output" in result.stderr
    assert "Traceback" not in result.stderr
