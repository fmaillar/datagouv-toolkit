from __future__ import annotations

import json
from pathlib import Path

from datagouv_toolkit import cli
from datagouv_toolkit.inspect_csv import analyze_csv, format_csv_audit


def make_csv(tmp_path: Path) -> Path:
    path = tmp_path / "sample.csv"
    path.write_text(
        "id;category;value\n1;a;10\n2;a;20\n3;b;30\n",
        encoding="utf-8",
    )
    return path


def test_analyze_csv_returns_structured_audit(tmp_path: Path) -> None:
    path = make_csv(tmp_path)

    audit = analyze_csv(path, low_cardinality=2)

    assert audit["file"]["path"] == str(path.resolve())
    assert audit["file"]["rows"] == 3
    assert audit["file"]["columns"] == 3
    assert audit["file"]["separator"] == ";"
    assert audit["duplicate_rows"] == 0
    assert audit["candidate_keys"] == ["id", "value"]
    assert audit["dtypes"]["id"].startswith("int")
    assert audit["missing_values"][0]["missing"] == 0
    assert [item["column"] for item in audit["low_cardinality"]] == ["category"]
    assert audit["preview"][0] == {"id": 1, "category": "a", "value": 10}


def test_format_csv_audit_keeps_human_report(tmp_path: Path) -> None:
    audit = analyze_csv(make_csv(tmp_path))

    report = format_csv_audit(audit)

    assert "FICHIER" in report
    assert "COLONNES ET TYPES" in report
    assert "VALEURS MANQUANTES" in report
    assert "CLÉS SIMPLES CANDIDATES" in report
    assert "APERÇU" in report


def test_inspect_csv_parser_accepts_json(tmp_path: Path) -> None:
    path = make_csv(tmp_path)

    args = cli.build_parser().parse_args(["inspect-csv", str(path), "--json"])

    assert args.json is True
    assert args.func is cli.command_inspect_csv


def test_command_inspect_csv_json_is_parseable(tmp_path: Path, capsys) -> None:
    path = make_csv(tmp_path)
    args = cli.build_parser().parse_args(
        ["inspect-csv", str(path), "--low-cardinality", "2", "--json"]
    )

    cli.command_inspect_csv(args)

    payload = json.loads(capsys.readouterr().out)
    assert payload["file"]["rows"] == 3
    assert payload["candidate_keys"] == ["id", "value"]
    assert [item["column"] for item in payload["low_cardinality"]] == ["category"]
