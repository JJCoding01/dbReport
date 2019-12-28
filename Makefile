PACKAGE_NAME=dbreport

.PHONY: install docs lint-html tests

install:
	python setup.py install

docs:
	cd docs && make html

lint:
	black $(PACKAGE_NAME) --line-length=79
	pylint $(PACKAGE_NAME)

lint-tests:
	black tests --line-length=79
	pylint tests

tests:
	pytest --cov-report html --cov=$(PACKAGE_NAME) tests/$(PACKAGE_NAME)

export-db:
	python tests\data\db_setup.py "create-dump"

create-db:
	python tests\data\db_setup.py "load-dump"

db:
	make export-db && make create-db
