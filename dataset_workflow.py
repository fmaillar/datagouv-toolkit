from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from pathlib import Path

from datagouv import resolve_dataset
from download_resources import (
    download_resource,
    safe_filename,
    select_resources,
)
from inspect_csv import inspect_csv


def run_workflow(
    dataset_query: str,
    output_dir: Path,
    *,
    producer: str | None = None,
    dataset_title: str | None = None,
    resource_format: str | None = None,
    resource_title: str | None = None,
    overwrite: bool = False,
    audit_csv: bool = True,
    audit_dir: Path | None = None,
) -> None:
    dataset = resolve_dataset(
        dataset_query,
        producer=producer,
        title=dataset_title,
    )

    resources = select_resources(
        dataset,
        resource_format=resource_format,
        title=resource_title,
    )

    print(f"Dataset    : {dataset['title']}")
    print(f"Ressources : {len(resources)}")
    print(f"Destination: {output_dir.resolve()}")

    if not resources:
        raise SystemExit("Aucune ressource correspondante.")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for index, resource in enumerate(
        resources,
        start=1,
    ):
        filename = safe_filename(resource)
        destination = output_dir / filename

        print()
        print(f"[{index}/{len(resources)}] {filename}")

        downloaded = download_resource(
            resource,
            destination,
            overwrite=overwrite,
        )

        if downloaded:
            print("Téléchargement : OK")
        else:
            print("Téléchargement : SKIP")

        if audit_csv and destination.suffix.casefold() == ".csv":
            if audit_dir is None:
                print()
                print("Audit CSV")
                print("-" * 80)

                inspect_csv(destination)
            else:
                audit_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                audit_path = audit_dir / f"{destination.name}.audit.txt"

                with (
                    audit_path.open("w", encoding="utf-8") as file,
                    redirect_stdout(file),
                ):
                    inspect_csv(destination)

                print(f"Audit       : {audit_path}")


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
        resource_format=args.resource_format,
        resource_title=args.resource_title,
        overwrite=args.overwrite,
        audit_csv=not args.no_audit,
        audit_dir=args.audit_dir,
    )


if __name__ == "__main__":
    main()
