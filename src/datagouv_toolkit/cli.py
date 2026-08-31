from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

from . import catalog_report, catalog_stats, datagouv
from .dataset_workflow import run_workflow
from .download_resources import download_resources, select_resources
from .inspect_csv import DEFAULT_LOW_CARDINALITY, analyze_csv, inspect_csv


def add_dataset_selector(parser: argparse.ArgumentParser) -> None:
    """Ajoute les arguments communs permettant de résoudre un dataset."""
    parser.add_argument(
        "dataset",
        help="Identifiant ou texte de recherche du jeu de données",
    )
    parser.add_argument(
        "--producer",
        help="Filtrer par nom de producteur",
    )
    parser.add_argument(
        "--title",
        help="Filtrer par texte présent dans le titre du dataset",
    )
    parser.add_argument(
        "--first",
        action="store_true",
        help="Sélectionner le premier résultat sans demander de choix interactif",
    )


def add_json_option(parser: argparse.ArgumentParser) -> None:
    """Ajoute une option de sortie JSON à une sous-commande."""
    parser.add_argument(
        "--json",
        action="store_true",
        help="Afficher le résultat au format JSON",
    )


def command_download(args: argparse.Namespace) -> None:
    """Télécharge les ressources sélectionnées d'un dataset."""
    dataset = datagouv.resolve_dataset(
        args.dataset,
        producer=args.producer,
        title=args.title,
        first=args.first,
    )
    resources = select_resources(
        dataset,
        resource_format=args.resource_format,
        title=args.resource_title,
    )

    json_output = getattr(args, "json", False)

    if not json_output:
        print(f"Dataset    : {dataset['title']}")
        print(f"Ressources : {len(resources)}")
        print(f"Destination: {args.output.resolve()}")

    if not resources:
        raise ValueError("Aucune ressource correspondante.")

    if json_output:
        results = download_resources(
            resources,
            args.output,
            overwrite=args.overwrite,
            progress=False,
        )
    else:
        results = download_resources(
            resources,
            args.output,
            overwrite=args.overwrite,
        )

    if json_output:
        payload = {
            "dataset": {
                "id": dataset.get("id"),
                "title": dataset.get("title"),
            },
            "destination": str(args.output.resolve()),
            "resources": [
                {
                    "resource": result["resource"],
                    "path": str(result["path"].resolve()),
                    "downloaded": result["downloaded"],
                }
                for result in results
            ],
        }
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )


def command_workflow(args: argparse.Namespace) -> None:
    """Télécharge un dataset puis audite automatiquement ses CSV."""
    json_output = getattr(args, "json", False)
    result = run_workflow(
        args.dataset,
        args.output,
        producer=args.producer,
        dataset_title=args.title,
        first=args.first,
        resource_format=args.resource_format,
        resource_title=args.resource_title,
        overwrite=args.overwrite,
        audit_csv=not args.no_audit,
        audit_dir=args.audit_dir,
        progress=not json_output,
    )

    if json_output:
        payload = {
            "dataset": {
                "id": result["dataset"].get("id"),
                "title": result["dataset"].get("title"),
            },
            "destination": str(result["destination"]),
            "resources": [
                {
                    "resource": item["resource"],
                    "path": str(item["path"].resolve()),
                    "downloaded": item["downloaded"],
                    "audited": item["audited"],
                    "audit_path": (
                        str(item["audit_path"].resolve())
                        if item["audit_path"] is not None
                        else None
                    ),
                }
                for item in result["resources"]
            ],
        }
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )


def command_inspect_csv(args: argparse.Namespace) -> None:
    """Audite un fichier CSV local."""
    if not args.file.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {args.file}")

    if getattr(args, "json", False):
        audit = analyze_csv(
            args.file,
            encoding=args.encoding,
            separator=args.sep,
            nrows=args.nrows,
            low_cardinality=args.low_cardinality,
        )
        print(
            json.dumps(
                audit,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        inspect_csv(
            args.file,
            encoding=args.encoding,
            separator=args.sep,
            nrows=args.nrows,
            low_cardinality=args.low_cardinality,
        )


def command_catalog_stats(args: argparse.Namespace) -> None:
    """Calcule les statistiques d'un snapshot local du catalogue."""
    result = catalog_report.analyze_catalog(
        args.query,
        args.snapshot,
        producer=args.producer,
        license_name=args.license_name,
        frequency=args.frequency,
        resource_format=args.resource_format,
        top=args.top,
    )

    if getattr(args, "json", False):
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        catalog_report.print_catalog_report(result, args)


def build_parser() -> argparse.ArgumentParser:
    """Construit la CLI unifiée ``datagouv``."""
    parser = argparse.ArgumentParser(
        prog="datagouv",
        description=(
            "Explorer, télécharger, auditer et analyser des données de data.gouv.fr"
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Rechercher des jeux de données",
    )
    search_parser.add_argument("query", help="Texte recherché")
    search_parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=10,
        help="Nombre de résultats à afficher (défaut: 10)",
    )
    add_json_option(search_parser)
    search_parser.set_defaults(func=datagouv.command_search)

    dataset_parser = subparsers.add_parser(
        "dataset",
        help="Afficher le résumé d'un jeu de données",
    )
    add_dataset_selector(dataset_parser)
    add_json_option(dataset_parser)
    dataset_parser.set_defaults(func=datagouv.command_dataset)

    resources_parser = subparsers.add_parser(
        "resources",
        help="Lister les ressources d'un jeu de données",
    )
    add_dataset_selector(resources_parser)
    add_json_option(resources_parser)
    resources_parser.set_defaults(func=datagouv.command_resources)

    metadata_parser = subparsers.add_parser(
        "metadata",
        help="Afficher les métadonnées principales d'un jeu de données",
    )
    add_dataset_selector(metadata_parser)
    add_json_option(metadata_parser)
    metadata_parser.set_defaults(func=datagouv.command_metadata)

    stats_parser = subparsers.add_parser(
        "stats",
        help="Afficher des statistiques sur les ressources d'un dataset",
    )
    add_dataset_selector(stats_parser)
    add_json_option(stats_parser)
    stats_parser.set_defaults(func=datagouv.command_stats)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Afficher le JSON brut d'un jeu de données",
    )
    add_dataset_selector(inspect_parser)
    inspect_parser.set_defaults(func=datagouv.command_inspect)

    organization_parser = subparsers.add_parser(
        "organization",
        help="Afficher une organisation data.gouv.fr",
    )
    organization_parser.add_argument(
        "organization_id",
        help="Identifiant de l'organisation",
    )
    add_json_option(organization_parser)
    organization_parser.set_defaults(func=datagouv.command_organization)

    download_parser = subparsers.add_parser(
        "download",
        help="Télécharger les ressources d'un dataset",
    )
    add_dataset_selector(download_parser)
    download_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Répertoire de destination",
    )
    download_parser.add_argument(
        "--format",
        dest="resource_format",
        help="Format des ressources à télécharger",
    )
    download_parser.add_argument(
        "--resource-title",
        help="Filtrer le titre des ressources",
    )
    download_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Écraser les fichiers locaux existants",
    )
    add_json_option(download_parser)
    download_parser.set_defaults(func=command_download)

    workflow_parser = subparsers.add_parser(
        "workflow",
        help="Télécharger puis auditer automatiquement les CSV",
    )
    add_dataset_selector(workflow_parser)
    workflow_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Répertoire de destination",
    )
    workflow_parser.add_argument(
        "--format",
        dest="resource_format",
        help="Format des ressources à sélectionner",
    )
    workflow_parser.add_argument(
        "--resource-title",
        help="Filtrer le titre des ressources",
    )
    workflow_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Écraser les fichiers locaux existants",
    )
    workflow_parser.add_argument(
        "--no-audit",
        action="store_true",
        help="Désactiver l'audit automatique des CSV",
    )
    workflow_parser.add_argument(
        "--audit-dir",
        type=Path,
        help="Répertoire dans lequel écrire les audits CSV",
    )
    add_json_option(workflow_parser)
    workflow_parser.set_defaults(func=command_workflow)

    csv_parser = subparsers.add_parser(
        "inspect-csv",
        help="Auditer un fichier CSV local",
    )
    csv_parser.add_argument("file", type=Path, help="Fichier CSV à analyser")
    csv_parser.add_argument("--encoding", help="Encodage à forcer")
    csv_parser.add_argument("--sep", help="Séparateur à forcer")
    csv_parser.add_argument(
        "--nrows",
        type=int,
        help="Limiter le chargement aux N premières lignes",
    )
    csv_parser.add_argument(
        "--low-cardinality",
        type=int,
        default=DEFAULT_LOW_CARDINALITY,
        help="Seuil de cardinalité pour afficher les distributions",
    )
    add_json_option(csv_parser)
    csv_parser.set_defaults(func=command_inspect_csv)

    catalog_parser = subparsers.add_parser(
        "catalog-stats",
        help="Analyser un snapshot local du catalogue data.gouv.fr",
    )
    catalog_parser.add_argument(
        "query",
        help="Texte recherché dans les métadonnées locales",
    )
    catalog_parser.add_argument(
        "--snapshot",
        type=Path,
        required=True,
        help="Répertoire contenant datasets.parquet et resources.parquet",
    )
    catalog_parser.add_argument(
        "--producer",
        help="Filtrer les datasets par producteur",
    )
    catalog_parser.add_argument(
        "--license",
        dest="license_name",
        help="Filtrer les datasets par licence",
    )
    catalog_parser.add_argument(
        "--frequency",
        help="Filtrer les datasets par fréquence",
    )
    catalog_parser.add_argument(
        "--format",
        dest="resource_format",
        help="Filtrer les ressources par format",
    )
    catalog_parser.add_argument(
        "--top",
        type=int,
        default=catalog_stats.DEFAULT_TOP,
        help="Nombre de valeurs affichées par classement (défaut: 15)",
    )
    add_json_option(catalog_parser)
    catalog_parser.set_defaults(func=command_catalog_stats)

    return parser


def main() -> int:
    """Point d'entrée de la CLI unifiée."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        args.func(args)
    except requests.HTTPError as exc:
        print(f"Erreur HTTP : {exc}", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"Erreur réseau : {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Erreur fichier : {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
