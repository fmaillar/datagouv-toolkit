import json
from pathlib import Path

from datagouv_toolkit import cli
from datagouv_toolkit import download_resources as download_module


def test_download_parser_accepts_json(tmp_path: Path) -> None:
    args = cli.build_parser().parse_args(
        [
            "download",
            "example",
            "--output",
            str(tmp_path),
            "--json",
        ]
    )

    assert args.json is True
    assert args.func is cli.command_download


def test_command_download_json(monkeypatch, tmp_path: Path, capsys) -> None:
    dataset = {
        "id": "dataset-id",
        "title": "Example dataset",
        "resources": [],
    }
    resource = {
        "id": "resource-id",
        "title": "data.csv",
        "format": "csv",
    }
    calls = {}

    monkeypatch.setattr(
        cli.datagouv,
        "resolve_dataset",
        lambda *args, **kwargs: dataset,
    )
    monkeypatch.setattr(
        cli,
        "select_resources",
        lambda *args, **kwargs: [resource],
    )

    def fake_download(
        resources,
        output,
        *,
        overwrite=False,
        progress=True,
    ):
        calls["resources"] = resources
        calls["output"] = output
        calls["overwrite"] = overwrite
        calls["progress"] = progress
        return [
            {
                "resource": resource,
                "path": output / "data.csv",
                "downloaded": True,
            }
        ]

    monkeypatch.setattr(cli, "download_resources", fake_download)

    args = cli.build_parser().parse_args(
        [
            "download",
            "example",
            "--output",
            str(tmp_path),
            "--overwrite",
            "--json",
        ]
    )

    cli.command_download(args)

    payload = json.loads(capsys.readouterr().out)

    assert calls == {
        "resources": [resource],
        "output": tmp_path,
        "overwrite": True,
        "progress": False,
    }
    assert payload["dataset"] == {
        "id": "dataset-id",
        "title": "Example dataset",
    }
    assert payload["destination"] == str(tmp_path.resolve())
    assert payload["resources"] == [
        {
            "resource": resource,
            "path": str((tmp_path / "data.csv").resolve()),
            "downloaded": True,
        }
    ]


def test_download_resources_can_disable_progress(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    resource = {
        "title": "data.csv",
        "url": "https://example.test/data.csv",
    }

    monkeypatch.setattr(
        download_module,
        "download_resource",
        lambda resource, destination, *, overwrite=False: True,
    )

    results = download_module.download_resources(
        [resource],
        tmp_path,
        progress=False,
    )

    assert capsys.readouterr().out == ""
    assert results == [
        {
            "resource": resource,
            "path": tmp_path / "data.csv",
            "downloaded": True,
        }
    ]
