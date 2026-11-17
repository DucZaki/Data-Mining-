"""Real VCT player profiles for a six-metric, peer-relative radar chart."""

from __future__ import annotations

import numpy as np
import pandas as pd

METRICS = ("acs", "adr", "kd", "assists_pr", "first_kills_pr", "kast")
PERCENTILE_COLUMNS = tuple(f"pct_{metric}" for metric in METRICS)


def build_profiles(player_maps: pd.DataFrame) -> pd.DataFrame:
    """Aggregate complete player-map rows, keeping source coverage explicit.

    ACS, ADR and KAST are round-weighted; K/D uses total kills / total deaths.
    Assists and first kills are divided by rounds. Percentiles are within the
    same season and map scope, among players that pass the sample gate.
    """
    df = player_maps.copy()
    df["rounds"] = pd.to_numeric(df["rounds"], errors="coerce")
    required = ["acs_all", "adr_all", "kast_all", "kills_all", "deaths_all", "assists_all", "fk_all"]
    df["complete"] = df[required].notna().all(axis=1) & df["rounds"].between(13, 40)
    total = df.groupby(["season", "map_name", "player_id"], dropna=False).size().rename("all_games")
    total_all = df.groupby(["season", "player_id"], dropna=False).size().rename("all_games")
    df = df[df["complete"]].copy()
    for stat in ("acs_all", "adr_all", "kast_all"):
        # DuckDB stores KAST as TINYINT. Cast before multiplying to avoid
        # integer overflow (75 * 20 must be 1500, not a wrapped byte).
        df[f"{stat}_weighted"] = df[stat].astype("float64") * df["rounds"].astype("float64")
    agg = {"player_name": "first", "rounds": "sum", "game_id": "size",
           "kills_all": "sum", "deaths_all": "sum", "assists_all": "sum", "fk_all": "sum",
           "acs_all_weighted": "sum", "adr_all_weighted": "sum", "kast_all_weighted": "sum"}
    scoped = df.groupby(["season", "map_name", "player_id"], dropna=False).agg(agg)
    scoped = scoped.join(total).reset_index().rename(columns={"map_name": "map"})
    overall = df.groupby(["season", "player_id"], dropna=False).agg(agg)
    overall = overall.join(total_all).reset_index()
    overall.insert(1, "map", "Tất cả map")
    out = pd.concat([overall, scoped], ignore_index=True)
    out = out.rename(columns={"game_id": "games"})
    out["coverage"] = out["games"] / out["all_games"]
    out = out[(out["coverage"] >= 0.80) &
              (((out["map"] == "Tất cả map") & (out["games"] >= 20)) |
               ((out["map"] != "Tất cả map") & (out["games"] >= 5)))].copy()
    out["acs"] = out["acs_all_weighted"] / out["rounds"]
    out["adr"] = out["adr_all_weighted"] / out["rounds"]
    out["kast"] = out["kast_all_weighted"] / out["rounds"] / 100
    out["kd"] = out["kills_all"] / out["deaths_all"].replace(0, np.nan)
    out["assists_pr"] = out["assists_all"] / out["rounds"]
    out["first_kills_pr"] = out["fk_all"] / out["rounds"]
    out = out.dropna(subset=list(METRICS))
    for metric in METRICS:
        out[f"pct_{metric}"] = out.groupby(["season", "map"])[metric].rank(pct=True, method="average")
    keep = ["season", "map", "player_id", "player_name", "games", "all_games", "rounds", "coverage",
            *METRICS, *PERCENTILE_COLUMNS]
    return out[keep].sort_values(["season", "map", "games", "player_name"],
                                 ascending=[False, True, False, True]).reset_index(drop=True)
