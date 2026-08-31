from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow as pa

from . import catalog_stats
from .normalize import normalize_format, normalize_frequency, normalize_license


def counter_result(counter: Counter[str], top: int) -> dict[str, Any]:
    """Convertit un classement en structure JSON sérialisable."""
    items = [
        {"value": value, "count": count}
        for value, count in counter.most_common(top)
    ]
    return {
        "items": items,
        "remaining_values": max(0, len(counter) - len(items)),
    }


def active_filters(
    *,
    producer: str | None,
    license_name: str | None,
    frequency: str | None,
    resource_format: str | None,
) -> dict[str, str]:
    """Retourne les filtres actifs sous leur forme normalisée."""
    filters: dict[str, str] = {}

    if producer:
        filters["producer"] = producer
    if license_name:
        filters["license"] = normalize_license(license_name)
    if frequency:
        filters["frequency"] = normalize_frequency(frequency)
    if resource_format:
        filters["format"] = normalize_format(resource_format)

    return filters


def analyze_catalog(
    query: str,
    snapshot_path: Path,
    *,
    producer: str | None = None,
    license_name: str | None = None,
    frequency: str | None = None,
    resource_format: str | None = None,
    top: int = catalog_stats.DEFAULT_TOP,
) -> dict[str, Any]:
    """Calcule les statistiques d'un snapshot sans produire de sortie texte."""
    if top <= 0:
        raise ValueError("--top doit être strictement positif")

    snapshot, datasets_path, resources_path = catalog_stats.resolve_snapshot(snapshot_path)
    total_datasets, candidates = catalog_stats.collect_dataset_candidates(
        datasets_path,
        query,
        producer=producer,
        license_name=license_name,
        frequency=frequency,
    )
    resource_stats = catalog_stats.collect_resource_stats(
        resources_path,
        set(candidates),
        resource_format_filter=resource_format,
    )

    selected_ids = resource_stats["dataset_ids"]
    if resource_format is None:
        selected_ids = set(candidates)

    dataset_stats = catalog_stats.build_dataset_stats(
        total_datasets,
        candidates,
        selected_ids,
    )

    return {
        "snapshot": str(snapshot),
        "query": query,
        "filters": active_filters(
            producer=producer,
            license_name=license_name,
            frequency=frequency,
            resource_format=resource_format,
        ),
        "datasets": {
            "catalog": dataset_stats["catalog_datasets"],
            "matched": dataset_stats["datasets"],
        },
        "resources": {
            "catalog": resource_stats["catalog_resources"],
            "matched": resource_stats["resources"],
            "known_size_bytes": resource_stats["known_size"],
            "unknown_size": resource_stats["unknown_size"],
        },
        "rankings": {
            "producers": counter_result(dataset_stats["producers"], top),
            "formats": counter_result(resource_stats["formats"], top),
            "licenses": counter_result(dataset_stats["licenses"], top),
            "frequencies": counter_result(dataset_stats["frequencies"], top),
        },
        "top": top,
    }


def print_catalog_report(result: dict[str, Any], args: argparse.Namespace) -> None:
    """Affiche le rapport humain historique à partir du calcul structuré."""
    snapshot = Path(result["snapshot"])
    dataset_stats = {
        "catalog_datasets": result["datasets"]["catalog"],
        "datasets": result["datasets"]["matched"],
        "producers": Counter(
            {item["value"]: item["count"] for item in result["rankings"]["producers"]["items"]}
        ),
        "licenses": Counter(
            {item["value"]: item["count"] for item in result["rankings"]["licenses"]["items"]}
        ),
        "frequencies": Counter(
            {item["value"]: item["count"] for item in result["rankings"]["frequencies"]["items"]}
        ),
    }
    resource_stats = {
        "catalog_resources": result["resources"]["catalog"],
        "resources": result["resources"]["matched"],
        "known_size": result["resources"]["known_size_bytes"],
        "unknown_size": result["resources"]["unknown_size"],
        "formats": Counter(
            {item["value"]: item["count"] for item in result["rankings"]["formats"]["items"]}
        ),
    }
    catalog_stats.print_stats(
        result["query"],
        snapshot,
        dataset_stats,
        resource_stats,
        result["top"],
        args,
        remaining_values={
            name: ranking["remaining_values"]
            for name, ranking in result["rankings"].items()
        },
    )


def build_parser() -> argparse.ArgumentParser:
    """Construit le parseur de compatibilité de ``datagouv-catalog-stats``."""
    parser = catalog_stats.build_parser()
    parser.add_argument(
        "--json",
        action="store_true",
        help="Afficher le résultat au format JSON",
    )
    return parser


def main() -> int:
    """Point d'entrée compatible avec sortie texte ou JSON."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = analyze_catalog(
            args.query,
            args.snapshot,
            producer=args.producer,
            license_name=args.license_name,
            frequency=args.frequency,
            resource_format=args.resource_format,
            top=args.top,
        )

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print_catalog_report(result, args)
    except FileNotFoundError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    except (OSError, pa.ArrowInvalid) as exc:
        print(f"Erreur fichier : {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        parser.error(str(exc))
    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
