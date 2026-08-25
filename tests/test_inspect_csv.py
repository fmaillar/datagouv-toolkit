from pathlib import Path

import pandas as pd

from inspect_csv import (
    detect_encoding,
    detect_separator,
    find_candidate_keys,
    load_csv,
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
