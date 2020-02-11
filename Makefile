define USAGE
USAGE:
> make [
	test: run all tests
	lint: run flake8 linter with tox

	clean: ...

	publish-pypi: publish package on python package index
	release: manage release on github, publish on python package index as well as docker hub
]
endef


ifeq ($(OS),)
	OS := $(shell uname -s | tr A-Z a-z)
endif

VERSION := $(shell python setup.py --version)
DEV_VERSION := $(shell git rev-parse HEAD || 'unknown')
REPO := preveil/pvHelpers


VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

ifeq ($(OS), Windows_NT)
PYTHON = $(VENV)/Scripts/python
PIP = $(VENV)/Scripts/pip
endif



all:
	$(info $(USAGE))
sense:
	@make

clean:
	rm -rf ./dist
	rm -rf ./build
	rm -rf ./.tox
	rm -rf $(VENV)

$(VENV):
	pip install virtualenv
	python -m virtualenv $(VENV)
	$(PIP) install tox


package: $(VENV)
	$(PYTHON) setup.py sdist

test: $(VENV)
	$(PYTHON) -m tox

lint: $(VENV)
	$(PYTHON) -m tox -e lint

publish-pypi:
	@echo 'todo, create pr request on vendor'

release:
	@echo 'todo: handle version bump, tag releases on git, merge to master'

