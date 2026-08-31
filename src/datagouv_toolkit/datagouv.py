"""Fonctions métier pour explorer le catalogue data.gouv.fr.

Ce module regroupe l'accès à l'API catalogue, la résolution des jeux de
données, l'affichage des métadonnées et le calcul de statistiques sur leurs
ressources.

La construction et le dispatch de la ligne de commande ``datagouv`` sont
assurés par :mod:`cli`.

Les opérations sur l'API sont effectuées en lecture seule.
"""

import json
import re
from collections import Counter
from urllib.parse import urlparse

import requests

API_BASE = "https://www.data.gouv.fr/api/1"
TIMEOUT = 30


def get_json(url, params=None):
    """Effectue une requête HTTP GET et retourne la réponse JSON décodée.

    Parameters
    ----------
    url:
        URL à interroger.
    params:
        Paramètres de requête optionnels transmis à ``requests.get``.

    Returns
    -------
    object
        Objet Python issu du décodage JSON.

    Raises
    ------
    requests.HTTPError
        Si le serveur retourne un statut HTTP en erreur.
    requests.RequestException
        En cas d'erreur réseau.
    """
    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def search_datasets(query, page_size=10):
    """Recherche des jeux de données dans le catalogue data.gouv.fr.

    Parameters
    ----------
    query:
        Texte recherché.
    page_size:
        Nombre maximal de résultats demandés à l'API.

    Returns
    -------
    dict
        Réponse JSON de l'endpoint ``/datasets/``.
    """
    url = f"{API_BASE}/datasets/"
    params = {
        "q": query,
        "page_size": page_size,
    }
    return get_json(url, params=params)


def get_dataset(dataset_id):
    """Récupère un jeu de données à partir de son identifiant data.gouv.fr."""
    url = f"{API_BASE}/datasets/{dataset_id}/"
    return get_json(url)


def resolve_dataset(
    value,
    page_size=20,
    producer=None,
    title=None,
    *,
    first=False,
):
    """Résout un jeu de données depuis son ID ou une recherche textuelle.

    Si ``value`` ressemble à un identifiant data.gouv.fr, le jeu est récupéré
    directement. Sinon, une recherche textuelle est effectuée puis filtrée
    éventuellement par producteur et par titre.

    Lorsqu'il reste plusieurs candidats, l'utilisateur choisit
    interactivement dans le terminal.

    Parameters
    ----------
    value:
        Identifiant data.gouv.fr ou texte de recherche.
    page_size:
        Nombre maximal de candidats récupérés lors de la recherche.
    producer:
        Sous-chaîne optionnelle recherchée dans le nom du producteur.
    title:
        Sous-chaîne optionnelle recherchée dans le titre.

    Returns
    -------
    dict
        Jeu de données complet retourné par l'API.

    Raises
    ------
    ValueError
        Si aucun jeu de données ne correspond aux critères.
    """

    # Les identifiants historiques de data.gouv.fr ont ici la forme
    # d'un ObjectId MongoDB : 24 caractères hexadécimaux.
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

    if len(datasets) == 1 or first:
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
        except EOFError:
            raise KeyboardInterrupt
        except ValueError:
            print("Entre un numéro valide.")
            continue

        if 1 <= choice <= len(datasets):
            dataset_id = datasets[choice - 1]["id"]
            return get_dataset(dataset_id)

        print(f"Choisis un nombre entre 1 et {len(datasets)}.")


def get_organization(org_id):
    """Récupère les métadonnées d'une organisation data.gouv.fr."""
    url = f"{API_BASE}/organizations/{org_id}/"
    return get_json(url)


def print_dataset_summary(dataset):
    """Affiche un résumé lisible d'un jeu de données."""
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
    """Affiche une liste compacte de résultats de recherche."""
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
    """Affiche les ressources associées à un jeu de données."""
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
    """Convertit une taille en octets vers une représentation lisible."""
    size = float(size)

    for unit in ("o", "Ko", "Mo", "Go", "To"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} Po"


def command_search(args):
    data = search_datasets(args.query, args.limit)

    if getattr(args, "json", False):
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
        return

    print_search_results(data)


def command_dataset(args):
    dataset = resolve_dataset(
        args.dataset,
        producer=args.producer,
        title=args.title,
        first=getattr(args, "first", False),
    )

    if getattr(args, "json", False):
        print(json.dumps(dataset, ensure_ascii=False, indent=2, sort_keys=True))
        return

    print_dataset_summary(dataset)

    description = dataset.get("description")

    if description:
        print()
        print("Description")
        print("-----------")
        print(description)


def command_resources(args):
    dataset = resolve_dataset(
        args.dataset,
        producer=args.producer,
        title=args.title,
        first=getattr(args, "first", False),
    )

    if getattr(args, "json", False):
        print(
            json.dumps(
                dataset.get("resources", []),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return

    print(dataset.get("title", "?"))
    print()

    print_resources(dataset)


def command_organization(args):
    organization = get_organization(args.organization_id)

    if getattr(args, "json", False):
        print(
            json.dumps(
                organization,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return

    print(organization.get("name", "?"))
    print(f"ID  : {organization.get('id', '?')}")
    print(f"URL : {organization.get('page', '?')}")

    description = organization.get("description")

    if description:
        print()
        print(description)


def dataset_stats(dataset):
    """Calcule des statistiques simples sur les ressources d'un dataset.

    Les statistiques incluent la répartition par format, les domaines
    d'hébergement, la somme des tailles connues et les années détectées dans
    les titres ou URL des ressources.

    Notes
    -----
    Certaines ressources data.gouv.fr n'ont pas de champ ``format``.
    Dans ce cas, le format est inféré depuis l'extension de l'URL lorsqu'elle
    appartient à un petit ensemble de formats connus.

    Les années détectées constituent une heuristique descriptive ; elles ne
    doivent pas être interprétées comme une couverture temporelle officielle.
    """
    resources = dataset.get("resources", [])

    formats = Counter()
    domains = Counter()
    years = set()

    total_size = 0
    unknown_size = 0

    for resource in resources:
        fmt = resource.get("format")

        if not fmt:
            # Les métadonnées de certaines ressources omettent le format.
            # On tente alors de l'inférer depuis l'extension de l'URL.
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
    dataset = resolve_dataset(
        args.dataset,
        producer=args.producer,
        title=args.title,
        first=getattr(args, "first", False),
    )
    stats = dataset_stats(dataset)

    if getattr(args, "json", False):
        payload = {
            **stats,
            "formats": dict(stats["formats"]),
            "domains": dict(stats["domains"]),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return

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
    """Affiche le JSON brut complet d'un jeu de données."""
    dataset = resolve_dataset(
        args.dataset,
        producer=args.producer,
        title=args.title,
        first=getattr(args, "first", False),
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
    """Convertit une valeur de métadonnée en texte lisible pour le terminal."""
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
    """Affiche un dictionnaire en privilégiant certains champs connus.

    Les clés reconnues sont affichées sous forme tabulaire. Les clés restantes
    sont conservées et affichées ensuite en JSON afin de ne perdre aucune
    métadonnée exposée par l'API.
    """
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
    """Affiche une vue structurée des principales métadonnées d'un dataset."""
    dataset = resolve_dataset(
        args.dataset,
        producer=args.producer,
        title=args.title,
        first=getattr(args, "first", False),
    )

    organization = dataset.get("organization")

    if organization:
        producer = organization.get("name", "?")
    else:
        owner = dataset.get("owner")
        producer = owner.get("name", "?") if owner else "?"

    if getattr(args, "json", False):
        payload = {
            "title": dataset.get("title"),
            "id": dataset.get("id"),
            "producer": producer,
            "license": dataset.get("license"),
            "created_at": dataset.get("created_at"),
            "last_modified": dataset.get("last_modified"),
            "last_update": dataset.get("last_update"),
            "frequency": dataset.get("frequency"),
            "frequency_date": dataset.get("frequency_date"),
            "tags": dataset.get("tags"),
            "temporal_coverage": dataset.get("temporal_coverage"),
            "spatial": dataset.get("spatial"),
            "resources": len(dataset.get("resources", [])),
            "page": dataset.get("page"),
            "quality": dataset.get("quality"),
            "metrics": dataset.get("metrics"),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return

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
