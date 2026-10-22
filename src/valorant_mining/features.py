"""Player-level feature engineering for clustering."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    AGENT_ROLES,
    DATA_PROCESSED,
    MIN_GAMES_PER_PLAYER,
    MIN_ROUNDS_PER_PLAYER,
    MODEL_FEATURES,
)

ROLE_NAMES = ["duelist", "initiator", "controller", "sentinel", "other"]


def build_player_features(scoreboard: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate player-map rows into one performance profile per PlayerID.

    Rates use total rounds as denominator, so overtime maps do not get extra
    weight. ACS/ADR/HS% are already per-round values, so they are weighted by
    the number of rounds played in each map.
    """
    df = scoreboard.copy()
    df = df[df["ACS"].notna()].copy()
    df["role"] = df["Agent"].map(AGENT_ROLES).fillna("other")

    df["acs_x_rounds"] = df["ACS"] * df["rounds"]
    df["adr_x_rounds"] = df["ADR"].fillna(0) * df["rounds"]
    df["hs_x_rounds"] = df["HS_Percent"].fillna(0) * df["rounds"]
    df["multi_kills"] = (
        df[["Num_2Ks", "Num_3Ks", "Num_4Ks", "Num_5Ks"]].fillna(0).sum(axis=1)
    )

    grouped = df.groupby("PlayerID", sort=False)
    out = grouped.agg(
        PlayerName=("PlayerName", lambda s: s.mode().iat[0] if len(s.mode()) else s.iloc[0]),
        games=("GameID", "nunique"),
        rounds=("rounds", "sum"),
        kills=("Kills", "sum"),
        deaths=("Deaths", "sum"),
        assists=("Assists", "sum"),
        first_kills=("FirstKills", "sum"),
        first_deaths=("FirstDeaths", "sum"),
        multi_kills=("multi_kills", "sum"),
        acs_x_rounds=("acs_x_rounds", "sum"),
        adr_x_rounds=("adr_x_rounds", "sum"),
        hs_x_rounds=("hs_x_rounds", "sum"),
        acs_sd=("ACS", lambda s: s.std(ddof=1) if len(s) > 1 else np.nan),
        agent_pool=("Agent", "nunique"),
        top_agent=("Agent", lambda s: s.mode().iat[0] if len(s.mode()) else s.iloc[0]),
        win_rate=("won", "mean"),
    ).reset_index()

    out["kills_pr"] = out["kills"] / out["rounds"]
    out["deaths_pr"] = out["deaths"] / out["rounds"]
    out["assists_pr"] = out["assists"] / out["rounds"]
    out["kd"] = out["kills"] / out["deaths"].replace(0, np.nan)
    out["fk_pr"] = out["first_kills"] / out["rounds"]
    out["fd_pr"] = out["first_deaths"] / out["rounds"]
    out["multi_pr"] = out["multi_kills"] / out["rounds"]
    out["acs"] = out["acs_x_rounds"] / out["rounds"]
    out["adr"] = out["adr_x_rounds"] / out["rounds"]
    out["hs"] = out["hs_x_rounds"] / out["rounds"]
    out["acs_cv"] = out["acs_sd"] / out["acs"].replace(0, np.nan)
    out["rounds_per_game"] = out["rounds"] / out["games"]

    # Descriptive role mix. Not used in the clustering model, so the clusters
    # are not forced to reproduce Agent role labels.
    role_counts = (
        df.groupby(["PlayerID", "role"])["GameID"].nunique().unstack(fill_value=0)
    )
    role_counts = role_counts.reindex(columns=ROLE_NAMES, fill_value=0)
    role_share = role_counts.div(role_counts.sum(axis=1), axis=0)
    role_share.columns = [f"role_{c}_share" for c in role_share.columns]
    out = out.merge(role_share.reset_index(), on="PlayerID", how="left")

    # Attrition log before filtering.
    attrition = [
        {"step": "Người chơi trong bảng điểm sạch", "players": int(out["PlayerID"].nunique())},
        {
            "step": f"Đủ ≥{MIN_GAMES_PER_PLAYER} ván",
            "players": int((out["games"] >= MIN_GAMES_PER_PLAYER).sum()),
        },
        {
            "step": f"Đủ ≥{MIN_ROUNDS_PER_PLAYER} round",
            "players": int(
                ((out["games"] >= MIN_GAMES_PER_PLAYER) & (out["rounds"] >= MIN_ROUNDS_PER_PLAYER)).sum()
            ),
        },
    ]

    out = out[
        (out["games"] >= MIN_GAMES_PER_PLAYER) & (out["rounds"] >= MIN_ROUNDS_PER_PLAYER)
    ].copy()

    attrition.append(
        {
            "step": "Đủ biến mô hình",
            "players": int(out[MODEL_FEATURES].notna().all(axis=1).sum()),
        }
    )
    out = out[out[MODEL_FEATURES].notna().all(axis=1)].copy()
    out = out.sort_values(["games", "rounds"], ascending=False).reset_index(drop=True)

    return out, pd.DataFrame(attrition)


def save_player_features(players: pd.DataFrame, attrition: pd.DataFrame) -> None:
    players.to_csv(DATA_PROCESSED / "player_features.csv", index=False)
    attrition.to_csv(DATA_PROCESSED / "player_attrition.csv", index=False)
