#!/usr/bin/env python3
"""Normalisation prudente des métadonnées du catalogue data.gouv.fr.

Ce module contient des fonctions de normalisation destinées à rendre les
métadonnées plus comparables sans masquer leur valeur d'origine.

Les règles restent volontairement conservatrices : seules les équivalences
claires sont regroupées. Les valeurs inconnues sont conservées sous une forme
normalisée quand cela est pertinent.
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

LICENSE_ALIASES = {
    "licence ouverte / open licence version 2.0": "fr-lo-2.0",
    "lov2": "fr-lo-2.0",
    "open data commons open database license (odbl)": "odbl",
    "odc-odbl": "odbl",
    "license not specified": "unknown",
    "notspecified": "unknown",
}

UNKNOWN_FREQUENCIES = {
    "",
    "?",
    "unknown",
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
    """
    if value is None:
        return "?"

    normalized = str(value).strip().lower()

    if not normalized:
        return "?"

    return FORMAT_ALIASES.get(normalized, normalized)


def normalize_license(value):
    """Normalise une licence data.gouv.fr vers un identifiant canonique.

    Les mappings restent limités aux équivalences explicites déjà observées
    dans l'API et dans les exports snapshot.

    ``fr-lo`` n'est volontairement pas fusionné avec ``fr-lo-2.0`` tant que
    sa sémantique exacte n'est pas vérifiée.

    Parameters
    ----------
    value:
        Valeur brute du champ licence.

    Returns
    -------
    str
        Identifiant canonique connu, ``unknown`` si la licence est absente ou
        non spécifiée, sinon valeur nettoyée en minuscules.
    """
    if value is None:
        return "unknown"

    normalized = str(value).strip().lower()

    if not normalized:
        return "unknown"

    return LICENSE_ALIASES.get(normalized, normalized)


def normalize_frequency(value):
    """Normalise une fréquence de mise à jour data.gouv.fr.

    Les valeurs vides, ``?`` et ``unknown`` sont regroupées sous
    ``unknown``. Les autres valeurs sont uniquement nettoyées et converties
    en minuscules afin de ne pas inventer de correspondances métier.

    Parameters
    ----------
    value:
        Valeur brute du champ fréquence.

    Returns
    -------
    str
        Fréquence canonique.
    """
    if value is None:
        return "unknown"

    normalized = str(value).strip().lower()

    if normalized in UNKNOWN_FREQUENCIES:
        return "unknown"

    return normalized
