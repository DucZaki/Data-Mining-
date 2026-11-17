#!/usr/bin/env python
"""Download the public VCT DuckDB and derive traceable player profiles."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from valorant_mining.player_radar import build_profiles  # noqa: E402

SOURCE_URL = "https://vct-reference.com/dataset/vct.duckdb"
DB_PATH = ROOT / "data" / "external" / "vct.duckdb"
CSV_PATH = ROOT / "data" / "processed" / "vct_player_profiles.csv"
META_PATH = ROOT / "data" / "processed" / "vct_player_profiles_source.json"


def ensure_database() -> None:
    if DB_PATH.is_file() and DB_PATH.stat().st_size > 1_000_000:
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = DB_PATH.with_suffix(".duckdb.download")
    try:
        with urlopen(Request(SOURCE_URL, headers={"User-Agent": "ValorantMapLab/1.0"}), timeout=60) as response, temp.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        if temp.stat().st_size < 1_000_000:
            raise RuntimeError("Downloaded VCT database is unexpectedly small")
        temp.replace(DB_PATH)
    finally:
        temp.unlink(missing_ok=True)


def main() -> None:
    ensure_database()
    con = duckdb.connect(str(DB_PATH), read_only=True)
    query = """
        SELECT pm.player_id, p.player_name, m.season, mp.map_name, pm.game_id,
               (mp.score0 + mp.score1) AS rounds, pm.acs_all, pm.adr_all,
               pm.kast_all, pm.kills_all, pm.deaths_all, pm.assists_all, pm.fk_all
        FROM player_map pm
        JOIN players p USING (player_id)
        JOIN matches m USING (match_id)
        JOIN maps mp USING (match_id, game_id)
        WHERE m.listing_status = 'Completed' AND m.is_showmatch = FALSE
          AND m.season BETWEEN 2021 AND 2026
          AND mp.score0 IS NOT NULL AND mp.score1 IS NOT NULL
    """
    frame = con.execute(query).df()
    date_range = con.execute("SELECT MIN(utc_timestamp), MAX(utc_timestamp) FROM matches WHERE listing_status='Completed' AND is_showmatch=FALSE").fetchone()
    con.close()
    profiles = build_profiles(frame)
    if not profiles["kast"].between(0, 1).all() or not profiles["coverage"].between(.8, 1).all():
        raise ValueError("VCT profile rates/coverage outside expected bounds")
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(CSV_PATH, index=False, float_format="%.6f")
    metadata = {"source": "VCT Reference", "url": SOURCE_URL,
                "source_file_sha256": hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
                "source_file_saved_utc": datetime.fromtimestamp(DB_PATH.stat().st_mtime, timezone.utc).isoformat(),
                "source_player_map_rows": len(frame), "profiles": len(profiles),
                "first_match_utc": str(date_range[0]), "last_match_utc": str(date_range[1]),
                "method": "Real player-map statistics; complete rows only, >=80% coverage, >=20 maps per season or >=5 on a named map; round-weighted ACS/ADR/KAST; peer percentiles by season and map."}
    META_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"VCT profiles: {len(profiles):,} rows, {profiles.player_id.nunique():,} players")
    print(f"Source dates: {date_range[0]} to {date_range[1]}")
    print(f"CSV: {CSV_PATH}")


if __name__ == "__main__":
    main()
