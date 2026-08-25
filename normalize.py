#!/usr/bin/env python3
"""Normalisation prudente des métadonnées du catalogue data.gouv.fr.

Ce module contient des fonctions de normalisation destinées à rendre les
métadonnées plus comparables sans masquer leur valeur d'origine.

Pour l'instant, seule la normalisation des formats de ressources est prise en
charge. Les règles restent volontairement conservatrices : seules les
équivalences évidentes sont regroupées.
"""

FORMAT_ALIASES = {
    "esri shapefile (shp)": "shp",
    "esri shapefile": "shp",
    "shapefile": "shp",
    "ogc:wfs": "wfs",
    "ogc:wms": "wms",
    "vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/json": "json",
    "text/csv": "csv",
    "application/pdf": "pdf",
}


def normalize_format(value):
    """Normalise un format de ressource data.gouv.fr.

    Parameters
    ----------
    value:
        Valeur brute du champ ``format``. ``None`` et les chaînes vides sont
        considérés comme inconnus.

    Returns
    -------
    str
        Format normalisé en minuscules. Les synonymes connus sont regroupés ;
        les valeurs non reconnues sont conservées, après suppression des
        espaces superflus et passage en minuscules.

    Examples
    --------
    >>> normalize_format("ESRI Shapefile (SHP)")
    'shp'
    >>> normalize_format("ogc:WFS")
    'wfs'
    >>> normalize_format("CSV")
    'csv'
    >>> normalize_format(None)
    '?'
    """
    if value is None:
        return "?"

    normalized = str(value).strip().lower()

    if not normalized:
        return "?"

    return FORMAT_ALIASES.get(normalized, normalized)
