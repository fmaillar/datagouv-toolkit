"""Tests unitaires de catalog_stats.py."""

import csv
from collections import Counter

import pytest

from catalog_stats import (
    build_dataset_stats,
    collect_resource_stats,
    dataset_matches,
    exact_matches,
    parse_int,
    text_matches,
)


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
    path = tmp_path / "resources.csv"

    write_csv(
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
    path = tmp_path / "resources.csv"

    write_csv(
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
    path = tmp_path / "resources.csv"

    write_csv(
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
    path = tmp_path / "resources.csv"

    write_csv(
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
