# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fmaillar/datagouv-toolkit/releases/tag/v0.1.0
