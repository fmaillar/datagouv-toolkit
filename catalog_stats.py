#!/usr/bin/env python3
"""Statistiques agrégées sur une recherche du catalogue data.gouv.fr.

Ce script complète ``datagouv.py`` : au lieu d'explorer un seul jeu de
données, il parcourt plusieurs pages de résultats et agrège des informations
sur les producteurs, formats de ressources, licences et fréquences de mise à
jour.

Exemples
--------
Analyser les 1 000 premiers jeux correspondant à « énergie » :

    python catalog_stats.py "énergie"

Limiter l'analyse à 200 jeux :

    python catalog_stats.py "transport" --limit 200

Parcourir tous les résultats :

    python catalog_stats.py "météo" --limit 0

Afficher les 25 premières valeurs de chaque classement :

    python catalog_stats.py "logement" --top 25
"""

import argparse
import sys
from collections import Counter

import requests

import datagouv

DEFAULT_PAGE_SIZE = 100
DEFAULT_LIMIT = 1000
DEFAULT_TOP = 15


def iter_datasets(query, page_size=DEFAULT_PAGE_SIZE, limit=DEFAULT_LIMIT):
    """Parcourt les résultats paginés d'une recherche data.gouv.fr.

    Parameters
    ----------
    query:
        Texte de recherche envoyé à l'API.
    page_size:
        Nombre de datasets demandés par page.
    limit:
        Nombre maximal de datasets à retourner. ``0`` signifie sans limite.

    Yields
    ------
    dict
        Un dataset tel que renvoyé par l'API catalogue.
    """
    page = 1
    yielded = 0

    while True:
        data = datagouv.get_json(
            f"{datagouv.API_BASE}/datasets/",
            params={
                "q": query,
                "page": page,
                "page_size": page_size,
            },
        )

        datasets = data.get("data", [])

        if not datasets:
            return

        for dataset in datasets:
            if limit and yielded >= limit:
                return

            yield dataset
            yielded += 1

        total = data.get("total")

        if total is not None and yielded >= total:
            return

        if len(datasets) < page_size:
            return

        page += 1


def dataset_producer(dataset):
    """Retourne le nom du producteur d'un dataset, si disponible."""
    organization = dataset.get("organization")

    if organization:
        return organization.get("name") or "?"

    owner = dataset.get("owner")
    if owner:
        return owner.get("name") or "?"

    return "?"


def resource_format(resource):
    """Retourne le format déclaré ou l'infère depuis l'URL."""
    fmt = resource.get("format")

    if fmt:
        return str(fmt).lower()

    url = resource.get("url") or ""
    suffix = url.rsplit(".", 1)[-1].lower() if "." in url else ""

    known_suffixes = {
        "csv",
        "pdf",
        "json",
        "geojson",
        "zip",
        "xlsx",
        "xls",
        "xml",
        "parquet",
    }

    return suffix if suffix in known_suffixes else "?"


def collect_stats(datasets):
    """Agrège les principales métadonnées d'une séquence de datasets."""
    producers = Counter()
    licenses = Counter()
    frequencies = Counter()
    formats = Counter()

    dataset_count = 0
    resource_count = 0
    known_size = 0
    unknown_size = 0

    for dataset in datasets:
        dataset_count += 1

        producers[dataset_producer(dataset)] += 1
        licenses[dataset.get("license") or "?"] += 1
        frequencies[dataset.get("frequency") or "?"] += 1

        for resource in dataset.get("resources", []):
            resource_count += 1
            formats[resource_format(resource)] += 1

            filesize = resource.get("filesize")
            if filesize is None:
                unknown_size += 1
            else:
                known_size += filesize

    return {
        "datasets": dataset_count,
        "resources": resource_count,
        "producers": producers,
        "licenses": licenses,
        "frequencies": frequencies,
        "formats": formats,
        "known_size": known_size,
        "unknown_size": unknown_size,
    }


def print_counter(title, counter, top):
    """Affiche les valeurs les plus fréquentes d'un Counter."""
    print()
    print(title)
    print("-" * len(title))

    if not counter:
        print("?")
        return

    for value, count in counter.most_common(top):
        print(f"{count:6}  {value}")

    remaining = len(counter) - min(top, len(counter))
    if remaining > 0:
        print(f"... {remaining} autre(s) valeur(s)")


def print_stats(query, total, stats, top):
    """Affiche la synthèse agrégée d'une recherche."""
    print(f"Recherche            : {query}")
    print(f"Datasets trouvés     : {total}")
    print(f"Datasets analysés    : {stats['datasets']}")
    print(f"Ressources analysées : {stats['resources']}")

    if stats["known_size"] == 0 and stats["unknown_size"] == stats["resources"]:
        print("Taille connue        : inconnue")
    else:
        print(f"Taille connue        : {datagouv.format_size(stats['known_size'])}")

    print(f"Tailles inconnues    : {stats['unknown_size']} ressource(s)")

    print_counter("Principaux producteurs", stats["producers"], top)
    print_counter("Formats de ressources", stats["formats"], top)
    print_counter("Licences", stats["licenses"], top)
    print_counter("Fréquences de mise à jour", stats["frequencies"], top)


def get_total(query):
    """Retourne le nombre total de datasets correspondant à une recherche."""
    data = datagouv.search_datasets(query, page_size=1)
    return data.get("total", "?")


def build_parser():
    """Construit le parseur de ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Statistiques agrégées sur le catalogue data.gouv.fr"
    )
    parser.add_argument(
        "query",
        help="Texte de recherche",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Nombre maximal de datasets à analyser ; 0 = tous (défaut: 1000)",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help="Nombre de datasets demandés par page (défaut: 100)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP,
        help="Nombre de valeurs affichées par classement (défaut: 15)",
    )
    return parser


def main():
    """Point d'entrée principal."""
    parser = build_parser()
    args = parser.parse_args()

    if args.limit < 0:
        parser.error("--limit doit être positif ou nul")

    if args.page_size <= 0:
        parser.error("--page-size doit être strictement positif")

    if args.top <= 0:
        parser.error("--top doit être strictement positif")

    try:
        total = get_total(args.query)
        stats = collect_stats(
            iter_datasets(
                args.query,
                page_size=args.page_size,
                limit=args.limit,
            )
        )
        print_stats(args.query, total, stats, args.top)

    except requests.HTTPError as exc:
        print(f"Erreur HTTP : {exc}", file=sys.stderr)
        return 1

    except requests.RequestException as exc:
        print(f"Erreur réseau : {exc}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
