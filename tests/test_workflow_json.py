import json
from pathlib import Path

from datagouv_toolkit import cli


def test_workflow_parser_accepts_json(tmp_path: Path) -> None:
    args = cli.build_parser().parse_args(
        [
            "workflow",
            "example",
            "--output",
            str(tmp_path),
            "--json",
        ]
    )

    assert args.json is True
    assert args.func is cli.command_workflow


def test_command_workflow_json(monkeypatch, tmp_path: Path, capsys) -> None:
    resource = {
        "id": "resource-id",
        "title": "data.csv",
        "format": "csv",
    }
    audit_path = tmp_path / "audits" / "data.csv.audit.txt"
    calls = {}

    def fake_workflow(dataset, output, **kwargs):
        calls["dataset"] = dataset
        calls["output"] = output
        calls.update(kwargs)
        return {
            "dataset": {
                "id": "dataset-id",
                "title": "Example dataset",
            },
            "destination": tmp_path.resolve(),
            "resources": [
                {
                    "resource": resource,
                    "path": tmp_path / "data.csv",
                    "downloaded": True,
                    "audited": True,
                    "audit_path": audit_path,
                }
            ],
        }

    monkeypatch.setattr(cli, "run_workflow", fake_workflow)

    args = cli.build_parser().parse_args(
        [
            "workflow",
            "example",
            "--output",
            str(tmp_path),
            "--audit-dir",
            str(tmp_path / "audits"),
            "--json",
        ]
    )

    cli.command_workflow(args)
    payload = json.loads(capsys.readouterr().out)

    assert calls["dataset"] == "example"
    assert calls["output"] == tmp_path
    assert calls["progress"] is False
    assert payload == {
        "dataset": {
            "id": "dataset-id",
            "title": "Example dataset",
        },
        "destination": str(tmp_path.resolve()),
        "resources": [
            {
                "resource": resource,
                "path": str((tmp_path / "data.csv").resolve()),
                "downloaded": True,
                "audited": True,
                "audit_path": str(audit_path.resolve()),
            }
        ],
    }


def test_command_workflow_json_without_audit_file(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    resource = {
        "id": "resource-id",
        "title": "data.json",
        "format": "json",
    }

    monkeypatch.setattr(
        cli,
        "run_workflow",
        lambda *args, **kwargs: {
            "dataset": {"id": "dataset-id", "title": "Example dataset"},
            "destination": tmp_path.resolve(),
            "resources": [
                {
                    "resource": resource,
                    "path": tmp_path / "data.json",
                    "downloaded": False,
                    "audited": False,
                    "audit_path": None,
                }
            ],
        },
    )

    args = cli.build_parser().parse_args(
        ["workflow", "example", "--output", str(tmp_path), "--json"]
    )
    cli.command_workflow(args)

    payload = json.loads(capsys.readouterr().out)
    assert payload["resources"][0]["downloaded"] is False
    assert payload["resources"][0]["audited"] is False
    assert payload["resources"][0]["audit_path"] is None
