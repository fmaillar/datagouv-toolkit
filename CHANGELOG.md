# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-08-31

### Added

- Non-interactive dataset selection with `--first` after producer/title filtering across dataset-resolving commands, downloads, and workflows.
- Resource filtering for `datagouv resources` with `--format` and `--resource-title`.
- URL-only resource handoff with `datagouv resources --urls` for Unix pipelines and downstream tools.
- Compact resource manifests with `datagouv resources --manifest`, including dataset identity and selected resource metadata.
- Focused tests covering non-interactive resolution, resource filtering, URL handoff, manifests, and parser behavior.

### Changed

- Project documentation now reflects the intended scope: discover, evaluate, select, and download data.gouv.fr resources, then hand them off to tools such as R, Python, DuckDB, or other Unix tooling.
- Package description and keywords now emphasize data discovery and access rather than downstream data analysis.
- `--json`, `--urls`, and `--manifest` are mutually exclusive resource output modes.

### Fixed

- Human-readable `catalog-stats` rankings now preserve and display remaining-value counts from structured ranking results.

## [0.4.0] - 2026-08-31

### Added

- Machine-readable `--json` output for `datagouv inspect-csv`, exposing file metadata, missing values, cardinalities, candidate keys, duplicate counts, low-cardinality distributions, and preview rows.
- Machine-readable `--json` output for `datagouv catalog-stats`, exposing normalized filters, dataset/resource totals, known and unknown resource sizes, and ranked producers, formats, licenses, and update frequencies.
- Focused tests covering structured CSV audits and structured catalog statistics.

### Changed

- CSV workflow auditing now reuses `analyze_csv()` and `format_csv_audit()` directly instead of capturing `stdout` from the human-readable `inspect_csv()` command.
- Workflow audit reports are written directly to their target files while JSON workflow execution remains free of human progress output.
- Documentation now includes `jq` examples for workflow, CSV-audit, and catalog-statistics JSON output.

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

[Unreleased]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/fmaillar/datagouv-toolkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fmaillar/datagouv-toolkit/releases/tag/v0.1.0
