PYTHON ?= python3
VENV := .venv
VENV_PY := $(VENV)/bin/python
SRC := src
export PYTHONPATH := $(SRC)

.PHONY: test inbox dogfood venv

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PY) -m pip install -q -r requirements-dev.txt

test: $(VENV_PY)
	$(VENV_PY) -m pytest -q

$(VENV_PY):
	$(PYTHON) -m venv $(VENV)
	$(VENV_PY) -m pip install -q -r requirements-dev.txt

# Usage: make inbox REPO=/path/to/git/repo
#    or: make inbox TARGET=vedic
inbox:
ifneq ($(TARGET),)
	$(PYTHON) -m dock inbox --target "$(TARGET)" --format md
else
	$(PYTHON) -m dock inbox --path "$(or $(REPO),$(CURDIR)/..)" --format md
endif

dogfood:
	$(PYTHON) -m dock dogfood --format md
