"""Tests unitaires de catalog_stats.py."""

import csv
import sys
from argparse import Namespace
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import catalog_stats as module
from catalog_stats import (
    build_dataset_stats,
    collect_dataset_candidates,
    collect_resource_stats,
    dataset_matches,
    exact_matches,
    format_size,
    parse_int,
    print_active_filters,
    print_counter,
    print_stats,
    resolve_snapshot,
    text_matches,
)


def write_parquet(path, fieldnames, rows):
    """Écrit une petite fixture Parquet pour les tests."""
    data = {
        field: [row.get(field, "") for row in rows]
        for field in fieldnames
    }
    table = pa.table(data)
    pq.write_table(table, path, compression="zstd")

@pytest.mark.parametrize(
    ("value", "expected", "result"),
    [
        ("Toulouse métropole", "toulouse", True),
        ("Toulouse métropole", "MÉTROPOLE", True),
        ("Toulouse métropole", "Rennes", False),
        ("", "Toulouse", False),
        (None, "Toulouse", False),
        ("Toulouse métropole", None, True),
    ],
)

def test_text_matches(value, expected, result):
    assert text_matches(value, expected) is result


@pytest.mark.parametrize(
    ("value", "expected", "result"),
    [
        ("annual", "annual", True),
        ("Annual", "annual", True),
        (" annual ", "ANNUAL", True),
        ("weekly", "annual", False),
        (None, "annual", False),
        ("annual", None, True),
    ],
)
def test_exact_matches(value, expected, result):
    assert exact_matches(value, expected) is result


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("123", 123),
        (" 42 ", 42),
        ("0", 0),
        ("", None),
        ("   ", None),
        (None, None),
        ("abc", None),
        ("12.5", None),
    ],
)
def test_parse_int(value, expected):
    assert parse_int(value) == expected


def make_dataset_row(**overrides):
    row = {
        "title": "Données transport Toulouse",
        "description_short": "Jeu sur les transports publics",
        "description": "Description détaillée",
        "tags": "transport,mobilite",
        "organization": "Toulouse métropole",
        "license": "Licence Ouverte / Open Licence version 2.0",
        "frequency": "annual",
    }
    row.update(overrides)
    return row


def test_dataset_matches_query_in_title():
    row = make_dataset_row()
    assert dataset_matches(row, "transport")


def test_dataset_matches_query_in_tags():
    row = make_dataset_row(title="Autre titre")
    assert dataset_matches(row, "mobilite")


def test_dataset_matches_rejects_missing_query():
    row = make_dataset_row()
    assert not dataset_matches(row, "énergie")


def test_dataset_matches_filters_producer():
    row = make_dataset_row()

    assert dataset_matches(row, "transport", producer="Toulouse")
    assert not dataset_matches(row, "transport", producer="Rennes")


@pytest.mark.parametrize(
    "license_name",
    [
        "fr-lo-2.0",
        "lov2",
        "Licence Ouverte / Open Licence version 2.0",
    ],
)
def test_dataset_matches_normalized_license(license_name):
    row = make_dataset_row()
    assert dataset_matches(row, "transport", license_name=license_name)


def test_dataset_matches_rejects_other_license():
    row = make_dataset_row()
    assert not dataset_matches(row, "transport", license_name="odbl")


@pytest.mark.parametrize(
    "frequency",
    [
        "annual",
        "Annual",
        " ANNUAL ",
    ],
)
def test_dataset_matches_normalized_frequency(frequency):
    row = make_dataset_row()
    assert dataset_matches(row, "transport", frequency=frequency)


def test_dataset_matches_unknown_frequency():
    row = make_dataset_row(frequency="?")
    assert dataset_matches(row, "transport", frequency="unknown")


def test_dataset_matches_rejects_other_frequency():
    row = make_dataset_row()
    assert not dataset_matches(row, "transport", frequency="weekly")


def test_build_dataset_stats():
    candidates = {
        "a": {
            "producer": "Toulouse métropole",
            "license": "fr-lo-2.0",
            "frequency": "annual",
        },
        "b": {
            "producer": "Toulouse métropole",
            "license": "odbl",
            "frequency": "weekly",
        },
        "c": {
            "producer": "Rennes Métropole",
            "license": "odbl",
            "frequency": "weekly",
        },
    }

    stats = build_dataset_stats(
        total_datasets=100,
        candidates=candidates,
        selected_ids={"a", "c"},
    )

    assert stats["catalog_datasets"] == 100
    assert stats["datasets"] == 2
    assert stats["producers"] == Counter(
        {
            "Toulouse métropole": 1,
            "Rennes Métropole": 1,
        }
    )
    assert stats["licenses"] == Counter(
        {
            "fr-lo-2.0": 1,
            "odbl": 1,
        }
    )
    assert stats["frequencies"] == Counter(
        {
            "annual": 1,
            "weekly": 1,
        }
    )


def write_csv(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def test_collect_resource_stats_filters_dataset_ids(tmp_path):
    path = tmp_path / "resources.parquet"

    write_parquet(
        path,
        [
            "dataset.id",
            "format",
            "filesize",
        ],
        [
            {
                "dataset.id": "a",
                "format": "CSV",
                "filesize": "100",
            },
            {
                "dataset.id": "b",
                "format": "JSON",
                "filesize": "200",
            },
            {
                "dataset.id": "c",
                "format": "CSV",
                "filesize": "300",
            },
        ],
    )

    stats = collect_resource_stats(
        path,
        {"a", "b"},
    )

    assert stats["catalog_resources"] == 3
    assert stats["resources"] == 2
    assert stats["known_size"] == 300
    assert stats["unknown_size"] == 0
    assert stats["formats"] == Counter(
        {
            "csv": 1,
            "json": 1,
        }
    )
    assert stats["dataset_ids"] == {"a", "b"}


def test_collect_resource_stats_normalizes_formats(tmp_path):
    path = tmp_path / "resources.parquet"

    write_parquet(
        path,
        [
            "dataset.id",
            "format",
            "filesize",
        ],
        [
            {
                "dataset.id": "a",
                "format": "ogc:WFS",
                "filesize": "",
            },
            {
                "dataset.id": "a",
                "format": "WFS",
                "filesize": "",
            },
            {
                "dataset.id": "a",
                "format": "ESRI Shapefile (SHP)",
                "filesize": "1024",
            },
        ],
    )

    stats = collect_resource_stats(
        path,
        {"a"},
    )

    assert stats["resources"] == 3
    assert stats["formats"] == Counter(
        {
            "wfs": 2,
            "shp": 1,
        }
    )
    assert stats["known_size"] == 1024
    assert stats["unknown_size"] == 2
    assert stats["dataset_ids"] == {"a"}


def test_collect_resource_stats_filters_normalized_format(tmp_path):
    path = tmp_path / "resources.parquet"

    write_parquet(
        path,
        [
            "dataset.id",
            "format",
            "filesize",
        ],
        [
            {
                "dataset.id": "a",
                "format": "ogc:WFS",
                "filesize": "",
            },
            {
                "dataset.id": "a",
                "format": "CSV",
                "filesize": "100",
            },
            {
                "dataset.id": "b",
                "format": "WFS",
                "filesize": "200",
            },
        ],
    )

    stats = collect_resource_stats(
        path,
        {"a", "b"},
        resource_format_filter="wfs",
    )

    assert stats["resources"] == 2
    assert stats["formats"] == Counter({"wfs": 2})
    assert stats["known_size"] == 200
    assert stats["unknown_size"] == 1
    assert stats["dataset_ids"] == {"a", "b"}


def test_collect_resource_stats_ignores_invalid_filesize(tmp_path):
    path = tmp_path / "resources.parquet"

    write_parquet(
        path,
        [
            "dataset.id",
            "format",
            "filesize",
        ],
        [
            {
                "dataset.id": "a",
                "format": "CSV",
                "filesize": "not-a-number",
            },
            {
                "dataset.id": "a",
                "format": "CSV",
                "filesize": "",
            },
        ],
    )

    stats = collect_resource_stats(
        path,
        {"a"},
    )

    assert stats["resources"] == 2
    assert stats["known_size"] == 0
    assert stats["unknown_size"] == 2


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0.0 o"),
        (1023, "1023.0 o"),
        (1024, "1.0 Ko"),
        (1024**2, "1.0 Mo"),
        (1024**3, "1.0 Go"),
        (1024**4, "1.0 To"),
        (1024**5, "1.0 Po"),
    ],
)
def test_format_size(size, expected):
    assert format_size(size) == expected


def test_collect_dataset_candidates(tmp_path: Path) -> None:
    path = tmp_path / "datasets.csv"

    write_csv(
        path,
        [
            "id",
            "title",
            "description_short",
            "description",
            "tags",
            "organization",
            "owner",
            "license",
            "frequency",
        ],
        [
            {
                "id": "a",
                "title": "Transport Toulouse",
                "description_short": "",
                "description": "",
                "tags": "",
                "organization": "Toulouse Métropole",
                "owner": "",
                "license": "Licence Ouverte / Open Licence version 2.0",
                "frequency": "Annual",
            },
            {
                "id": "b",
                "title": "Énergie Rennes",
                "description_short": "",
                "description": "",
                "tags": "",
                "organization": "Rennes Métropole",
                "owner": "",
                "license": "ODC-ODbL",
                "frequency": "weekly",
            },
            {
                "id": "",
                "title": "Transport sans identifiant",
                "description_short": "",
                "description": "",
                "tags": "",
                "organization": "",
                "owner": "Example owner",
                "license": "",
                "frequency": "",
            },
        ],
    )

    total, candidates = collect_dataset_candidates(
        path,
        "transport",
    )

    assert total == 3
    assert candidates == {
        "a": {
            "producer": "Toulouse Métropole",
            "license": "fr-lo-2.0",
            "frequency": "annual",
        }
    }


def test_collect_dataset_candidates_applies_filters(tmp_path: Path) -> None:
    path = tmp_path / "datasets.csv"

    write_csv(
        path,
        [
            "id",
            "title",
            "description_short",
            "description",
            "tags",
            "organization",
            "owner",
            "license",
            "frequency",
        ],
        [
            {
                "id": "a",
                "title": "Transport",
                "description_short": "",
                "description": "",
                "tags": "",
                "organization": "Toulouse Métropole",
                "owner": "",
                "license": "Licence Ouverte / Open Licence version 2.0",
                "frequency": "annual",
            },
            {
                "id": "b",
                "title": "Transport",
                "description_short": "",
                "description": "",
                "tags": "",
                "organization": "Rennes Métropole",
                "owner": "",
                "license": "ODC-ODbL",
                "frequency": "weekly",
            },
        ],
    )

    total, candidates = collect_dataset_candidates(
        path,
        "transport",
        producer="Toulouse",
        license_name="fr-lo-2.0",
        frequency="annual",
    )

    assert total == 2
    assert set(candidates) == {"a"}


def test_print_counter_empty(capsys) -> None:
    print_counter("Titre", Counter(), 10)

    output = capsys.readouterr().out

    assert "Titre" in output
    assert "?" in output


def test_print_counter_with_remaining_values(capsys) -> None:
    counter = Counter(
        {
            "a": 3,
            "b": 2,
            "c": 1,
        }
    )

    print_counter("Titre", counter, 2)

    output = capsys.readouterr().out

    assert "a" in output
    assert "b" in output
    assert "... 1 autre(s) valeur(s)" in output


def test_print_active_filters(capsys) -> None:
    args = Namespace(
        producer="Example",
        license_name="lov2",
        frequency="Annual",
        resource_format="ogc:WFS",
    )

    print_active_filters(args)

    output = capsys.readouterr().out

    assert "producteur=Example" in output
    assert "licence=fr-lo-2.0" in output
    assert "fréquence=annual" in output
    assert "format=wfs" in output


def test_print_active_filters_empty(capsys) -> None:
    args = Namespace(
        producer=None,
        license_name=None,
        frequency=None,
        resource_format=None,
    )

    print_active_filters(args)

    assert capsys.readouterr().out == ""


def test_print_stats_unknown_size(
    tmp_path: Path,
    capsys,
) -> None:
    args = Namespace(
        producer=None,
        license_name=None,
        frequency=None,
        resource_format=None,
    )

    dataset_stats = {
        "catalog_datasets": 10,
        "datasets": 1,
        "producers": Counter({"Example": 1}),
        "licenses": Counter({"fr-lo-2.0": 1}),
        "frequencies": Counter({"annual": 1}),
    }

    resource_stats = {
        "catalog_resources": 20,
        "resources": 2,
        "formats": Counter({"csv": 2}),
        "known_size": 0,
        "unknown_size": 2,
    }

    print_stats(
        "transport",
        tmp_path,
        dataset_stats,
        resource_stats,
        10,
        args,
    )

    output = capsys.readouterr().out

    assert "Recherche            : transport" in output
    assert "Taille connue        : inconnue" in output
    assert "Example" in output
    assert "csv" in output


def test_print_stats_known_size(
    tmp_path: Path,
    capsys,
) -> None:
    args = Namespace(
        producer=None,
        license_name=None,
        frequency=None,
        resource_format=None,
    )

    dataset_stats = {
        "catalog_datasets": 1,
        "datasets": 1,
        "producers": Counter(),
        "licenses": Counter(),
        "frequencies": Counter(),
    }

    resource_stats = {
        "catalog_resources": 1,
        "resources": 1,
        "formats": Counter(),
        "known_size": 1024,
        "unknown_size": 0,
    }

    print_stats(
        "x",
        tmp_path,
        dataset_stats,
        resource_stats,
        10,
        args,
    )

    assert "1.0 Ko" in capsys.readouterr().out


def test_resolve_snapshot(tmp_path: Path) -> None:
    (tmp_path / "datasets.csv").write_text("", encoding="utf-8")
    (tmp_path / "resources.parquet").touch()

    snapshot, datasets, resources = resolve_snapshot(tmp_path)

    assert snapshot == tmp_path.resolve()
    assert datasets == snapshot / "datasets.csv"
    assert resources == snapshot / "resources.parquet"


def test_resolve_snapshot_rejects_missing_files(tmp_path: Path) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="Snapshot incomplet",
    ):
        resolve_snapshot(tmp_path)


def test_build_parser() -> None:
    parser = module.build_parser()

    args = parser.parse_args(
        [
            "transport",
            "--snapshot",
            "snapshot/test",
            "--producer",
            "Example",
            "--license",
            "odbl",
            "--frequency",
            "weekly",
            "--format",
            "csv",
            "--top",
            "5",
        ]
    )

    assert args.query == "transport"
    assert args.snapshot == Path("snapshot/test")
    assert args.producer == "Example"
    assert args.license_name == "odbl"
    assert args.frequency == "weekly"
    assert args.resource_format == "csv"
    assert args.top == 5


def test_main_success(
    monkeypatch,
    tmp_path: Path,
) -> None:
    datasets = tmp_path / "datasets.csv"
    resources = tmp_path / "resources.parquet"

    monkeypatch.setattr(
        module,
        "resolve_snapshot",
        lambda path: (tmp_path, datasets, resources),
    )
    monkeypatch.setattr(
        module,
        "collect_dataset_candidates",
        lambda *args, **kwargs: (
            10,
            {
                "a": {
                    "producer": "Example",
                    "license": "fr-lo-2.0",
                    "frequency": "annual",
                }
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "collect_resource_stats",
        lambda *args, **kwargs: {
            "catalog_resources": 20,
            "resources": 1,
            "formats": Counter({"csv": 1}),
            "known_size": 100,
            "unknown_size": 0,
            "dataset_ids": {"a"},
        },
    )

    printed = []

    monkeypatch.setattr(
        module,
        "print_stats",
        lambda *args, **kwargs: printed.append(args),
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "catalog_stats.py",
            "transport",
            "--snapshot",
            str(tmp_path),
        ],
    )

    assert module.main() == 0
    assert len(printed) == 1


def test_main_with_format_filter(
    monkeypatch,
    tmp_path: Path,
) -> None:
    datasets = tmp_path / "datasets.csv"
    resources = tmp_path / "resources.parquet"

    candidates = {
        "a": {
            "producer": "A",
            "license": "fr-lo-2.0",
            "frequency": "annual",
        },
        "b": {
            "producer": "B",
            "license": "odbl",
            "frequency": "weekly",
        },
    }

    monkeypatch.setattr(
        module,
        "resolve_snapshot",
        lambda path: (tmp_path, datasets, resources),
    )
    monkeypatch.setattr(
        module,
        "collect_dataset_candidates",
        lambda *args, **kwargs: (2, candidates),
    )
    monkeypatch.setattr(
        module,
        "collect_resource_stats",
        lambda *args, **kwargs: {
            "catalog_resources": 2,
            "resources": 1,
            "formats": Counter({"csv": 1}),
            "known_size": 1,
            "unknown_size": 0,
            "dataset_ids": {"a"},
        },
    )

    selected = []

    def fake_build_dataset_stats(total, candidate_rows, selected_ids):
        selected.append(selected_ids)
        return {
            "catalog_datasets": total,
            "datasets": len(selected_ids),
            "producers": Counter(),
            "licenses": Counter(),
            "frequencies": Counter(),
        }

    monkeypatch.setattr(
        module,
        "build_dataset_stats",
        fake_build_dataset_stats,
    )
    monkeypatch.setattr(
        module,
        "print_stats",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "catalog_stats.py",
            "transport",
            "--snapshot",
            str(tmp_path),
            "--format",
            "csv",
        ],
    )

    assert module.main() == 0
    assert selected == [{"a"}]


def test_main_rejects_invalid_top(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "catalog_stats.py",
            "transport",
            "--snapshot",
            str(tmp_path),
            "--top",
            "0",
        ],
    )

    with pytest.raises(SystemExit):
        module.main()


@pytest.mark.parametrize(
    ("exception", "expected_code"),
    [
        (FileNotFoundError("missing"), 1),
        (OSError("failure"), 1),
        (KeyboardInterrupt(), 130),
    ],
)
def test_main_handles_errors(
    monkeypatch,
    tmp_path: Path,
    exception,
    expected_code,
) -> None:
    monkeypatch.setattr(
        module,
        "resolve_snapshot",
        lambda path: (_ for _ in ()).throw(exception),
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "catalog_stats.py",
            "transport",
            "--snapshot",
            str(tmp_path),
        ],
    )

    assert module.main() == expected_code


def test_main_handles_csv_error(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        module,
        "resolve_snapshot",
        lambda path: (
            tmp_path,
            tmp_path / "datasets.csv",
            tmp_path / "resources.parquet",
        ),
    )

    monkeypatch.setattr(
        module,
        "collect_dataset_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(csv.Error("broken")),
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "catalog_stats.py",
            "transport",
            "--snapshot",
            str(tmp_path),
        ],
    )

    assert module.main() == 1
