import sys
from pathlib import Path

import pandas as pd
import pytest

import inspect_csv as module
from inspect_csv import (
    detect_encoding,
    detect_separator,
    find_candidate_keys,
    inspect_csv,
    load_csv,
    print_cardinalities,
    print_low_cardinality,
    print_missing_values,
)


def test_detect_encoding_utf8(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("name;city\nAndré;Strasbourg\n", encoding="utf-8")

    assert detect_encoding(path) in {"utf-8", "utf-8-sig"}


def test_detect_separator_semicolon(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text(
        "id;name;value\n1;alpha;10\n2;beta;20\n",
        encoding="utf-8",
    )

    encoding = detect_encoding(path)

    assert detect_separator(path, encoding) == ";"


def test_detect_separator_comma(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text(
        "id,name,value\n1,alpha,10\n2,beta,20\n",
        encoding="utf-8",
    )

    encoding = detect_encoding(path)

    assert detect_separator(path, encoding) == ","


def test_load_csv(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text(
        "id;name\n1;alpha\n2;beta\n",
        encoding="utf-8",
    )

    df = load_csv(
        path,
        encoding="utf-8",
        separator=";",
    )

    assert len(df) == 2
    assert list(df.columns) == ["id", "name"]


def test_load_csv_with_nrows(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text(
        "id;name\n1;alpha\n2;beta\n3;gamma\n",
        encoding="utf-8",
    )

    df = load_csv(
        path,
        encoding="utf-8",
        separator=";",
        nrows=2,
    )

    assert len(df) == 2


def test_find_candidate_keys() -> None:
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "category": ["a", "a", "b"],
            "value": [10, 20, 30],
        }
    )

    assert find_candidate_keys(df) == ["id", "value"]


def test_find_candidate_keys_rejects_duplicates() -> None:
    df = pd.DataFrame(
        {
            "id": [1, 1, 2],
            "name": ["a", "b", "c"],
        }
    )

    assert find_candidate_keys(df) == ["name"]


def test_find_candidate_keys_rejects_missing_values() -> None:
    df = pd.DataFrame(
        {
            "id": [1, 2, None],
            "name": ["a", "b", "c"],
        }
    )

    assert find_candidate_keys(df) == ["name"]


def test_print_missing_values(capsys) -> None:
    df = pd.DataFrame(
        {
            "a": [1, None, 3],
            "b": ["x", "y", "z"],
        }
    )

    print_missing_values(df)

    output = capsys.readouterr().out

    assert "missing" in output
    assert "percent" in output
    assert "a" in output
    assert "1" in output


def test_print_cardinalities(capsys) -> None:
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "category": ["a", "a", "b"],
        }
    )

    print_cardinalities(df)

    output = capsys.readouterr().out

    assert "column" in output
    assert "unique" in output
    assert "ratio" in output
    assert "id" in output
    assert "category" in output


def test_print_low_cardinality(capsys) -> None:
    df = pd.DataFrame(
        {
            "small": ["a", "a", "b"],
            "large": [1, 2, 3],
        }
    )

    print_low_cardinality(
        df,
        threshold=2,
    )

    output = capsys.readouterr().out

    assert "small" in output
    assert "large" not in output


def test_inspect_csv_full_output(
    tmp_path: Path,
    capsys,
) -> None:
    path = tmp_path / "data.csv"
    path.write_text(
        "id;category;value\n1;a;10\n2;a;20\n3;b;30\n",
        encoding="utf-8",
    )

    inspect_csv(path)

    output = capsys.readouterr().out

    assert "FICHIER" in output
    assert "COLONNES ET TYPES" in output
    assert "VALEURS MANQUANTES" in output
    assert "DOUBLONS" in output
    assert "CARDINALITÉS" in output
    assert "CLÉS SIMPLES CANDIDATES" in output
    assert "APERÇU" in output
    assert "id" in output


def test_inspect_csv_with_nrows(
    tmp_path: Path,
    capsys,
) -> None:
    path = tmp_path / "data.csv"
    path.write_text(
        "id;value\n1;a\n2;b\n3;c\n",
        encoding="utf-8",
    )

    inspect_csv(
        path,
        nrows=2,
    )

    output = capsys.readouterr().out

    assert "Lignes       : 2" in output
    assert "Limite       : 2 lignes" in output


def test_inspect_csv_with_forced_encoding_and_separator(
    tmp_path: Path,
    capsys,
) -> None:
    path = tmp_path / "data.csv"
    path.write_text(
        "id|value\n1|a\n2|b\n",
        encoding="utf-8",
    )

    inspect_csv(
        path,
        encoding="utf-8",
        separator="|",
    )

    output = capsys.readouterr().out

    assert "Encodage     : utf-8" in output
    assert "Séparateur   : '|'" in output
    assert "Colonnes     : 2" in output


def test_parse_args(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "inspect_csv.py",
            "data.csv",
            "--encoding",
            "utf-8",
            "--sep",
            ";",
            "--nrows",
            "100",
            "--low-cardinality",
            "10",
        ],
    )

    args = module.parse_args()

    assert args.file == Path("data.csv")
    assert args.encoding == "utf-8"
    assert args.sep == ";"
    assert args.nrows == 100
    assert args.low_cardinality == 10


def test_main_rejects_missing_file(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "inspect_csv.py",
            "missing.csv",
        ],
    )

    with pytest.raises(
        SystemExit,
        match="Fichier introuvable",
    ):
        module.main()


def test_main_calls_inspect_csv(
    monkeypatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "data.csv"
    path.write_text(
        "id;value\n1;a\n",
        encoding="utf-8",
    )

    calls = []

    def fake_inspect_csv(
        file,
        *,
        encoding=None,
        separator=None,
        nrows=None,
        low_cardinality=30,
    ):
        calls.append(
            {
                "file": file,
                "encoding": encoding,
                "separator": separator,
                "nrows": nrows,
                "low_cardinality": low_cardinality,
            }
        )

    monkeypatch.setattr(
        module,
        "inspect_csv",
        fake_inspect_csv,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "inspect_csv.py",
            str(path),
            "--encoding",
            "utf-8",
            "--sep",
            ";",
            "--nrows",
            "5",
            "--low-cardinality",
            "12",
        ],
    )

    module.main()

    assert calls == [
        {
            "file": path,
            "encoding": "utf-8",
            "separator": ";",
            "nrows": 5,
            "low_cardinality": 12,
        }
    ]
