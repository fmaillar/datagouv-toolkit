import sys
from pathlib import Path

import pytest

from datagouv_toolkit import dataset_workflow as module
from datagouv_toolkit.dataset_workflow import run_workflow


def test_run_workflow_downloads_and_audits_csv(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dataset = {
        "title": "Example dataset",
        "resources": [
            {
                "title": "data.csv",
                "format": "csv",
                "url": "https://example.test/data.csv",
            }
        ],
    }

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.resolve_dataset",
        lambda *args, **kwargs: dataset,
    )

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.select_resources",
        lambda *args, **kwargs: dataset["resources"],
    )

    downloaded = []
    audited = []

    def fake_download(resource, destination, *, overwrite=False):
        downloaded.append((resource, destination, overwrite))
        destination.write_text("id;value\n1;a\n", encoding="utf-8")
        return True

    def fake_inspect(path):
        audited.append(path)

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.download_resource",
        fake_download,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.inspect_csv",
        fake_inspect,
    )

    run_workflow(
        "example",
        tmp_path,
    )

    assert len(downloaded) == 1
    assert downloaded[0][1] == tmp_path / "data.csv"
    assert audited == [tmp_path / "data.csv"]


def test_run_workflow_does_not_audit_non_csv(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dataset = {
        "title": "Example dataset",
        "resources": [
            {
                "title": "data.json",
                "format": "json",
                "url": "https://example.test/data.json",
            }
        ],
    }

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.resolve_dataset",
        lambda *args, **kwargs: dataset,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.select_resources",
        lambda *args, **kwargs: dataset["resources"],
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.download_resource",
        lambda resource, destination, *, overwrite=False: True,
    )

    audited = []

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.inspect_csv",
        lambda path: audited.append(path),
    )

    run_workflow(
        "example",
        tmp_path,
    )

    assert audited == []


def test_run_workflow_can_disable_audit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dataset = {
        "title": "Example dataset",
        "resources": [
            {
                "title": "data.csv",
                "format": "csv",
                "url": "https://example.test/data.csv",
            }
        ],
    }

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.resolve_dataset",
        lambda *args, **kwargs: dataset,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.select_resources",
        lambda *args, **kwargs: dataset["resources"],
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.download_resource",
        lambda resource, destination, *, overwrite=False: True,
    )

    audited = []

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.inspect_csv",
        lambda path: audited.append(path),
    )

    run_workflow(
        "example",
        tmp_path,
        audit_csv=False,
    )

    assert audited == []


def test_run_workflow_audits_existing_csv_after_skip(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dataset = {
        "title": "Example dataset",
        "resources": [
            {
                "title": "data.csv",
                "format": "csv",
                "url": "https://example.test/data.csv",
            }
        ],
    }

    destination = tmp_path / "data.csv"
    destination.write_text("id;value\n1;a\n", encoding="utf-8")

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.resolve_dataset",
        lambda *args, **kwargs: dataset,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.select_resources",
        lambda *args, **kwargs: dataset["resources"],
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.download_resource",
        lambda resource, destination, *, overwrite=False: False,
    )

    audited = []

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.inspect_csv",
        lambda path: audited.append(path),
    )

    run_workflow(
        "example",
        tmp_path,
    )

    assert audited == [destination]


def test_run_workflow_forwards_filters(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dataset = {
        "title": "Example dataset",
        "resources": [],
    }

    resolve_calls = []
    select_calls = []

    def fake_resolve(
        dataset_query,
        *,
        producer=None,
        title=None,
    ):
        resolve_calls.append(
            {
                "dataset_query": dataset_query,
                "producer": producer,
                "title": title,
            }
        )
        return dataset

    def fake_select(
        selected_dataset,
        *,
        resource_format=None,
        title=None,
    ):
        select_calls.append(
            {
                "dataset": selected_dataset,
                "resource_format": resource_format,
                "title": title,
            }
        )
        return [
            {
                "title": "data.csv",
                "format": "csv",
                "url": "https://example.test/data.csv",
            }
        ]

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.resolve_dataset",
        fake_resolve,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.select_resources",
        fake_select,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.download_resource",
        lambda resource, destination, *, overwrite=False: True,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.inspect_csv",
        lambda path: None,
    )

    run_workflow(
        "transport",
        tmp_path,
        producer="Example org",
        dataset_title="Mobilité",
        resource_format="csv",
        resource_title="2024",
    )

    assert resolve_calls == [
        {
            "dataset_query": "transport",
            "producer": "Example org",
            "title": "Mobilité",
        }
    ]

    assert select_calls == [
        {
            "dataset": dataset,
            "resource_format": "csv",
            "title": "2024",
        }
    ]


def test_run_workflow_forwards_overwrite(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dataset = {
        "title": "Example dataset",
        "resources": [
            {
                "title": "data.csv",
                "format": "csv",
                "url": "https://example.test/data.csv",
            }
        ],
    }

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.resolve_dataset",
        lambda *args, **kwargs: dataset,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.select_resources",
        lambda *args, **kwargs: dataset["resources"],
    )

    overwrite_values = []

    def fake_download(resource, destination, *, overwrite=False):
        overwrite_values.append(overwrite)
        return True

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.download_resource",
        fake_download,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.inspect_csv",
        lambda path: None,
    )

    run_workflow(
        "example",
        tmp_path,
        overwrite=True,
    )

    assert overwrite_values == [True]


def test_run_workflow_rejects_empty_selection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dataset = {
        "title": "Example dataset",
        "resources": [],
    }

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.resolve_dataset",
        lambda *args, **kwargs: dataset,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.select_resources",
        lambda *args, **kwargs: [],
    )

    with pytest.raises(
        SystemExit,
        match="Aucune ressource correspondante",
    ):
        run_workflow(
            "example",
            tmp_path,
        )


def test_run_workflow_writes_audit_file(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dataset = {
        "title": "Example dataset",
        "resources": [
            {
                "title": "data.csv",
                "format": "csv",
                "url": "https://example.test/data.csv",
            }
        ],
    }

    output_dir = tmp_path / "data"
    audit_dir = tmp_path / "audits"

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.resolve_dataset",
        lambda *args, **kwargs: dataset,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.select_resources",
        lambda *args, **kwargs: dataset["resources"],
    )

    def fake_download(resource, destination, *, overwrite=False):
        destination.write_text("id;value\n1;a\n", encoding="utf-8")
        return True

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.download_resource",
        fake_download,
    )

    def fake_inspect(path):
        print(f"Audit de {path.name}")

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.inspect_csv",
        fake_inspect,
    )

    run_workflow(
        "example",
        output_dir,
        audit_dir=audit_dir,
    )

    audit_path = audit_dir / "data.csv.audit.txt"

    assert audit_path.is_file()
    assert audit_path.read_text(encoding="utf-8") == "Audit de data.csv\n"


def test_run_workflow_audit_dir_ignored_when_audit_disabled(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dataset = {
        "title": "Example dataset",
        "resources": [
            {
                "title": "data.csv",
                "format": "csv",
                "url": "https://example.test/data.csv",
            }
        ],
    }

    audit_dir = tmp_path / "audits"

    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.resolve_dataset",
        lambda *args, **kwargs: dataset,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.select_resources",
        lambda *args, **kwargs: dataset["resources"],
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.download_resource",
        lambda resource, destination, *, overwrite=False: True,
    )
    monkeypatch.setattr(
        "datagouv_toolkit.dataset_workflow.inspect_csv",
        lambda path: None,
    )

    run_workflow(
        "example",
        tmp_path / "data",
        audit_csv=False,
        audit_dir=audit_dir,
    )

    assert not audit_dir.exists()


def test_parse_args(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dataset_workflow.py",
            "transport",
            "--output",
            "data",
            "--producer",
            "Example org",
            "--dataset-title",
            "Mobilité",
            "--format",
            "csv",
            "--resource-title",
            "2024",
            "--overwrite",
            "--audit-dir",
            "audits",
        ],
    )

    args = module.parse_args()

    assert args.dataset == "transport"
    assert args.output == Path("data")
    assert args.producer == "Example org"
    assert args.dataset_title == "Mobilité"
    assert args.resource_format == "csv"
    assert args.resource_title == "2024"
    assert args.overwrite is True
    assert args.no_audit is False
    assert args.audit_dir == Path("audits")


def test_main_forwards_cli_arguments(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls = []

    def fake_run_workflow(
        dataset_query,
        output_dir,
        **kwargs,
    ):
        calls.append(
            {
                "dataset_query": dataset_query,
                "output_dir": output_dir,
                **kwargs,
            }
        )

    monkeypatch.setattr(
        module,
        "run_workflow",
        fake_run_workflow,
    )

    audit_dir = tmp_path / "audits"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dataset_workflow.py",
            "example",
            "--output",
            str(tmp_path),
            "--no-audit",
            "--audit-dir",
            str(audit_dir),
        ],
    )

    module.main()

    assert calls == [
        {
            "dataset_query": "example",
            "output_dir": tmp_path,
            "producer": None,
            "dataset_title": None,
            "resource_format": None,
            "resource_title": None,
            "overwrite": False,
            "audit_csv": False,
            "audit_dir": audit_dir,
        }
    ]
