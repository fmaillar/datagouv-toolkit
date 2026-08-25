"""Tests de la normalisation des métadonnées data.gouv.fr."""

import pytest

from normalize import normalize_format


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
def test_normalize_known_aliases(raw, expected):
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
