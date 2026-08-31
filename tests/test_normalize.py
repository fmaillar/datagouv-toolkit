"""Tests de la normalisation des métadonnées data.gouv.fr."""

import pytest

from datagouv_toolkit.normalize import (
    normalize_format,
    normalize_frequency,
    normalize_license,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ESRI Shapefile (SHP)", "shp"),
        ("esri shapefile", "shp"),
        ("Shapefile", "shp"),
        ("ogc:WFS", "wfs"),
        ("ogc:WMS", "wms"),
        ("vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
        ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
        ("application/json", "json"),
        ("text/csv", "csv"),
        ("application/pdf", "pdf"),
    ],
)
def test_normalize_known_format_aliases(raw, expected):
    assert normalize_format(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("CSV", "csv"),
        (" GeoJSON ", "geojson"),
        ("GTFS-RT", "gtfs-rt"),
        ("MapInfo TAB", "mapinfo tab"),
    ],
)
def test_normalize_preserves_unknown_formats(raw, expected):
    assert normalize_format(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_normalize_unknown_format(raw):
    assert normalize_format(raw) == "?"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Licence Ouverte / Open Licence version 2.0", "fr-lo-2.0"),
        ("lov2", "fr-lo-2.0"),
        ("Open Data Commons Open Database License (ODbL)", "odbl"),
        ("odc-odbl", "odbl"),
        ("License Not Specified", "unknown"),
        ("notspecified", "unknown"),
        (None, "unknown"),
        ("", "unknown"),
        ("   ", "unknown"),
    ],
)
def test_normalize_known_license_aliases(raw, expected):
    assert normalize_license(raw) == expected


def test_normalize_license_does_not_merge_fr_lo():
    assert normalize_license("fr-lo") == "fr-lo"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Annual", "annual"),
        (" WEEKLY ", "weekly"),
        ("threeTimesAYear", "threetimesayear"),
        ("notPlanned", "notplanned"),
    ],
)
def test_normalize_frequency_preserves_explicit_values(raw, expected):
    assert normalize_frequency(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "?", "unknown", "UNKNOWN"])
def test_normalize_unknown_frequency(raw):
    assert normalize_frequency(raw) == "unknown"
