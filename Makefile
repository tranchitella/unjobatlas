# Makefile for QA checks in a Django application

# Variables
PYTHON := python3
VENV := .venv
ACTIVATE := $(VENV)/bin/activate
FLAKE8 := $(VENV)/bin/flake8
FLAKE8_OPTS := "--max-line-length=120"
BLACK := $(VENV)/bin/black
BLACK_CHECK_OPTS := --check
ISORT := $(VENV)/bin/isort --profile=black
ISORT_CHECK_OPTS := --check-only
SRC := config core

# Default target
.PHONY: all
all: qa

# Create virtual environment
.PHONY: .venv
.venv:
	$(PYTHON) -m .venv $(VENV)
	. $(ACTIVATE) && pip install --upgrade pip setuptools
	. $(ACTIVATE) && pip install -r requirements.txt

# Run flake8 for linting
.PHONY: lint
lint:
	$(FLAKE8) $(FLAKE8_OPTS) $(SRC)

# Run black for code formatting
.PHONY: format
format:
	$(BLACK) $(SRC)

# Run black in check mode
.PHONY: check-format
check-format:
	$(BLACK) $(BLACK_CHECK_OPTS) $(SRC)

# Run isort for import sorting
.PHONY: sort-imports
sort-imports:
	$(ISORT) $(SRC)

# Run isort in check mode
.PHONY: check-imports
check-imports:
	$(ISORT) $(ISORT_CHECK_OPTS) $(SRC)

# Run all QA checks
.PHONY: qa
qa: format sort-imports lint
	@echo "QA checks completed successfully."

# Run all QA checks in check mode
.PHONY: check-qa
check-qa: check-format check-imports lint
	@echo "QA checks (check mode) completed successfully."

.PHONY: test
test: test-run test-coverage

.PHONY: test-run
test-run:
	coverage run --source='.' manage.py test $(ARGS)

.PHONY: test-coverage
test-coverage:
	coverage report
	coverage html
