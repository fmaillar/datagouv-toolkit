#!/usr/bin/env python3

import argparse
import json
import re
import sys
from collections import Counter
from urllib.parse import urlparse

import requests

API_BASE = "https://www.data.gouv.fr/api/1"
TIMEOUT = 30


def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def search_datasets(query, page_size=10):
    url = f"{API_BASE}/datasets/"
    params = {
        "q": query,
        "page_size": page_size,
    }
    return get_json(url, params=params)


def get_dataset(dataset_id):
    url = f"{API_BASE}/datasets/{dataset_id}/"
    return get_json(url)


def resolve_dataset(value, page_size=20, producer=None, title=None):
    """Résout un jeu de données depuis son ID ou une recherche textuelle."""

    if re.fullmatch(r"[0-9a-fA-F]{24}", value):
        return get_dataset(value)

    data = search_datasets(value, page_size=page_size)
    datasets = data.get("data", [])

    if producer:
        producer_lower = producer.casefold()
        datasets = [
            dataset
            for dataset in datasets
            if dataset.get("organization")
            and producer_lower in dataset["organization"].get("name", "").casefold()
        ]

    if title:
        title_lower = title.casefold()
        datasets = [
            dataset
            for dataset in datasets
            if title_lower in dataset.get("title", "").casefold()
        ]

    if not datasets:
        raise ValueError(f"Aucun jeu de données trouvé pour : {value}")

    if len(datasets) == 1:
        return get_dataset(datasets[0]["id"])

    print(f"{len(datasets)} résultat(s) trouvé(s)")
    print()

    for index, dataset in enumerate(datasets, start=1):
        organization = dataset.get("organization")

        if organization:
            producer = organization.get("name", "?")
        else:
            owner = dataset.get("owner")
            producer = owner.get("name", "?") if owner else "?"

        print(f"[{index}] {dataset.get('title', '?')}")
        print(f"    Producteur : {producer}")
        print()

    while True:
        try:
            choice = int(input("Choix : "))
        except (ValueError, EOFError):
            print("Entre un numéro valide.")
            continue

        if 1 <= choice <= len(datasets):
            dataset_id = datasets[choice - 1]["id"]
            return get_dataset(dataset_id)

        print(f"Choisis un nombre entre 1 et {len(datasets)}.")


def get_organization(org_id):
    url = f"{API_BASE}/organizations/{org_id}/"
    return get_json(url)


def print_dataset_summary(dataset):
    organization = dataset.get("organization")

    if organization:
        producer = organization.get("name", "?")
    else:
        owner = dataset.get("owner")
        producer = owner.get("name", "?") if owner else "?"

    print(dataset.get("title", "?"))
    print(f"ID         : {dataset.get('id', '?')}")
    print(f"Producteur : {producer}")
    print(f"Mis à jour : {dataset.get('last_update', '?')}")

    license_name = dataset.get("license")
    print(f"Licence    : {license_name or '?'}")

    resources = dataset.get("resources", [])
    print(f"Ressources : {len(resources)}")


def print_search_results(data):
    datasets = data.get("data", [])

    total = data.get("total", "?")

    print(f"{total} résultat(s) trouvé(s), {len(datasets)} affiché(s)")
    print()

    for index, dataset in enumerate(datasets, start=1):
        print(f"[{index}] {dataset.get('title', '?')}")
        print(f"    ID : {dataset.get('id', '?')}")

        organization = dataset.get("organization")
        if organization:
            print(f"    Producteur : {organization.get('name', '?')}")

        print()


def print_resources(dataset):
    resources = dataset.get("resources", [])

    if not resources:
        print("Aucune ressource.")
        return

    for index, resource in enumerate(resources, start=1):
        title = resource.get("title") or "sans titre"
        fmt = resource.get("format") or "?"
        url = resource.get("url") or "?"
        filesize = resource.get("filesize")

        print(f"[{index}] {title}")
        print(f"    Format : {fmt}")

        if filesize is not None:
            print(f"    Taille : {format_size(filesize)}")

        print(f"    URL    : {url}")
        print()


def format_size(size):
    size = float(size)

    for unit in ("o", "Ko", "Mo", "Go", "To"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} Po"


def command_search(args):
    data = search_datasets(args.query, args.limit)
    print_search_results(data)


def command_dataset(args):
    dataset = resolve_dataset(args.dataset, producer=args.producer, title=args.title)

    print_dataset_summary(dataset)

    description = dataset.get("description")

    if description:
        print()
        print("Description")
        print("-----------")
        print(description)


def command_resources(args):
    dataset = resolve_dataset(args.dataset, producer=args.producer, title=args.title)

    print(dataset.get("title", "?"))
    print()

    print_resources(dataset)


def command_organization(args):
    organization = get_organization(args.organization_id)

    print(organization.get("name", "?"))
    print(f"ID  : {organization.get('id', '?')}")
    print(f"URL : {organization.get('page', '?')}")

    description = organization.get("description")

    if description:
        print()
        print(description)


def dataset_stats(dataset):
    resources = dataset.get("resources", [])

    formats = Counter()
    domains = Counter()
    years = set()

    total_size = 0
    unknown_size = 0

    for resource in resources:
        fmt = resource.get("format")

        if not fmt:
            url = resource.get("url", "")
            suffix = url.rsplit(".", 1)[-1].lower() if "." in url else ""

            if suffix in {"csv", "pdf", "json", "geojson", "zip", "xlsx", "xls"}:
                fmt = suffix
            else:
                fmt = "?"

        formats[fmt.lower()] += 1

        filesize = resource.get("filesize")

        if filesize is None:
            unknown_size += 1
        else:
            total_size += filesize

        url = resource.get("url")

        if url:
            domain = urlparse(url).netloc
            if domain:
                domains[domain] += 1

        text = " ".join(
            filter(
                None,
                [
                    resource.get("title"),
                    resource.get("url"),
                ],
            )
        )

        for year in re.findall(r"\b(?:19|20)\d{2}\b", text):
            years.add(int(year))

    return {
        "resources": len(resources),
        "formats": formats,
        "domains": domains,
        "total_size": total_size,
        "unknown_size": unknown_size,
        "years": sorted(years),
    }


def command_stats(args):
    dataset = resolve_dataset(args.dataset, producer=args.producer, title=args.title)
    stats = dataset_stats(dataset)

    print(dataset.get("title", "?"))
    print()

    print(f"Ressources totales : {stats['resources']}")
    print()

    print("Formats")
    print("-------")

    for fmt, count in stats["formats"].most_common():
        print(f"{fmt:10} {count:5}")

    print()

    if stats["total_size"] == 0 and stats["unknown_size"] == stats["resources"]:
        print("Taille connue      : inconnue")
    else:
        print(f"Taille connue      : {format_size(stats['total_size'])}")

    print(f"Taille inconnue    : {stats['unknown_size']} ressource(s)")

    print()
    print("Domaines")
    print("--------")

    for domain, count in stats["domains"].most_common():
        print(f"{domain:35} {count:5}")

    if stats["years"]:
        print()
        print(f"Période détectée   : {stats['years'][0]} → {stats['years'][-1]}")
        print("Années détectées   : " + ", ".join(map(str, stats["years"])))


def command_inspect(args):
    dataset = resolve_dataset(
        args.dataset,
        producer=args.producer,
        title=args.title,
    )

    print(
        json.dumps(
            dataset,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


def format_metadata_value(value):
    if value is None:
        return "?"

    if isinstance(value, bool):
        return "oui" if value else "non"

    if isinstance(value, list):
        if not value:
            return "?"
        if all(isinstance(item, str) for item in value):
            return ", ".join(value)
        return json.dumps(value, ensure_ascii=False)

    if isinstance(value, dict):
        if not value:
            return "?"
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def print_mapping_section(title, data, known_fields):
    print()
    print(title)
    print("-" * len(title))

    if not data:
        print("?")
        return

    remaining = dict(data)

    for key, label in known_fields:
        if key not in data:
            continue

        value = data[key]
        remaining.pop(key, None)

        if isinstance(value, bool):
            value = "oui" if value else "non"

        elif isinstance(value, float):
            value = f"{value:.2f}"

        width = max(len(label) for _, label in known_fields)
        print(f"{label:<{width}} : {value}")

    if remaining:
        print()
        print(f"Autres {title.lower()}")
        print("-" * (7 + len(title)))

        print(
            json.dumps(
                remaining,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )


def command_metadata(args):
    dataset = resolve_dataset(
        args.dataset,
        producer=args.producer,
        title=args.title,
    )

    organization = dataset.get("organization")

    if organization:
        producer = organization.get("name", "?")
    else:
        owner = dataset.get("owner")
        producer = owner.get("name", "?") if owner else "?"

    fields = [
        ("Titre", dataset.get("title")),
        ("ID", dataset.get("id")),
        ("Producteur", producer),
        ("Licence", dataset.get("license")),
        ("Créé le", dataset.get("created_at")),
        ("Dernière modification", dataset.get("last_modified")),
        ("Dernière mise à jour", dataset.get("last_update")),
        ("Fréquence", dataset.get("frequency")),
        ("Prochaine fréquence", dataset.get("frequency_date")),
        ("Tags", dataset.get("tags")),
        ("Couverture temporelle", dataset.get("temporal_coverage")),
        ("Couverture spatiale", dataset.get("spatial")),
        ("Ressources", len(dataset.get("resources", []))),
        ("Page", dataset.get("page")),
    ]

    width = max(len(label) for label, _ in fields)

    for label, value in fields:
        print(f"{label:<{width}} : {format_metadata_value(value)}")

    quality_fields = [
        ("score", "Score"),
        ("all_resources_available", "Ressources disponibles"),
        ("dataset_description_quality", "Description"),
        ("has_open_format", "Format ouvert"),
        ("has_resources", "Ressources présentes"),
        ("license", "Licence renseignée"),
        ("resources_documentation", "Documentation"),
        ("spatial", "Couverture spatiale"),
        ("temporal_coverage", "Couverture temporelle"),
        ("update_frequency", "Fréquence renseignée"),
        ("update_fulfilled_in_time", "Mise à jour dans les temps"),
    ]

    metrics_fields = [
        ("views", "Vues"),
        ("resources_downloads", "Téléchargements"),
        ("reuses", "Réutilisations"),
        ("followers", "Followers"),
        ("discussions", "Discussions"),
        ("discussions_open", "Discussions ouvertes"),
        ("dataservices", "Dataservices"),
    ]

    print_mapping_section(
        "Qualité",
        dataset.get("quality"),
        quality_fields,
    )

    print_mapping_section(
        "Métriques",
        dataset.get("metrics"),
        metrics_fields,
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description="Client minimal pour l'API catalogue data.gouv.fr"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Rechercher des jeux de données",
    )
    search_parser.add_argument(
        "query",
        help="Texte recherché",
    )
    search_parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=10,
        help="Nombre de résultats à afficher (défaut: 10)",
    )
    search_parser.set_defaults(func=command_search)

    dataset_parser = subparsers.add_parser(
        "dataset",
        help="Afficher les métadonnées d'un jeu de données",
    )
    dataset_parser.add_argument(
        "dataset",
        help="Identifiant ou texte de recherche du jeu de données",
    )
    dataset_parser.add_argument(
        "--producer",
        help="Filtrer par nom de producteur",
    )
    dataset_parser.add_argument(
        "--title",
        help="Filtrer par texte présent dans le titre",
    )
    dataset_parser.set_defaults(func=command_dataset)

    resources_parser = subparsers.add_parser(
        "resources",
        help="Lister les ressources d'un jeu de données",
    )
    resources_parser.add_argument(
        "dataset",
        help="Identifiant ou texte de recherche du jeu de données",
    )
    resources_parser.add_argument(
        "--producer",
        help="Filtrer par nom de producteur",
    )
    resources_parser.add_argument(
        "--title",
        help="Filtrer par texte présent dans le titre",
    )
    resources_parser.set_defaults(func=command_resources)

    organization_parser = subparsers.add_parser(
        "organization",
        help="Afficher une organisation",
    )
    organization_parser.add_argument(
        "organization_id",
        help="Identifiant de l'organisation",
    )
    organization_parser.set_defaults(func=command_organization)

    stats_parser = subparsers.add_parser(
        "stats",
        help="Afficher des statistiques sur les ressources d'un jeu de données",
    )
    stats_parser.add_argument(
        "dataset",
        help="Identifiant ou texte de recherche du jeu de données",
    )
    stats_parser.add_argument(
        "--producer",
        help="Filtrer par nom de producteur",
    )
    stats_parser.add_argument(
        "--title",
        help="Filtrer par texte présent dans le titre",
    )
    stats_parser.set_defaults(func=command_stats)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Afficher toutes les métadonnées JSON d'un jeu de données",
    )
    inspect_parser.add_argument(
        "dataset",
        help="Identifiant ou texte de recherche du jeu de données",
    )
    inspect_parser.add_argument(
        "--producer",
        help="Filtrer par nom de producteur",
    )
    inspect_parser.add_argument(
        "--title",
        help="Filtrer par texte présent dans le titre",
    )
    inspect_parser.set_defaults(func=command_inspect)

    metadata_parser = subparsers.add_parser(
        "metadata",
        help="Afficher les métadonnées principales d'un jeu de données",
    )
    metadata_parser.add_argument(
        "dataset",
        help="Identifiant ou texte de recherche du jeu de données",
    )
    metadata_parser.add_argument(
        "--producer",
        help="Filtrer par nom de producteur",
    )
    metadata_parser.add_argument(
        "--title",
        help="Filtrer par texte présent dans le titre",
    )
    metadata_parser.set_defaults(func=command_metadata)

    return parser


def main():
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

    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130

    except ValueError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
