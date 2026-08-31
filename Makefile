.PHONY: check lint typecheck security test build clean

check: lint typecheck security test build

lint:
	ruff check .

typecheck:
	mypy

security:
	bandit -q -r src/datagouv_toolkit

test:
	pytest \
		--cov=datagouv_toolkit \
		--cov-report=term-missing \
		--cov-fail-under=95 \
		-q

build:
	rm -rf build dist
	python -m build
	python -m twine check dist/*
	datagouv --help

clean:
	rm -rf build dist
