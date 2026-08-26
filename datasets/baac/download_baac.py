#!/usr/bin/env python3

from __future__ import annotations

import re
from pathlib import Path

from datagouv import resolve_dataset
from download_resources import download_resource

DATASET_QUERY = "accidents corporels"
PRODUCER = "Ministère de l'intérieur"

OUTPUT_DIR = Path("datasets/baac")

YEAR_MIN = 2005
YEAR_MAX = 2024

RESOURCE_RE = re.compile(
    r"^(?P<table>"
    r"caract(?:eristiques)?"
    r"|carcteristiques"
    r"|lieux"
    r"|vehicules"
    r"|usagers"
    r")[-_](?P<year>20\d{2})\.csv$",
    re.IGNORECASE,
)

CANONICAL_NAMES = {
    "caracteristiques": "Caract_{year}.csv",
    "lieux": "Lieux_{year}.csv",
    "vehicules": "Vehicules_{year}.csv",
    "usagers": "Usagers_{year}.csv",
}


def normalize_table(value: str) -> str:
    value = value.casefold()

    if value.startswith(("caract", "carcter")):
        return "caracteristiques"

    return value


def classify_resource(
    resource: dict,
) -> tuple[int, str] | None:
    """Identifie une ressource BAAC annuelle canonique."""
    title = str(resource.get("title") or "").strip()

    match = RESOURCE_RE.fullmatch(title)

    if match is None:
        return None

    year = int(match.group("year"))

    if not YEAR_MIN <= year <= YEAR_MAX:
        return None

    table = normalize_table(match.group("table"))

    return year, table


def select_baac_resources(
    dataset: dict,
) -> dict[tuple[int, str], dict]:
    """Sélectionne exactement les quatre tables annuelles BAAC."""
    selected: dict[tuple[int, str], dict] = {}

    for resource in dataset.get("resources", []):
        result = classify_resource(resource)

        if result is None:
            continue

        year, table = result
        key = (year, table)

        if key in selected:
            previous = selected[key]

            raise RuntimeError(
                "Plusieurs ressources correspondent à "
                f"{year} / {table} :\n"
                f"  - {previous.get('title')}\n"
                f"  - {resource.get('title')}"
            )

        selected[key] = resource

    return selected


def validate_resources(
    resources: dict[tuple[int, str], dict],
) -> None:
    """Vérifie la présence des 4 × 20 ressources attendues."""
    missing: list[tuple[int, str]] = []

    for year in range(YEAR_MIN, YEAR_MAX + 1):
        for table in CANONICAL_NAMES:
            if (year, table) not in resources:
                missing.append((year, table))

    if missing:
        print()
        print("Ressources manquantes")
        print("---------------------")

        for year, table in missing:
            print(f"{year}  {table}")

        raise RuntimeError(f"{len(missing)} ressource(s) BAAC manquante(s)")


def print_inventory(
    resources: dict[tuple[int, str], dict],
) -> None:
    """Affiche l'inventaire avant téléchargement."""
    print()
    print("Inventaire BAAC")
    print("---------------")

    for year in range(YEAR_MIN, YEAR_MAX + 1):
        for table in CANONICAL_NAMES:
            resource = resources[(year, table)]

            print(f"{year}  {table:17}  {resource.get('title')}")

    print()
    print(f"Total : {len(resources)} ressources")


def download_all(
    resources: dict[tuple[int, str], dict],
) -> None:
    """Télécharge les ressources dans un répertoire par année."""
    total = len(resources)
    index = 0

    for year in range(YEAR_MIN, YEAR_MAX + 1):
        year_dir = OUTPUT_DIR / str(year)

        for table, filename_template in CANONICAL_NAMES.items():
            index += 1

            resource = resources[(year, table)]

            filename = filename_template.format(year=year)
            destination = year_dir / filename

            if destination.exists():
                print(f"[{index}/{total}] SKIP {year}/{filename}")
                continue

            print(f"[{index}/{total}] GET  {year}/{filename}")

            download_resource(
                resource,
                destination,
            )


def main() -> None:
    dataset = resolve_dataset(
        DATASET_QUERY,
        producer=PRODUCER,
    )

    print("Dataset :", dataset["title"])

    resources = select_baac_resources(dataset)

    print(f"Ressources BAAC détectées : {len(resources)}")

    validate_resources(resources)
    print_inventory(resources)

    download_all(resources)


if __name__ == "__main__":
    main()
