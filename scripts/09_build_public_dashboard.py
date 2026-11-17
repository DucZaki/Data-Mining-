#!/usr/bin/env python
"""Build the offline, visitor-facing historical Valorant map explorer."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from valorant_mining.public_stats import build_public_data  # noqa: E402


def main() -> None:
    frame = pd.read_csv(ROOT / "data" / "processed" / "team_compositions.csv")
    data = build_public_data(frame)
    profiles_path = ROOT / "data" / "processed" / "vct_player_profiles.csv"
    source_path = ROOT / "data" / "processed" / "vct_player_profiles_source.json"
    if not profiles_path.is_file() or not source_path.is_file():
        raise FileNotFoundError("Run 'python scripts/10_build_vct_player_profiles.py' first")
    profiles = pd.read_csv(profiles_path)
    profiles = profiles.loc[profiles["map"].eq("Tất cả map")].drop(columns=["map", "coverage", "all_games", "rounds"])
    data["players"] = json.loads(profiles.to_json(orient="records", force_ascii=False, double_precision=6))
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    template = (ROOT / "dashboard" / "public_template.html").read_text(encoding="utf-8")
    template = template.replace("__PLAYER_CSS__", (ROOT / "dashboard" / "player_radar.css").read_text(encoding="utf-8"))
    template = template.replace("__PLAYER_JS__", (ROOT / "dashboard" / "player_radar.js").read_text(encoding="utf-8"))
    output = ROOT / "dashboard" / "index.html"
    output.write_text(template.replace("__DATA__", payload), encoding="utf-8")
    print(f"Public dashboard: {output} ({output.stat().st_size / 1024:.0f} KiB)")


if __name__ == "__main__":
    main()
