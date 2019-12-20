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
export USAGE

ifeq ($(OS),)
	OS := $(shell uname -s | tr A-Z a-z)
endif

VERSION := $(shell python setup.py --version)
DEV_VERSION := $(shell git rev-parse HEAD || 'unknown')
REPO := preveil/pvHelpers


all:
	@echo "$$USAGE"

clean:
	rm -rf ./dist
	rm -rf ./build
	rm -rf ./.tox
	rm -rf ./.venv

package:
	python setup.py sdist

test:
	tox

lint:
	tox -e lint

publish-pypi:
	@echo 'todo, create pr request on vendor'

release:
	@echo 'todo: handle version bump, tag releases on git, merge to master'

