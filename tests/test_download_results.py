from pathlib import Path

from datagouv_toolkit import download_resources as module
from datagouv_toolkit.download_resources import download_resources


def test_download_resources_returns_downloaded_results(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    resources = [
        {
            "title": "a.csv",
            "url": "https://example.test/a.csv",
        },
        {
            "title": "b.csv",
            "url": "https://example.test/b.csv",
        },
    ]

    def fake_download(resource, destination, *, overwrite=False):
        return True

    monkeypatch.setattr(module, "download_resource", fake_download)

    results = download_resources(resources, tmp_path)

    assert results == [
        {
            "resource": resources[0],
            "path": tmp_path / "a.csv",
            "downloaded": True,
        },
        {
            "resource": resources[1],
            "path": tmp_path / "b.csv",
            "downloaded": True,
        },
    ]
    assert capsys.readouterr().out == "[1/2] GET  a.csv\n[2/2] GET  b.csv\n"


def test_download_resources_returns_skipped_result(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    destination = tmp_path / "a.csv"
    destination.write_text("existing", encoding="utf-8")

    resource = {
        "title": "a.csv",
        "url": "https://example.test/a.csv",
    }

    called = False

    def fake_download(resource, destination, *, overwrite=False):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr(module, "download_resource", fake_download)

    results = download_resources([resource], tmp_path)

    assert called is False
    assert results == [
        {
            "resource": resource,
            "path": destination,
            "downloaded": False,
        }
    ]
    assert capsys.readouterr().out == "[1/1] SKIP a.csv\n"
