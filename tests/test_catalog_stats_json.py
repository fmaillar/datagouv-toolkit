from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from datagouv_toolkit import catalog_report, cli


def write_parquet(path: Path, rows: list[dict[str, object]]) -> None:
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path)


def make_snapshot(tmp_path: Path) -> Path:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()

    write_parquet(
        snapshot / "datasets.parquet",
        [
            {
                "id": "a",
                "title": "Transport Strasbourg",
                "description_short": "Bus et tram",
                "description": "",
                "tags": "transport,mobilite",
                "organization": "Eurométropole de Strasbourg",
                "owner": "",
                "license": "Licence Ouverte / Open Licence version 2.0",
                "frequency": "annual",
            },
            {
                "id": "b",
                "title": "Transport régional",
                "description_short": "Trains régionaux",
                "description": "",
                "tags": "transport,rail",
                "organization": "Région Grand Est",
                "owner": "",
                "license": "ODC-ODbL",
                "frequency": "weekly",
            },
        ],
    )
    write_parquet(
        snapshot / "resources.parquet",
        [
            {"dataset.id": "a", "format": "CSV", "filesize": "1024"},
            {"dataset.id": "a", "format": "JSON", "filesize": "2048"},
            {"dataset.id": "b", "format": "CSV", "filesize": ""},
        ],
    )
    return snapshot


def test_analyze_catalog_returns_structured_result(tmp_path: Path) -> None:
    snapshot = make_snapshot(tmp_path)

    result = catalog_report.analyze_catalog(
        "transport",
        snapshot,
        top=1,
    )

    assert result["query"] == "transport"
    assert result["datasets"] == {"catalog": 2, "matched": 2}
    assert result["resources"]["catalog"] == 3
    assert result["resources"]["matched"] == 3
    assert result["resources"]["known_size_bytes"] == 3072
    assert result["resources"]["unknown_size"] == 1
    assert result["rankings"]["formats"]["items"] == [
        {"value": "csv", "count": 2}
    ]
    assert result["rankings"]["formats"]["remaining_values"] == 1
    assert result["top"] == 1


def test_analyze_catalog_normalizes_filters(tmp_path: Path) -> None:
    snapshot = make_snapshot(tmp_path)

    result = catalog_report.analyze_catalog(
        "transport",
        snapshot,
        license_name="lov2",
        frequency="Annual",
        resource_format="CSV",
    )

    assert result["filters"] == {
        "license": "fr-lo-2.0",
        "frequency": "annual",
        "format": "csv",
    }
    assert result["datasets"]["matched"] == 1
    assert result["resources"]["matched"] == 1


def test_catalog_stats_parser_accepts_json() -> None:
    args = cli.build_parser().parse_args(
        [
            "catalog-stats",
            "transport",
            "--snapshot",
            "snapshot",
            "--json",
        ]
    )

    assert args.json is True
    assert args.func is cli.command_catalog_stats


def test_command_catalog_stats_json_is_parseable(
    tmp_path: Path,
    capsys,
) -> None:
    snapshot = make_snapshot(tmp_path)
    args = cli.build_parser().parse_args(
        [
            "catalog-stats",
            "transport",
            "--snapshot",
            str(snapshot),
            "--top",
            "2",
            "--json",
        ]
    )

    cli.command_catalog_stats(args)
    payload = json.loads(capsys.readouterr().out)

    assert payload["datasets"]["matched"] == 2
    assert payload["resources"]["matched"] == 3
    assert payload["rankings"]["formats"]["items"][0] == {
        "value": "csv",
        "count": 2,
    }


def test_compatibility_parser_accepts_json() -> None:
    args = catalog_report.build_parser().parse_args(
        [
            "transport",
            "--snapshot",
            "snapshot",
            "--json",
        ]
    )

    assert args.json is True

def test_human_catalog_report_preserves_remaining_values(
    tmp_path: Path,
    capsys,
) -> None:
    snapshot = make_snapshot(tmp_path)
    args = cli.build_parser().parse_args(
        [
            "catalog-stats",
            "transport",
            "--snapshot",
            str(snapshot),
            "--top",
            "1",
        ]
    )

    cli.command_catalog_stats(args)
    output = capsys.readouterr().out

    assert output.count("... 1 autre(s) valeur(s)") == 4

