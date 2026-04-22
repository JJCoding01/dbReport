PACKAGE_NAME=dbreport

# GENERAL SETUP

.PHONY: install
install:
	pip install -e ".[dev]"
	pre-commit install
	git submodule init
	git submodule update

# DOCUMENTATION AND TEST DB

.PHONY: docs
docs:
	cd docs && make html

create-db:
	python tests\data\db_setup.py "load-dump"

# FORMATTING AND LINTING

format:
	black $(PACKAGE_NAME)
	isort $(PACKAGE_NAME)
	flake8 $(PACKAGE_NAME)
	pylint $(PACKAGE_NAME)

pyproject:
	validate-pyproject pyproject.toml
	pyproject-fmt pyproject.toml

format-tests:
	black tests
	isort tests
	flake8 tests

# TESTING

.PHONY: tests
tests:
	pytest --cov-report html --cov=$(PACKAGE_NAME) tests/$(PACKAGE_NAME)

tests-ci:
	pytest --cov-report html --cov=$(PACKAGE_NAME) tests/$(PACKAGE_NAME) -v
