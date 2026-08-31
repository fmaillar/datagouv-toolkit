import json

import pytest

from datagouv_toolkit import cli


def test_resources_parser_maps_handoff_arguments() -> None:
    args = cli.build_parser().parse_args(
        [
            "resources",
            "transport",
            "--first",
            "--format",
            "csv",
            "--resource-title",
            "2024",
            "--manifest",
        ]
    )

    assert args.dataset == "transport"
    assert args.first is True
    assert args.resource_format == "csv"
    assert args.resource_title == "2024"
    assert args.manifest is True
    assert args.urls is False
    assert args.json is False


def test_resources_output_modes_are_mutually_exclusive() -> None:
    parser = cli.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "resources",
                "transport",
                "--urls",
                "--manifest",
            ]
        )


def test_build_resource_manifest() -> None:
    manifest = cli.build_resource_manifest(
        {
            "id": "dataset-id",
            "title": "Example dataset",
        },
        [
            {
                "id": "resource-id",
                "title": "data.csv",
                "format": "CSV",
                "filesize": 1234,
                "url": "https://example.test/data.csv",
                "extra": "ignored",
            }
        ],
    )

    assert manifest == {
        "dataset": {
            "id": "dataset-id",
            "title": "Example dataset",
        },
        "resources": [
            {
                "id": "resource-id",
                "title": "data.csv",
                "format": "CSV",
                "filesize": 1234,
                "url": "https://example.test/data.csv",
            }
        ],
    }


def test_command_resources_urls(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli.datagouv,
        "resolve_dataset",
        lambda *args, **kwargs: {
            "id": "dataset-id",
            "title": "Example",
            "resources": [
                {
                    "id": "a",
                    "title": "2024.csv",
                    "format": "csv",
                    "url": "https://example.test/2024.csv",
                },
                {
                    "id": "b",
                    "title": "2023.csv",
                    "format": "csv",
                    "url": "https://example.test/2023.csv",
                },
            ],
        },
    )

    args = cli.build_parser().parse_args(
        [
            "resources",
            "example",
            "--first",
            "--format",
            "csv",
            "--resource-title",
            "2024",
            "--urls",
        ]
    )

    cli.command_resources(args)

    assert capsys.readouterr().out.strip() == "https://example.test/2024.csv"


def test_command_resources_urls_reject_missing_urls(monkeypatch) -> None:
    monkeypatch.setattr(
        cli.datagouv,
        "resolve_dataset",
        lambda *args, **kwargs: {
            "title": "Example",
            "resources": [
                {
                    "id": "a",
                    "title": "data.csv",
                    "format": "csv",
                    "url": None,
                }
            ],
        },
    )

    args = cli.build_parser().parse_args(
        [
            "resources",
            "example",
            "--urls",
        ]
    )

    with pytest.raises(ValueError, match="Aucune URL disponible"):
        cli.command_resources(args)


def test_command_resources_manifest(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli.datagouv,
        "resolve_dataset",
        lambda *args, **kwargs: {
            "id": "dataset-id",
            "title": "Example",
            "resources": [
                {
                    "id": "resource-id",
                    "title": "data.csv",
                    "format": "csv",
                    "filesize": 42,
                    "url": "https://example.test/data.csv",
                }
            ],
        },
    )

    args = cli.build_parser().parse_args(
        [
            "resources",
            "example",
            "--manifest",
        ]
    )

    cli.command_resources(args)
    payload = json.loads(capsys.readouterr().out)

    assert payload["dataset"] == {
        "id": "dataset-id",
        "title": "Example",
    }
    assert payload["resources"][0]["url"] == "https://example.test/data.csv"
    assert payload["resources"][0]["filesize"] == 42


def test_command_resources_rejects_empty_selection(monkeypatch) -> None:
    monkeypatch.setattr(
        cli.datagouv,
        "resolve_dataset",
        lambda *args, **kwargs: {
            "title": "Example",
            "resources": [],
        },
    )

    args = cli.build_parser().parse_args(["resources", "example", "--manifest"])

    with pytest.raises(ValueError, match="Aucune ressource correspondante"):
        cli.command_resources(args)
