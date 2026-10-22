#!/usr/bin/env python
"""Step 3: FP-Growth association rules for Agent compositions, per map."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from valorant_mining.config import DATA_PROCESSED, FIGURE_DIR
from valorant_mining.plotting import plot_composition_volume, plot_rules
from valorant_mining.rules import run_rules, save_rules


def main() -> None:
    comps = pd.read_csv(DATA_PROCESSED / "team_compositions.csv")
    result = run_rules(comps)
    save_rules(result)
    plot_rules(result)
    plot_composition_volume(comps)

    rules = result["rules"]
    print(result["summary"])
    print("\nSố luật theo bản đồ:")
    if not rules.empty:
        print(rules.groupby("map").size().to_string())
        cols = ["map", "rule", "support", "confidence", "lift", "support_count"]
        print("\nTop 15 luật theo lift:")
        print(rules.sort_values("lift", ascending=False)[cols].head(15).to_string(index=False))
    print(f"\nHình: {FIGURE_DIR}")


if __name__ == "__main__":
    main()
