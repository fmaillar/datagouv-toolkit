# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-08-31

### Added

- Machine-readable `--json` output for catalog exploration commands, dataset metadata, resources, statistics, organizations, downloads, and workflows.
- Structured download results exposing each resource path and whether it was actually downloaded or skipped.
- Structured workflow results exposing download state, CSV audit state, and audit report paths per resource.
- Subprocess-level CLI integration tests covering the real `python -m datagouv_toolkit.cli` entry point, command help, required arguments, and controlled failures without tracebacks.

### Changed

- Migrated the Python package to a standard `src/` layout and updated packaging, typing, tests, and tooling accordingly.
- `datagouv download --json` and `datagouv workflow --json` now keep standard output parseable by suppressing human progress output.
- Documentation now includes JSON examples and Unix-style composition with tools such as `jq`.
- Quality checks are consolidated through the project `Makefile` while CI continues to validate Ruff, mypy, Bandit, tests, coverage, package build, metadata, and CLI installation.

## [0.2.1] - 2026-08-31

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
- CLI error-handler tests now use correctly bound mock callables across Python 3.11–3.13.

## [0.2.0] - 2026-08-26

### Added

- Published BAAC 2005–2024 analysis release.

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

[Unreleased]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fmaillar/datagouv-toolkit/releases/tag/v0.1.0
