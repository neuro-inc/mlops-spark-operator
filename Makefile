include k8s.mk

setup:
	pip install -U pip
	pip install -e .[dev]
	pre-commit install

lint: format
	mypy src

format:
ifdef CI
	pre-commit run --all-files --show-diff-on-failure
else
	pre-commit run --all-files
endif

test_unit:
	pytest -vv --cov-report xml:.coverage-unit.xml tests/unit

test_integration:
	pytest -vv --maxfail=3 --cov-report xml:.coverage-integration.xml tests/integration
