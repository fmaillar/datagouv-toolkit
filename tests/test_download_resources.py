from pathlib import Path

import pytest

from download_resources import (
    download_resource,
    safe_filename,
    select_resources,
)


def test_select_resources_by_format() -> None:
    dataset = {
        "resources": [
            {
                "title": "data.csv",
                "format": "CSV",
            },
            {
                "title": "data.json",
                "format": "application/json",
            },
        ]
    }

    resources = select_resources(
        dataset,
        resource_format="csv",
    )

    assert [resource["title"] for resource in resources] == ["data.csv"]


def test_select_resources_uses_normalized_format() -> None:
    dataset = {
        "resources": [
            {
                "title": "service",
                "format": "ogc:WFS",
            }
        ]
    }

    resources = select_resources(
        dataset,
        resource_format="wfs",
    )

    assert len(resources) == 1


def test_select_resources_by_title_case_insensitive() -> None:
    dataset = {
        "resources": [
            {
                "title": "Caract_2024.csv",
                "format": "csv",
            },
            {
                "title": "Lieux_2024.csv",
                "format": "csv",
            },
        ]
    }

    resources = select_resources(
        dataset,
        title="caract_2024",
    )

    assert [resource["title"] for resource in resources] == ["Caract_2024.csv"]


def test_select_resources_combines_filters() -> None:
    dataset = {
        "resources": [
            {
                "title": "Caract_2024.csv",
                "format": "csv",
            },
            {
                "title": "Caract_2024.json",
                "format": "json",
            },
        ]
    }

    resources = select_resources(
        dataset,
        resource_format="csv",
        title="Caract",
    )

    assert [resource["title"] for resource in resources] == ["Caract_2024.csv"]


def test_safe_filename_uses_title() -> None:
    resource = {
        "title": "data.csv",
        "id": "abc",
    }

    assert safe_filename(resource) == "data.csv"


def test_safe_filename_removes_path_components() -> None:
    resource = {
        "title": "../../data.csv",
        "id": "abc",
    }

    assert safe_filename(resource) == "data.csv"


def test_safe_filename_falls_back_to_id() -> None:
    resource = {
        "title": "",
        "id": "resource-123",
    }

    assert safe_filename(resource) == "resource-123"


class FakeResponse:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.raise_called = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def raise_for_status(self) -> None:
        self.raise_called = True

    def iter_content(self, chunk_size: int):
        assert chunk_size > 0
        yield from self.chunks


def test_download_resource(monkeypatch, tmp_path: Path) -> None:
    response = FakeResponse(
        [
            b"hello ",
            b"world",
        ]
    )

    def fake_get(url, *, stream, timeout):
        assert url == "https://example.test/data.csv"
        assert stream is True
        assert timeout == 60

        return response

    monkeypatch.setattr(
        "download_resources.requests.get",
        fake_get,
    )

    resource = {
        "title": "data.csv",
        "url": "https://example.test/data.csv",
    }

    destination = tmp_path / "data.csv"

    downloaded = download_resource(
        resource,
        destination,
    )

    assert downloaded is True
    assert response.raise_called is True
    assert destination.read_bytes() == b"hello world"
    assert not (tmp_path / "data.csv.part").exists()


def test_download_resource_skips_existing_file(tmp_path: Path) -> None:
    destination = tmp_path / "data.csv"
    destination.write_bytes(b"existing")

    resource = {
        "title": "data.csv",
        "url": "https://example.test/data.csv",
    }

    downloaded = download_resource(
        resource,
        destination,
    )

    assert downloaded is False
    assert destination.read_bytes() == b"existing"


def test_download_resource_requires_url(tmp_path: Path) -> None:
    resource = {
        "title": "data.csv",
    }

    with pytest.raises(ValueError, match="sans URL"):
        download_resource(
            resource,
            tmp_path / "data.csv",
        )


def test_download_resource_removes_partial_file_on_error(
    monkeypatch,
    tmp_path: Path,
) -> None:
    class BrokenResponse(FakeResponse):
        def iter_content(self, chunk_size: int):
            yield b"partial"
            raise RuntimeError("network error")

    def fake_get(url, *, stream, timeout):
        return BrokenResponse([])

    monkeypatch.setattr(
        "download_resources.requests.get",
        fake_get,
    )

    resource = {
        "title": "data.csv",
        "url": "https://example.test/data.csv",
    }

    destination = tmp_path / "data.csv"

    with pytest.raises(RuntimeError, match="network error"):
        download_resource(
            resource,
            destination,
        )

    assert not destination.exists()
    assert not (tmp_path / "data.csv.part").exists()
