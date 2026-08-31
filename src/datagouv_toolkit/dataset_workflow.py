from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .datagouv import resolve_dataset
from .download_resources import download_resource, download_resources, select_resources
from .inspect_csv import analyze_csv, format_csv_audit


def build_csv_audit(path: Path) -> str:
    """Construit le rapport texte d'un audit CSV sans écrire sur stdout."""
    return format_csv_audit(analyze_csv(path))


def run_workflow(
    dataset_query: str,
    output_dir: Path,
    *,
    producer: str | None = None,
    dataset_title: str | None = None,
    first: bool = False,
    resource_format: str | None = None,
    resource_title: str | None = None,
    overwrite: bool = False,
    audit_csv: bool = True,
    audit_dir: Path | None = None,
    progress: bool = True,
) -> dict[str, Any]:
    dataset = resolve_dataset(
        dataset_query,
        producer=producer,
        title=dataset_title,
        first=first,
    )

    resources = select_resources(
        dataset,
        resource_format=resource_format,
        title=resource_title,
    )

    if progress:
        print(f"Dataset    : {dataset['title']}")
        print(f"Ressources : {len(resources)}")
        print(f"Destination: {output_dir.resolve()}")

    if not resources:
        raise SystemExit("Aucune ressource correspondante.")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = download_resources(
        resources,
        output_dir,
        overwrite=overwrite,
        progress=False,
        download_func=download_resource,
    )

    workflow_results: list[dict[str, Any]] = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        destination = result["path"]
        downloaded = result["downloaded"]
        audit_path: Path | None = None
        audited = False

        if progress:
            print()
            print(f"[{index}/{len(results)}] {destination.name}")
            if downloaded:
                print("Téléchargement : OK")
            else:
                print("Téléchargement : SKIP")

        if audit_csv and destination.suffix.casefold() == ".csv":
            audited = True
            report = build_csv_audit(destination)

            if audit_dir is None:
                if progress:
                    print()
                    print("Audit CSV")
                    print("-" * 80)
                    print(report)
            else:
                audit_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                audit_path = audit_dir / f"{destination.name}.audit.txt"
                audit_path.write_text(f"{report}\n", encoding="utf-8")

                if progress:
                    print(f"Audit       : {audit_path}")

        workflow_results.append(
            {
                "resource": result["resource"],
                "path": destination,
                "downloaded": downloaded,
                "audited": audited,
                "audit_path": audit_path,
            }
        )

    return {
        "dataset": dataset,
        "destination": output_dir.resolve(),
        "resources": workflow_results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Résout un dataset data.gouv.fr, télécharge ses ressources "
            "et audite automatiquement les CSV."
        ),
    )

    parser.add_argument(
        "dataset",
        help="ID ou texte permettant d'identifier le dataset.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Répertoire de destination.",
    )
    parser.add_argument(
        "--producer",
        help="Filtre sur le producteur.",
    )
    parser.add_argument(
        "--dataset-title",
        help="Filtre supplémentaire sur le titre du dataset.",
    )
    parser.add_argument(
        "--first",
        action="store_true",
        help="Sélectionne le premier résultat sans choix interactif.",
    )
    parser.add_argument(
        "--format",
        dest="resource_format",
        help="Format des ressources à sélectionner.",
    )
    parser.add_argument(
        "--resource-title",
        help="Sous-chaîne du titre des ressources.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Écrase les fichiers déjà présents.",
    )
    parser.add_argument(
        "--no-audit",
        action="store_true",
        help="Désactive l'audit automatique des CSV.",
    )
    parser.add_argument(
        "--audit-dir",
        type=Path,
        help="Répertoire dans lequel écrire les audits CSV.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    run_workflow(
        args.dataset,
        args.output,
        producer=args.producer,
        dataset_title=args.dataset_title,
        first=args.first,
        resource_format=args.resource_format,
        resource_title=args.resource_title,
        overwrite=args.overwrite,
        audit_csv=not args.no_audit,
        audit_dir=args.audit_dir,
    )


if __name__ == "__main__":
    main()
