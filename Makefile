PYTHON ?= python3

.PHONY: all setup audit build cluster rules predict diagnostics vct-profiles dashboard test report validate slides clean

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

predict:
	$(PYTHON) scripts/07_compare_predictors.py

diagnostics:
	$(PYTHON) scripts/08_build_diagnostic_page.py

vct-profiles:
	$(PYTHON) scripts/10_build_vct_player_profiles.py

dashboard:
	$(PYTHON) scripts/09_build_public_dashboard.py

test:
	$(PYTHON) -m unittest discover -s tests -v

report:
	$(PYTHON) scripts/04_make_report.py

validate:
	$(PYTHON) scripts/05_validate.py

slides:
	$(PYTHON) scripts/06_make_slides.py

all: audit build cluster rules predict diagnostics vct-profiles dashboard test validate

clean:
	rm -rf data/processed/* outputs/tables/* reports/figures/*
