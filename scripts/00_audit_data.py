#!/usr/bin/env python
"""Step 0: audit the raw database and write the data-quality report."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from valorant_mining.audit import build_audit_report, md_table
from valorant_mining.config import OUTPUT_TABLES, REPORT_DIR
from valorant_mining.plotting import plot_audit


def main() -> None:
    report, audit = build_audit_report()

    (REPORT_DIR / "01_kiem_tra_du_lieu.md").write_text(report, encoding="utf-8")
    audit["missing"].to_csv(OUTPUT_TABLES / "audit_missing.csv", index=False)
    audit["players_by_threshold"].to_csv(
        OUTPUT_TABLES / "audit_players_by_threshold.csv", index=False
    )
    audit["maps"].to_csv(OUTPUT_TABLES / "audit_maps.csv", index=False)
    audit["round_history"].to_csv(OUTPUT_TABLES / "audit_round_history.csv", index=False)

    missing_pct = audit["missing"].set_index("field")["missing_pct"].to_dict()

    plot_audit(
        {
            "KAST_Percent": missing_pct["KAST_Percent"],
            "Num_2Ks": missing_pct["Num_2Ks"],
            "Agent": missing_pct["Agent (rỗng/null)"],
            "ACS": missing_pct["ACS"],
            "PlayerID": missing_pct["PlayerID"],
        },
        audit["maps"].set_index("Map")["games"],
        audit["games_per_player"],
    )

    print("Đã ghi reports/01_kiem_tra_du_lieu.md")
    print(md_table(audit["players_by_threshold"]))


if __name__ == "__main__":
    main()
