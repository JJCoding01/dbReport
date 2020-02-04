PACKAGE_NAME=dbreport

.PHONY: install docs lint-html tests

create-db:
	python tests\data\db_setup.py "load-dump"

docs:
	cd docs && make html

db:
	make export-db && make create-db

example-simple:
	python .\example.py simple

example-parse:
	python .\example.py parse

example-category:
	python .\example.py category

export-db:
	python tests\data\db_setup.py "create-dump"

install:
	python setup.py install

lint:
	black $(PACKAGE_NAME) --line-length=79
	pylint $(PACKAGE_NAME)

lint-tests:
	black tests --line-length=79
	pylint tests

tests:
	pytest --cov-report html --cov=$(PACKAGE_NAME) tests/$(PACKAGE_NAME)
