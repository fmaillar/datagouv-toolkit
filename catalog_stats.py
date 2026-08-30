#!/usr/bin/env python3
"""Statistiques reproductibles sur un snapshot du catalogue data.gouv.fr.

Le script analyse localement les exports ``datasets.parquet`` et ``resources.parquet``
du jeu « Catalogue des données de data.gouv.fr ». Contrairement à la recherche
paginée de l'API, un snapshot local fournit un corpus stable et reproductible.

Exemples
--------
Recherche textuelle simple :

    python catalog_stats.py "transport" \
        --snapshot snapshot/2026-08-25

Filtrer par producteur :

    python catalog_stats.py "transport" \
        --snapshot snapshot/2026-08-25 \
        --producer "Toulouse métropole"

Filtrer par licence et fréquence :

    python catalog_stats.py "énergie" \
        --snapshot snapshot/2026-08-25 \
        --license lov2 \
        --frequency annual

Ne conserver que les ressources CSV :

    python catalog_stats.py "transport" \
        --snapshot snapshot/2026-08-25 \
        --format csv

Le filtrage textuel porte sur le titre, la description courte, la description,
les tags et le producteur du dataset.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from normalize import (
    normalize_format,
    normalize_frequency,
    normalize_license,
)

DATASETS_FILENAME = "datasets.parquet"
RESOURCES_FILENAME = "resources.parquet"
DEFAULT_TOP = 15


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


def text_matches(value, expected):
    """Teste une correspondance de sous-chaîne insensible à la casse."""
    if expected is None:
        return True

    if not value:
        return False

    return expected.casefold() in str(value).casefold()


def exact_matches(value, expected):
    """Teste une égalité textuelle insensible à la casse."""
    if expected is None:
        return True

    if value is None:
        return False

    return str(value).strip().casefold() == expected.strip().casefold()


def dataset_matches(row, query, producer=None, license_name=None, frequency=None):
    """Indique si un dataset correspond à la requête et aux filtres structurés."""
    needle = query.casefold()

    searchable_fields = (
        row.get("title"),
        row.get("description_short"),
        row.get("description"),
        row.get("tags"),
        row.get("organization"),
    )

    haystack = " ".join(str(value) for value in searchable_fields if value).casefold()

    if needle not in haystack:
        return False

    if not text_matches(row.get("organization"), producer):
        return False

    if license_name is not None and normalize_license(
        row.get("license")
    ) != normalize_license(license_name):
        return False

    return frequency is None or normalize_frequency(
        row.get("frequency")
    ) == normalize_frequency(frequency)


def collect_dataset_candidates(
    path,
    query,
    producer=None,
    license_name=None,
    frequency=None,
):
    """Parcourt ``datasets.parquet`` et retourne les candidats retenus.

    Les métadonnées minimales nécessaires aux statistiques sont conservées en
    mémoire. Cela permet ensuite de restreindre les statistiques dataset aux
    seuls jeux possédant une ressource correspondant éventuellement à
    ``--format``.
    """
    candidates = {}
    total_datasets = 0

    parquet = pq.ParquetFile(path)

    for batch in parquet.iter_batches(
        columns=[
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
        batch_size=100_000,
    ):
        for row in batch.to_pylist():
            total_datasets += 1

            if not dataset_matches(
                row,
                query,
                producer=producer,
                license_name=license_name,
                frequency=frequency,
            ):
                continue

            dataset_id = row.get("id")

            if not dataset_id:
                continue

            candidates[dataset_id] = {
                "producer": row.get("organization") or row.get("owner") or "?",
                "license": normalize_license(row.get("license")),
                "frequency": normalize_frequency(row.get("frequency")),
            }

    return total_datasets, candidates


def collect_resource_stats(path, candidate_ids, resource_format_filter=None):
    """Agrège les ressources des datasets candidats.

    Si ``resource_format_filter`` est renseigné, seules les ressources dont le
    format normalisé correspond exactement au filtre sont retenues.

    Returns
    -------
    dict
        Statistiques ressources et ensemble des IDs de datasets ayant au moins
        une ressource retenue.
    """
    formats = Counter()
    matched_dataset_ids = set()

    total_resources = 0
    matched_resources = 0
    known_size = 0
    unknown_size = 0

    normalized_filter = (
        normalize_format(resource_format_filter)
        if resource_format_filter is not None
        else None
    )

    parquet = pq.ParquetFile(path)

    for batch in parquet.iter_batches(
        columns=["dataset.id", "format", "filesize"],
        batch_size=100_000,
    ):
        for row in batch.to_pylist():
            total_resources += 1

            dataset_id = row.get("dataset.id")

            if dataset_id not in candidate_ids:
                continue

            fmt = normalize_format(row.get("format"))

            if normalized_filter is not None and fmt != normalized_filter:
                continue

            matched_resources += 1
            matched_dataset_ids.add(dataset_id)
            formats[fmt] += 1

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
        "dataset_ids": matched_dataset_ids,
    }


def build_dataset_stats(total_datasets, candidates, selected_ids):
    """Construit les statistiques dataset pour les IDs finalement retenus."""
    producers = Counter()
    licenses = Counter()
    frequencies = Counter()

    for dataset_id in selected_ids:
        metadata = candidates[dataset_id]
        producers[metadata["producer"]] += 1
        licenses[metadata["license"]] += 1
        frequencies[metadata["frequency"]] += 1

    return {
        "catalog_datasets": total_datasets,
        "datasets": len(selected_ids),
        "producers": producers,
        "licenses": licenses,
        "frequencies": frequencies,
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


def print_active_filters(args):
    """Affiche les filtres structurés effectivement utilisés."""
    filters = []

    if args.producer:
        filters.append(f"producteur={args.producer}")

    if args.license_name:
        filters.append(f"licence={normalize_license(args.license_name)}")

    if args.frequency:
        filters.append(f"fréquence={normalize_frequency(args.frequency)}")

    if args.resource_format:
        filters.append(f"format={normalize_format(args.resource_format)}")

    if filters:
        print(f"Filtres              : {', '.join(filters)}")


def print_stats(query, snapshot, dataset_stats, resource_stats, top, args):
    """Affiche les statistiques agrégées du snapshot."""
    print(f"Snapshot             : {snapshot}")
    print(f"Recherche            : {query}")
    print_active_filters(args)
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
    """Vérifie le snapshot et retourne les fichiers catalogue attendus."""
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
        help="Répertoire contenant datasets.parquet et resources.parquet",
    )
    parser.add_argument(
        "--producer",
        help="Filtrer les datasets par nom de producteur (correspondance partielle)",
    )
    parser.add_argument(
        "--license",
        dest="license_name",
        help="Filtrer les datasets par licence (correspondance exacte)",
    )
    parser.add_argument(
        "--frequency",
        help="Filtrer les datasets par fréquence (correspondance exacte)",
    )
    parser.add_argument(
        "--format",
        dest="resource_format",
        help="Filtrer les ressources par format normalisé",
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

        total_datasets, candidates = collect_dataset_candidates(
            datasets_path,
            args.query,
            producer=args.producer,
            license_name=args.license_name,
            frequency=args.frequency,
        )

        resource_stats = collect_resource_stats(
            resources_path,
            set(candidates),
            resource_format_filter=args.resource_format,
        )

        selected_ids = resource_stats["dataset_ids"]

        # Sans filtre de format, un dataset sans ressource exportée doit rester
        # comptabilisé dans les statistiques dataset.
        if args.resource_format is None:
            selected_ids = set(candidates)

        dataset_stats = build_dataset_stats(
            total_datasets,
            candidates,
            selected_ids,
        )

        print_stats(
            args.query,
            snapshot,
            dataset_stats,
            resource_stats,
            args.top,
            args,
        )

    except FileNotFoundError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    except (OSError, pa.ArrowInvalid) as exc:
        print(f"Erreur fichier : {exc}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
