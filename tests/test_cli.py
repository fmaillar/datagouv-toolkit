from __future__ import annotations

from pathlib import Path

import cli


def test_build_parser_exposes_unified_commands():
    parser = cli.build_parser()

    commands = {
        action.dest: set(action.choices)
        for action in parser._actions
        if hasattr(action, "choices") and isinstance(action.choices, dict)
    }

    assert commands["command"] == {
        "search",
        "dataset",
        "resources",
        "metadata",
        "stats",
        "inspect",
        "organization",
        "download",
        "workflow",
        "inspect-csv",
        "catalog-stats",
    }


def test_download_parser_maps_arguments():
    args = cli.build_parser().parse_args(
        [
            "download",
            "accidents corporels",
            "--producer",
            "Ministère de l'intérieur",
            "--title",
            "BAAC",
            "--format",
            "csv",
            "--resource-title",
            "Caract_2024",
            "--output",
            "data",
            "--overwrite",
        ]
    )

    assert args.dataset == "accidents corporels"
    assert args.producer == "Ministère de l'intérieur"
    assert args.title == "BAAC"
    assert args.resource_format == "csv"
    assert args.resource_title == "Caract_2024"
    assert args.output == Path("data")
    assert args.overwrite is True
    assert args.func is cli.command_download


def test_workflow_parser_maps_arguments():
    args = cli.build_parser().parse_args(
        [
            "workflow",
            "accidents corporels",
            "--output",
            "data",
            "--audit-dir",
            "audits",
            "--no-audit",
        ]
    )

    assert args.output == Path("data")
    assert args.audit_dir == Path("audits")
    assert args.no_audit is True
    assert args.func is cli.command_workflow


def test_inspect_csv_parser_maps_arguments():
    args = cli.build_parser().parse_args(
        [
            "inspect-csv",
            "sample.csv",
            "--encoding",
            "utf-8",
            "--sep",
            ";",
            "--nrows",
            "100",
            "--low-cardinality",
            "10",
        ]
    )

    assert args.file == Path("sample.csv")
    assert args.encoding == "utf-8"
    assert args.sep == ";"
    assert args.nrows == 100
    assert args.low_cardinality == 10
    assert args.func is cli.command_inspect_csv


def test_catalog_stats_parser_maps_arguments():
    args = cli.build_parser().parse_args(
        [
            "catalog-stats",
            "énergie",
            "--snapshot",
            "snapshot/2026-08-25",
            "--license",
            "fr-lo-2.0",
            "--frequency",
            "annual",
            "--format",
            "csv",
            "--top",
            "5",
        ]
    )

    assert args.query == "énergie"
    assert args.snapshot == Path("snapshot/2026-08-25")
    assert args.license_name == "fr-lo-2.0"
    assert args.frequency == "annual"
    assert args.resource_format == "csv"
    assert args.top == 5
    assert args.func is cli.command_catalog_stats


def test_command_download_delegates(monkeypatch, tmp_path):
    dataset = {"title": "Dataset", "resources": [{"title": "data.csv"}]}
    selected = [{"title": "data.csv"}]
    calls = {}

    monkeypatch.setattr(cli.datagouv, "resolve_dataset", lambda *args, **kwargs: dataset)
    monkeypatch.setattr(cli, "select_resources", lambda *args, **kwargs: selected)

    def fake_download(resources, output, *, overwrite=False):
        calls["resources"] = resources
        calls["output"] = output
        calls["overwrite"] = overwrite

    monkeypatch.setattr(cli, "download_resources", fake_download)

    args = cli.build_parser().parse_args(
        ["download", "dataset", "--output", str(tmp_path), "--overwrite"]
    )
    cli.command_download(args)

    assert calls == {
        "resources": selected,
        "output": tmp_path,
        "overwrite": True,
    }


def test_command_download_rejects_empty_selection(monkeypatch, tmp_path):
    monkeypatch.setattr(
        cli.datagouv,
        "resolve_dataset",
        lambda *args, **kwargs: {"title": "Dataset", "resources": []},
    )
    monkeypatch.setattr(cli, "select_resources", lambda *args, **kwargs: [])

    args = cli.build_parser().parse_args(
        ["download", "dataset", "--output", str(tmp_path)]
    )

    try:
        cli.command_download(args)
    except ValueError as exc:
        assert str(exc) == "Aucune ressource correspondante."
    else:
        raise AssertionError("ValueError attendu")


def test_command_workflow_delegates(monkeypatch, tmp_path):
    calls = {}

    def fake_workflow(dataset, output, **kwargs):
        calls["dataset"] = dataset
        calls["output"] = output
        calls.update(kwargs)

    monkeypatch.setattr(cli, "run_workflow", fake_workflow)

    args = cli.build_parser().parse_args(
        [
            "workflow",
            "dataset",
            "--output",
            str(tmp_path),
            "--format",
            "csv",
            "--audit-dir",
            str(tmp_path / "audits"),
        ]
    )
    cli.command_workflow(args)

    assert calls["dataset"] == "dataset"
    assert calls["output"] == tmp_path
    assert calls["resource_format"] == "csv"
    assert calls["audit_csv"] is True
    assert calls["audit_dir"] == tmp_path / "audits"


def test_command_inspect_csv_delegates(monkeypatch, tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("a,b\n1,2\n", encoding="utf-8")
    calls = {}

    def fake_inspect(path, **kwargs):
        calls["path"] = path
        calls.update(kwargs)

    monkeypatch.setattr(cli, "inspect_csv", fake_inspect)

    args = cli.build_parser().parse_args(["inspect-csv", str(csv_path)])
    cli.command_inspect_csv(args)

    assert calls["path"] == csv_path
    assert calls["encoding"] is None
    assert calls["separator"] is None


def test_command_inspect_csv_rejects_missing_file(tmp_path):
    args = cli.build_parser().parse_args(
        ["inspect-csv", str(tmp_path / "missing.csv")]
    )

    try:
        cli.command_inspect_csv(args)
    except FileNotFoundError as exc:
        assert "Fichier introuvable" in str(exc)
    else:
        raise AssertionError("FileNotFoundError attendu")


def test_catalog_stats_rejects_non_positive_top(tmp_path):
    args = cli.build_parser().parse_args(
        ["catalog-stats", "test", "--snapshot", str(tmp_path), "--top", "0"]
    )

    try:
        cli.command_catalog_stats(args)
    except ValueError as exc:
        assert str(exc) == "--top doit être strictement positif"
    else:
        raise AssertionError("ValueError attendu")

def test_search_parser_maps_arguments():
    args = cli.build_parser().parse_args(
        ["search", "transport", "--limit", "7"]
    )

    assert args.command == "search"
    assert args.query == "transport"
    assert args.limit == 7
    assert args.func is cli.datagouv.command_search


def test_dataset_parsers_map_arguments():
    expected = {
        "dataset": cli.datagouv.command_dataset,
        "resources": cli.datagouv.command_resources,
        "stats": cli.datagouv.command_stats,
        "inspect": cli.datagouv.command_inspect,
        "metadata": cli.datagouv.command_metadata,
    }

    for command, func in expected.items():
        args = cli.build_parser().parse_args(
            [
                command,
                "example",
                "--producer",
                "Example Org",
                "--title",
                "Example",
            ]
        )

        assert args.command == command
        assert args.dataset == "example"
        assert args.producer == "Example Org"
        assert args.title == "Example"
        assert args.func is func


def test_organization_parser_maps_arguments():
    args = cli.build_parser().parse_args(
        ["organization", "abc"]
    )

    assert args.organization_id == "abc"
    assert args.func is cli.datagouv.command_organization


def test_main_success(monkeypatch):
    called = []

    monkeypatch.setattr(
        cli,
        "build_parser",
        lambda: type(
            "Parser",
            (),
            {
                "parse_args": lambda self: type(
                    "Args",
                    (),
                    {
                        "func": lambda self, args: called.append(True),
                    },
                )()
            },
        )(),
    )

    assert cli.main() == 0
    assert called == [True]
