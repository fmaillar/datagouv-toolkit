import json
from argparse import Namespace

import pytest
import requests

import datagouv as module


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self.payload


def test_get_json(monkeypatch):
    response = FakeResponse({"ok": True})
    calls = []

    def fake_get(url, *, params=None, timeout=None):
        calls.append((url, params, timeout))
        return response

    monkeypatch.setattr(module.requests, "get", fake_get)

    result = module.get_json(
        "https://example.test",
        params={"q": "abc"},
    )

    assert result == {"ok": True}
    assert response.raise_called is True
    assert calls == [
        (
            "https://example.test",
            {"q": "abc"},
            module.TIMEOUT,
        )
    ]


def test_search_datasets(monkeypatch):
    calls = []

    def fake_get_json(url, params=None):
        calls.append((url, params))
        return {"data": []}

    monkeypatch.setattr(module, "get_json", fake_get_json)

    result = module.search_datasets("transport", page_size=25)

    assert result == {"data": []}
    assert calls == [
        (
            f"{module.API_BASE}/datasets/",
            {
                "q": "transport",
                "page_size": 25,
            },
        )
    ]


def test_get_dataset(monkeypatch):
    monkeypatch.setattr(
        module,
        "get_json",
        lambda url: {"url": url},
    )

    result = module.get_dataset("abc")

    assert result == {"url": f"{module.API_BASE}/datasets/abc/"}


def test_get_organization(monkeypatch):
    monkeypatch.setattr(
        module,
        "get_json",
        lambda url: {"url": url},
    )

    result = module.get_organization("org")

    assert result == {"url": f"{module.API_BASE}/organizations/org/"}


def test_resolve_dataset_by_id(monkeypatch):
    dataset_id = "0123456789abcdef01234567"

    monkeypatch.setattr(
        module,
        "get_dataset",
        lambda value: {"id": value},
    )

    assert module.resolve_dataset(dataset_id) == {"id": dataset_id}


def test_resolve_dataset_single_result(monkeypatch):
    monkeypatch.setattr(
        module,
        "search_datasets",
        lambda *args, **kwargs: {"data": [{"id": "one"}]},
    )
    monkeypatch.setattr(
        module,
        "get_dataset",
        lambda value: {"id": value, "full": True},
    )

    assert module.resolve_dataset("transport") == {
        "id": "one",
        "full": True,
    }


def test_resolve_dataset_filters_producer_and_title(monkeypatch):
    monkeypatch.setattr(
        module,
        "search_datasets",
        lambda *args, **kwargs: {
            "data": [
                {
                    "id": "a",
                    "title": "Transport Toulouse",
                    "organization": {"name": "Toulouse Métropole"},
                },
                {
                    "id": "b",
                    "title": "Énergie Toulouse",
                    "organization": {"name": "Toulouse Métropole"},
                },
                {
                    "id": "c",
                    "title": "Transport Rennes",
                    "organization": {"name": "Rennes Métropole"},
                },
            ]
        },
    )
    monkeypatch.setattr(
        module,
        "get_dataset",
        lambda value: {"id": value},
    )

    result = module.resolve_dataset(
        "transport",
        producer="toulouse",
        title="TRANSPORT",
    )

    assert result == {"id": "a"}


def test_resolve_dataset_rejects_empty_result(monkeypatch):
    monkeypatch.setattr(
        module,
        "search_datasets",
        lambda *args, **kwargs: {"data": []},
    )

    with pytest.raises(
        ValueError,
        match="Aucun jeu de données",
    ):
        module.resolve_dataset("missing")


def test_resolve_dataset_interactive(monkeypatch, capsys):
    datasets = [
        {
            "id": "a",
            "title": "Dataset A",
            "organization": {"name": "Org A"},
        },
        {
            "id": "b",
            "title": "Dataset B",
            "organization": None,
            "owner": {"name": "Owner B"},
        },
    ]

    monkeypatch.setattr(
        module,
        "search_datasets",
        lambda *args, **kwargs: {"data": datasets},
    )
    monkeypatch.setattr(
        module,
        "get_dataset",
        lambda value: {"id": value},
    )

    answers = iter(["abc", "0", "2"])
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    result = module.resolve_dataset("dataset")

    assert result == {"id": "b"}

    output = capsys.readouterr().out
    assert "2 résultat(s) trouvé(s)" in output
    assert "Org A" in output
    assert "Owner B" in output
    assert "Entre un numéro valide." in output
    assert "Choisis un nombre entre 1 et 2." in output


def test_print_dataset_summary_with_organization(capsys):
    module.print_dataset_summary(
        {
            "title": "Dataset",
            "id": "abc",
            "organization": {"name": "Example Org"},
            "last_update": "2026-01-01",
            "license": "odbl",
            "resources": [{}, {}],
        }
    )

    output = capsys.readouterr().out

    assert "Dataset" in output
    assert "abc" in output
    assert "Example Org" in output
    assert "odbl" in output
    assert "Ressources : 2" in output


def test_print_dataset_summary_owner_fallback(capsys):
    module.print_dataset_summary(
        {
            "title": "Dataset",
            "owner": {"name": "Example Owner"},
        }
    )

    assert "Example Owner" in capsys.readouterr().out


def test_print_search_results(capsys):
    module.print_search_results(
        {
            "total": 3,
            "data": [
                {
                    "title": "A",
                    "id": "a",
                    "organization": {"name": "Org"},
                },
                {
                    "title": "B",
                    "id": "b",
                },
            ],
        }
    )

    output = capsys.readouterr().out

    assert "3 résultat(s) trouvé(s), 2 affiché(s)" in output
    assert "Producteur : Org" in output
    assert "[2] B" in output


def test_print_resources_empty(capsys):
    module.print_resources({"resources": []})

    assert capsys.readouterr().out.strip() == "Aucune ressource."


def test_print_resources(capsys):
    module.print_resources(
        {
            "resources": [
                {
                    "title": "data.csv",
                    "format": "csv",
                    "filesize": 1024,
                    "url": "https://example.test/data.csv",
                },
                {
                    "title": None,
                    "format": None,
                    "filesize": None,
                    "url": None,
                },
            ]
        }
    )

    output = capsys.readouterr().out

    assert "data.csv" in output
    assert "1.0 Ko" in output
    assert "sans titre" in output
    assert "Format : ?" in output


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0.0 o"),
        (1024, "1.0 Ko"),
        (1024**2, "1.0 Mo"),
        (1024**3, "1.0 Go"),
        (1024**4, "1.0 To"),
        (1024**5, "1.0 Po"),
    ],
)
def test_format_size(size, expected):
    assert module.format_size(size) == expected


def test_dataset_stats():
    dataset = {
        "resources": [
            {
                "title": "Export 2024",
                "format": "CSV",
                "filesize": 100,
                "url": "https://static.example.test/data-2024.csv",
            },
            {
                "title": "Archive 2023",
                "format": None,
                "filesize": None,
                "url": "https://files.example.test/archive-2023.zip",
            },
            {
                "title": "Unknown 1999",
                "format": None,
                "filesize": 50,
                "url": "https://example.test/no-extension",
            },
        ]
    }

    stats = module.dataset_stats(dataset)

    assert stats["resources"] == 3
    assert stats["formats"]["csv"] == 1
    assert stats["formats"]["zip"] == 1
    assert stats["formats"]["?"] == 1
    assert stats["domains"] == {
        "static.example.test": 1,
        "files.example.test": 1,
        "example.test": 1,
    }
    assert stats["total_size"] == 150
    assert stats["unknown_size"] == 1
    assert stats["years"] == [1999, 2023, 2024]


def test_command_search(monkeypatch):
    calls = []

    monkeypatch.setattr(
        module,
        "search_datasets",
        lambda query, limit: {
            "query": query,
            "limit": limit,
        },
    )

    monkeypatch.setattr(
        module,
        "print_search_results",
        lambda data: calls.append(data),
    )

    module.command_search(Namespace(query="transport", limit=5))

    assert calls == [
        {
            "query": "transport",
            "limit": 5,
        }
    ]


def test_command_dataset(monkeypatch, capsys):
    monkeypatch.setattr(
        module,
        "resolve_dataset",
        lambda *args, **kwargs: {
            "title": "Example",
            "description": "Description test",
        },
    )

    module.command_dataset(
        Namespace(
            dataset="example",
            producer=None,
            title=None,
        )
    )

    output = capsys.readouterr().out

    assert "Example" in output
    assert "Description" in output
    assert "Description test" in output


def test_command_resources(monkeypatch, capsys):
    monkeypatch.setattr(
        module,
        "resolve_dataset",
        lambda *args, **kwargs: {
            "title": "Example",
            "resources": [],
        },
    )

    module.command_resources(
        Namespace(
            dataset="example",
            producer=None,
            title=None,
        )
    )

    output = capsys.readouterr().out

    assert "Example" in output
    assert "Aucune ressource." in output


def test_command_organization(monkeypatch, capsys):
    monkeypatch.setattr(
        module,
        "get_organization",
        lambda value: {
            "name": "Example Org",
            "id": value,
            "page": "https://example.test/org",
            "description": "Description",
        },
    )

    module.command_organization(Namespace(organization_id="org-id"))

    output = capsys.readouterr().out

    assert "Example Org" in output
    assert "org-id" in output
    assert "Description" in output


def test_command_stats_unknown_size(monkeypatch, capsys):
    monkeypatch.setattr(
        module,
        "resolve_dataset",
        lambda *args, **kwargs: {
            "title": "Example",
        },
    )
    monkeypatch.setattr(
        module,
        "dataset_stats",
        lambda dataset: {
            "resources": 2,
            "formats": module.Counter({"csv": 2}),
            "domains": module.Counter({"example.test": 2}),
            "total_size": 0,
            "unknown_size": 2,
            "years": [2023, 2024],
        },
    )

    module.command_stats(
        Namespace(
            dataset="example",
            producer=None,
            title=None,
        )
    )

    output = capsys.readouterr().out

    assert "Taille connue      : inconnue" in output
    assert "example.test" in output
    assert "2023 → 2024" in output


def test_command_stats_known_size(monkeypatch, capsys):
    monkeypatch.setattr(
        module,
        "resolve_dataset",
        lambda *args, **kwargs: {
            "title": "Example",
        },
    )
    monkeypatch.setattr(
        module,
        "dataset_stats",
        lambda dataset: {
            "resources": 1,
            "formats": module.Counter({"csv": 1}),
            "domains": module.Counter(),
            "total_size": 1024,
            "unknown_size": 0,
            "years": [],
        },
    )

    module.command_stats(
        Namespace(
            dataset="example",
            producer=None,
            title=None,
        )
    )

    assert "1.0 Ko" in capsys.readouterr().out


def test_command_inspect(monkeypatch, capsys):
    monkeypatch.setattr(
        module,
        "resolve_dataset",
        lambda *args, **kwargs: {
            "title": "Énergie",
            "value": 1,
        },
    )

    module.command_inspect(
        Namespace(
            dataset="example",
            producer=None,
            title=None,
        )
    )

    payload = json.loads(capsys.readouterr().out)

    assert payload == {
        "title": "Énergie",
        "value": 1,
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "?"),
        (True, "oui"),
        (False, "non"),
        ([], "?"),
        (["a", "b"], "a, b"),
        ([1, 2], "[1, 2]"),
        ({}, "?"),
        ({"a": 1}, '{"a": 1}'),
        (42, "42"),
    ],
)
def test_format_metadata_value(value, expected):
    assert module.format_metadata_value(value) == expected


def test_print_mapping_section_empty(capsys):
    module.print_mapping_section(
        "Qualité",
        None,
        [("score", "Score")],
    )

    output = capsys.readouterr().out

    assert "Qualité" in output
    assert "?" in output


def test_print_mapping_section(capsys):
    module.print_mapping_section(
        "Qualité",
        {
            "score": 0.987,
            "available": True,
            "extra": {"x": 1},
        },
        [
            ("score", "Score"),
            ("available", "Disponible"),
        ],
    )

    output = capsys.readouterr().out

    assert "Score" in output
    assert "0.99" in output
    assert "Disponible" in output
    assert "oui" in output
    assert "Autres qualité" in output
    assert '"extra"' in output


def test_command_metadata(monkeypatch, capsys):
    monkeypatch.setattr(
        module,
        "resolve_dataset",
        lambda *args, **kwargs: {
            "title": "Example",
            "id": "abc",
            "organization": {"name": "Example Org"},
            "license": "odbl",
            "created_at": "2026",
            "last_modified": "2026",
            "last_update": "2026",
            "frequency": "annual",
            "frequency_date": None,
            "tags": ["transport", "open-data"],
            "temporal_coverage": {
                "start": "2024",
                "end": "2024",
            },
            "spatial": {},
            "resources": [{}, {}],
            "page": "https://example.test",
            "quality": {
                "score": 1.0,
            },
            "metrics": {
                "views": 12,
            },
        },
    )

    module.command_metadata(
        Namespace(
            dataset="example",
            producer=None,
            title=None,
        )
    )

    output = capsys.readouterr().out

    assert "Example Org" in output
    assert "transport, open-data" in output
    assert "Ressources" in output
    assert "Qualité" in output
    assert "Métriques" in output
    assert "12" in output


def test_build_parser_search():
    parser = module.build_parser()

    args = parser.parse_args(
        [
            "search",
            "transport",
            "--limit",
            "7",
        ]
    )

    assert args.command == "search"
    assert args.query == "transport"
    assert args.limit == 7
    assert args.func is module.command_search


@pytest.mark.parametrize(
    ("command", "func"),
    [
        ("dataset", module.command_dataset),
        ("resources", module.command_resources),
        ("stats", module.command_stats),
        ("inspect", module.command_inspect),
        ("metadata", module.command_metadata),
    ],
)
def test_build_parser_dataset_commands(command, func):
    parser = module.build_parser()

    args = parser.parse_args(
        [
            command,
            "example",
            "--producer",
            "Example Org",
            "--title",
            "Example",
        ]
    )

    assert args.command == command
    assert args.dataset == "example"
    assert args.producer == "Example Org"
    assert args.title == "Example"
    assert args.func is func


def test_build_parser_organization():
    parser = module.build_parser()

    args = parser.parse_args(
        [
            "organization",
            "abc",
        ]
    )

    assert args.organization_id == "abc"
    assert args.func is module.command_organization


def test_main_success(monkeypatch):
    called = []

    monkeypatch.setattr(
        module,
        "build_parser",
        lambda: type(
            "Parser",
            (),
            {
                "parse_args": lambda self: Namespace(
                    func=lambda args: called.append(True)
                )
            },
        )(),
    )

    assert module.main() == 0
    assert called == [True]


@pytest.mark.parametrize(
    ("exception", "message", "code"),
    [
        (
            requests.HTTPError("HTTP failure"),
            "Erreur HTTP",
            1,
        ),
        (
            requests.RequestException("Network failure"),
            "Erreur réseau",
            1,
        ),
        (
            ValueError("Bad value"),
            "Erreur : Bad value",
            1,
        ),
        (
            KeyboardInterrupt(),
            "Interrompu.",
            130,
        ),
    ],
)
def test_main_handles_errors(
    monkeypatch,
    capsys,
    exception,
    message,
    code,
):
    def fail(args):
        raise exception

    monkeypatch.setattr(
        module,
        "build_parser",
        lambda: type(
            "Parser",
            (),
            {"parse_args": lambda self: Namespace(func=fail)},
        )(),
    )

    assert module.main() == code

    error = capsys.readouterr().err
    assert message in error
