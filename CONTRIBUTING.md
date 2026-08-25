# Contributing to datagouv-toolkit

Contributions are welcome. The project aims to keep a small, testable and reusable core for working with datasets published on data.gouv.fr.

## Scope

Contributions should preferably improve one of the following areas:

- exploration of the data.gouv.fr catalogue;
- dataset and resource resolution;
- downloading and validating resources;
- CSV inspection and structural auditing;
- reproducible catalogue statistics;
- metadata normalization;
- tests, documentation and developer tooling.

Dataset-specific work should remain isolated under `datasets/` when it cannot reasonably be generalized.

## Development setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/fmaillar/datagouv-toolkit.git
cd datagouv-toolkit
python -m venv .venv
source .venv/bin/activate
```

Install the project in editable mode with development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Quality checks

Before submitting a change, run:

```bash
ruff check .
ruff format --check .
mypy . --ignore-missing-imports
bandit -q *.py
pytest -q
```

The CI also enforces a minimum global coverage threshold of 95% for the generic core modules.

To reproduce the coverage check locally:

```bash
pytest \
  --cov=datagouv \
  --cov=catalog_stats \
  --cov=normalize \
  --cov=inspect_csv \
  --cov=download_resources \
  --cov=dataset_workflow \
  --cov-report=term-missing \
  --cov-fail-under=95 \
  -q
```

## Tests

New behavior should normally include tests. Network access should be mocked in unit tests so that the suite remains deterministic and does not depend on data.gouv.fr availability.

Prefer focused tests that cover behavior and error handling rather than tests written only to increase the coverage percentage.

## Code style

Keep changes small and explicit. In particular:

- preserve the separation between generic tooling and dataset-specific code;
- avoid adding derived domain semantics to generic modules;
- keep CLI errors understandable and actionable;
- avoid unnecessary dependencies;
- retain deterministic behavior where reproducibility matters;
- use type hints for new public functions where practical.

## Commit and pull request guidance

Use concise, imperative commit messages, for example:

```text
Add CSV delimiter fallback
Fix dataset producer filtering
Document snapshot workflow
```

A pull request should explain:

- what problem it solves;
- what changed;
- how the change was tested;
- any compatibility or data interpretation implications.

Keep unrelated changes in separate pull requests when possible.

## Security issues

Do not open a public issue for a suspected security vulnerability. Follow the process described in [`SECURITY.md`](SECURITY.md).

## License

By contributing, you agree that your contribution will be licensed under the GNU General Public License v3.0 (`GPL-3.0-only`), consistent with the project license.
