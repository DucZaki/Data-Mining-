PYTHON ?= python3

.PHONY: all setup audit build cluster rules report validate clean

setup:
	$(PYTHON) -m pip install -r requirements.txt

audit:
	$(PYTHON) scripts/00_audit_data.py

build:
	$(PYTHON) scripts/01_build_datasets.py

cluster:
	$(PYTHON) scripts/02_cluster_players.py

rules:
	$(PYTHON) scripts/03_agent_rules.py

report:
	$(PYTHON) scripts/04_make_report.py

validate:
	$(PYTHON) scripts/05_validate.py

all: audit build cluster rules report validate

clean:
	rm -rf data/processed/* outputs/tables/* reports/figures/*
