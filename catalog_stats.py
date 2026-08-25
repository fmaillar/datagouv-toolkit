#!/usr/bin/env python3
"""Statistiques reproductibles sur un snapshot du catalogue data.gouv.fr.

Le script analyse localement les exports ``datasets.csv`` et ``resources.csv``
du jeu « Catalogue des données de data.gouv.fr ». Contrairement à la recherche
paginée de l'API, un snapshot local fournit un corpus stable et reproductible.

Exemple
-------
    python catalog_stats.py "transport" \
        --snapshot snapshot/2026-08-25

Le filtrage textuel porte sur le titre, la description courte, la description,
les tags et le producteur du dataset.
"""

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

from normalize import normalize_format

DATASETS_FILENAME = "datasets.csv"
RESOURCES_FILENAME = "resources.csv"
DEFAULT_TOP = 15

# Certains champs des exports data.gouv.fr, notamment les descriptions ou
# métadonnées JSON, dépassent la limite par défaut du module csv.
csv.field_size_limit(sys.maxsize)


def format_size(size):
    """Convertit une taille en octets vers une représentation lisible."""
    size = float(size)

    for unit in ("o", "Ko", "Mo", "Go", "To"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} Po"


def parse_int(value):
    """Convertit une valeur textuelle en entier ou retourne ``None``."""
    if value is None:
        return None

    value = value.strip()

    if not value:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def dataset_matches(row, query):
    """Indique si un dataset correspond à la requête textuelle.

    Le filtrage est volontairement simple et déterministe : recherche de
    sous-chaîne insensible à la casse dans plusieurs champs textuels du
    snapshot.
    """
    needle = query.casefold()

    searchable_fields = (
        row.get("title"),
        row.get("description_short"),
        row.get("description"),
        row.get("tags"),
        row.get("organization"),
    )

    haystack = " ".join(str(value) for value in searchable_fields if value).casefold()

    return needle in haystack


def collect_dataset_stats(path, query):
    """Parcourt ``datasets.csv`` et agrège les datasets correspondants.

    Returns
    -------
    tuple
        ``(matching_ids, stats)`` où ``matching_ids`` est l'ensemble des IDs
        retenus et ``stats`` contient les compteurs au niveau dataset.
    """
    matching_ids = set()
    producers = Counter()
    licenses = Counter()
    frequencies = Counter()

    total_datasets = 0

    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            total_datasets += 1

            if not dataset_matches(row, query):
                continue

            dataset_id = row.get("id")
            if not dataset_id:
                continue

            matching_ids.add(dataset_id)

            producers[row.get("organization") or row.get("owner") or "?"] += 1
            licenses[row.get("license") or "?"] += 1
            frequencies[row.get("frequency") or "?"] += 1

    stats = {
        "catalog_datasets": total_datasets,
        "datasets": len(matching_ids),
        "producers": producers,
        "licenses": licenses,
        "frequencies": frequencies,
    }

    return matching_ids, stats


def collect_resource_stats(path, dataset_ids):
    """Parcourt ``resources.csv`` et agrège les ressources des datasets retenus."""
    formats = Counter()

    total_resources = 0
    matched_resources = 0
    known_size = 0
    unknown_size = 0

    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            total_resources += 1

            if row.get("dataset.id") not in dataset_ids:
                continue

            matched_resources += 1

            formats[normalize_format(row.get("format"))] += 1

            filesize = parse_int(row.get("filesize"))

            if filesize is None:
                unknown_size += 1
            else:
                known_size += filesize

    return {
        "catalog_resources": total_resources,
        "resources": matched_resources,
        "formats": formats,
        "known_size": known_size,
        "unknown_size": unknown_size,
    }


def print_counter(title, counter, top):
    """Affiche les valeurs les plus fréquentes d'un ``Counter``."""
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


def print_stats(query, snapshot, dataset_stats, resource_stats, top):
    """Affiche les statistiques agrégées du snapshot."""
    print(f"Snapshot             : {snapshot}")
    print(f"Recherche            : {query}")
    print(f"Datasets catalogue   : {dataset_stats['catalog_datasets']}")
    print(f"Datasets trouvés     : {dataset_stats['datasets']}")
    print(f"Ressources catalogue : {resource_stats['catalog_resources']}")
    print(f"Ressources analysées : {resource_stats['resources']}")

    if (
        resource_stats["known_size"] == 0
        and resource_stats["unknown_size"] == resource_stats["resources"]
    ):
        print("Taille connue        : inconnue")
    else:
        print(f"Taille connue        : {format_size(resource_stats['known_size'])}")

    print(f"Tailles inconnues    : {resource_stats['unknown_size']} ressource(s)")

    print_counter(
        "Principaux producteurs",
        dataset_stats["producers"],
        top,
    )
    print_counter(
        "Formats de ressources",
        resource_stats["formats"],
        top,
    )
    print_counter(
        "Licences",
        dataset_stats["licenses"],
        top,
    )
    print_counter(
        "Fréquences de mise à jour",
        dataset_stats["frequencies"],
        top,
    )


def resolve_snapshot(path):
    """Vérifie le snapshot et retourne les deux fichiers CSV attendus."""
    snapshot = path.expanduser().resolve()
    datasets = snapshot / DATASETS_FILENAME
    resources = snapshot / RESOURCES_FILENAME

    missing = [file.name for file in (datasets, resources) if not file.is_file()]

    if missing:
        names = ", ".join(missing)
        raise FileNotFoundError(
            f"Snapshot incomplet : fichier(s) manquant(s) : {names}"
        )

    return snapshot, datasets, resources


def build_parser():
    """Construit le parseur de ligne de commande."""
    parser = argparse.ArgumentParser(
        description=(
            "Statistiques reproductibles sur un snapshot du catalogue data.gouv.fr"
        )
    )
    parser.add_argument(
        "query",
        help="Texte recherché dans les métadonnées locales",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        required=True,
        help="Répertoire contenant datasets.csv et resources.csv",
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

    if args.top <= 0:
        parser.error("--top doit être strictement positif")

    try:
        snapshot, datasets_path, resources_path = resolve_snapshot(args.snapshot)

        matching_ids, dataset_stats = collect_dataset_stats(
            datasets_path,
            args.query,
        )

        resource_stats = collect_resource_stats(
            resources_path,
            matching_ids,
        )

        print_stats(
            args.query,
            snapshot,
            dataset_stats,
            resource_stats,
            args.top,
        )

    except FileNotFoundError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    except csv.Error as exc:
        print(f"Erreur CSV : {exc}", file=sys.stderr)
        return 1

    except OSError as exc:
        print(f"Erreur fichier : {exc}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
