# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-08-31

### Added

- Unified `datagouv` CLI for catalog exploration, resource downloads, workflows, CSV audits, and local catalog statistics.
- `datagouv download`, `datagouv workflow`, `datagouv inspect-csv`, and `datagouv catalog-stats` subcommands.
- Tests covering unified CLI argument mapping, command delegation, and top-level error handling.
- Regression test ensuring an EOF during interactive dataset selection terminates cleanly instead of looping indefinitely.
- In-depth `TUTORIAL.md` covering the CLI, API/HTTP concepts, JSON, metadata, resources, data profiling, pipelines, and reproducibility.

### Changed

- The installed `datagouv` command now uses `cli.py` as its single entry point.
- CLI parsing and dispatch are centralized in `cli.py`; the duplicated historical parser and `main()` were removed from `datagouv.py`.
- `datagouv.py` is now documented and structured as the data.gouv.fr business/API layer rather than as a standalone CLI.
- Legacy specialized console commands remain available for backward compatibility.
- CI coverage now includes the unified `cli.py` layer while retaining the 95% project coverage threshold.

### Fixed

- Interactive dataset selection now handles end-of-file input as an interruption instead of repeatedly prompting forever.

## [0.1.1] - 2026-08-25

### Added

- Python packaging with `pyproject.toml`.
- Installable console commands: `datagouv`, `datagouv-download`, `datagouv-workflow`, `datagouv-inspect-csv`, and `datagouv-catalog-stats`.
- Official support for Python 3.11, 3.12, and 3.13.
- GitHub Actions CI matrix for Python 3.11–3.13.
- Package build and metadata validation in CI.
- Automated PyPI publication through GitHub Actions Trusted Publishing (OIDC).
- `CONTRIBUTING.md` and `SECURITY.md`.

### Changed

- Project version bumped to `0.1.1`.
- Development dependencies are now declared in `pyproject.toml`.

## [0.1.0] - 2026-08-25

### Added

- Generic data.gouv.fr dataset exploration CLI.
- Dataset resource downloader.
- Generic dataset workflow combining resolution, download, and CSV audit.
- CSV structural audit tooling.
- Local data.gouv.fr catalog statistics tooling.
- Metadata normalization helpers.
- BAAC dataset case study under `datasets/baac/`.
- Automated test suite with high coverage.
- Ruff, mypy, Bandit, pytest, and coverage checks.
- GPL-3.0-only license.

[Unreleased]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fmaillar/datagouv-toolkit/releases/tag/v0.1.0
