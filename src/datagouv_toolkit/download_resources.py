from __future__ import annotations

import argparse
from pathlib import Path

import requests

from .datagouv import resolve_dataset
from .normalize import normalize_format

CHUNK_SIZE = 1024 * 1024


def select_resources(
    dataset: dict,
    *,
    resource_format: str | None = None,
    title: str | None = None,
) -> list[dict]:
    """Sélectionne les ressources selon des filtres optionnels."""
    resources = dataset.get("resources", [])

    selected = []

    for resource in resources:
        if resource_format is not None:
            actual_format = normalize_format(resource.get("format"))
            expected_format = normalize_format(resource_format)

            if actual_format != expected_format:
                continue

        if title is not None:
            resource_title = str(resource.get("title") or "")

            if title.casefold() not in resource_title.casefold():
                continue

        selected.append(resource)

    return selected


def safe_filename(resource: dict) -> str:
    """Retourne un nom de fichier exploitable pour une ressource."""
    title = str(resource.get("title") or "").strip()

    if title:
        return Path(title).name

    resource_id = str(resource.get("id") or "resource")
    return resource_id


def download_resource(
    resource: dict,
    destination: Path,
    *,
    overwrite: bool = False,
) -> bool:
    """
    Télécharge une ressource.

    Retourne True si le fichier a été téléchargé,
    False s'il existait déjà.
    """
    if destination.exists() and not overwrite:
        return False

    url = resource.get("url")

    if not url:
        raise ValueError(
            f"Ressource sans URL : {resource.get('title') or resource.get('id')}"
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = destination.with_suffix(
        destination.suffix + ".part",
    )

    try:
        with requests.get(
            url,
            stream=True,
            timeout=60,
        ) as response:
            response.raise_for_status()

            with temporary.open("wb") as file:
                for chunk in response.iter_content(
                    chunk_size=CHUNK_SIZE,
                ):
                    if chunk:
                        file.write(chunk)

        temporary.replace(destination)

    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    return True


def download_resources(
    resources: list[dict],
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> list[dict]:
    """Télécharge une liste de ressources et retourne le résultat de chacune."""
    total = len(resources)
    results = []

    for index, resource in enumerate(
        resources,
        start=1,
    ):
        filename = safe_filename(resource)
        destination = output_dir / filename

        if destination.exists() and not overwrite:
            print(f"[{index}/{total}] SKIP {filename}")
            results.append(
                {
                    "resource": resource,
                    "path": destination,
                    "downloaded": False,
                }
            )
            continue

        print(f"[{index}/{total}] GET  {filename}")

        downloaded = download_resource(
            resource,
            destination,
            overwrite=overwrite,
        )
        results.append(
            {
                "resource": resource,
                "path": destination,
                "downloaded": downloaded,
            }
        )

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Télécharge les ressources d'un dataset data.gouv.fr.",
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
        help="Filtre sur le producteur du dataset.",
    )
    parser.add_argument(
        "--dataset-title",
        help="Filtre supplémentaire sur le titre du dataset.",
    )
    parser.add_argument(
        "--format",
        dest="resource_format",
        help="Format des ressources à télécharger.",
    )
    parser.add_argument(
        "--resource-title",
        help="Sous-chaîne à rechercher dans le titre des ressources.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Écrase les fichiers locaux existants.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    dataset = resolve_dataset(
        args.dataset,
        producer=args.producer,
        title=args.dataset_title,
    )

    resources = select_resources(
        dataset,
        resource_format=args.resource_format,
        title=args.resource_title,
    )

    print(f"Dataset    : {dataset['title']}")
    print(f"Ressources : {len(resources)}")
    print(f"Destination: {args.output.resolve()}")

    if not resources:
        raise SystemExit("Aucune ressource correspondante.")

    download_resources(
        resources,
        args.output,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
