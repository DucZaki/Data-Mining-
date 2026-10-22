"""Project paths and analysis constants."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
REPORT_DIR = ROOT / "reports"
FIGURE_DIR = REPORT_DIR / "figures"

DB_PATH = DATA_RAW / "valorant.sqlite"

for _dir in (DATA_PROCESSED, OUTPUT_TABLES, FIGURE_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
MIN_GAMES_PER_PLAYER = 10
MIN_ROUNDS_PER_PLAYER = 100

# Only maps that appear often enough for per-map association rules.
# "TBD" is not a playable map.
VALID_MAPS = ["Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox", "Split"]

# Agent role labels as of the 2021-2022 competitive season covered by the DB.
AGENT_ROLES = {
    "jett": "duelist",
    "raze": "duelist",
    "phoenix": "duelist",
    "reyna": "duelist",
    "yoru": "duelist",
    "neon": "duelist",
    "sova": "initiator",
    "skye": "initiator",
    "breach": "initiator",
    "kayo": "initiator",
    "omen": "controller",
    "brimstone": "controller",
    "astra": "controller",
    "viper": "controller",
    "sage": "sentinel",
    "cypher": "sentinel",
    "killjoy": "sentinel",
    "chamber": "sentinel",
}

FEATURE_LABELS = {
    "kills_pr": "Kills / round",
    "deaths_pr": "Deaths / round",
    "assists_pr": "Assists / round",
    "kd": "K/D",
    "acs": "ACS",
    "adr": "ADR",
    "fk_pr": "First kills / round",
    "fd_pr": "First deaths / round",
    "multi_pr": "Multi-kill rounds / round",
    "acs_sd": "Độ lệch chuẩn ACS",
    "hs": "HS %",
}

MODEL_FEATURES = list(FEATURE_LABELS)
