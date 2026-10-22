"""Cleaning and dataset construction for the Valorant mining project.

The raw database contains one row per player per map in ``Game_Scoreboard``.
A usable *team composition* needs exactly five valid players and five distinct
Agents on each side, so the cleaning is done at team level first and only then
at game level.
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import VALID_MAPS
from .db import read_sql


SCOREBOARD_SQL = """
SELECT
    s.GameID, s.PlayerID, s.PlayerName, s.TeamAbbreviation, s.Agent,
    s.ACS, s.Kills, s.Deaths, s.Assists, s.PlusMinus, s.KAST_Percent,
    s.ADR, s.HS_Percent, s.FirstKills, s.FirstDeaths, s.FKFD_PlusMinus,
    s.Num_2Ks, s.Num_3Ks, s.Num_4Ks, s.Num_5Ks,
    s.OnevOne, s.OnevTwo, s.OnevThree, s.OnevFour, s.OnevFive,
    s.Econ, s.Plants, s.Defuses
FROM Game_Scoreboard AS s
"""

GAMES_SQL = """
SELECT
    g.GameID, g.MatchID, g.Map, g.Team1ID, g.Team2ID, g.Team1, g.Team2,
    g.Winner, g.Team1_TotalRounds, g.Team2_TotalRounds,
    g.Team1_SideFirstHalf, g.Team2_SideFirstHalf,
    m.Date, m.Patch, m.EventID, m.EventName, m.EventStage
FROM Games AS g
LEFT JOIN Matches AS m ON m.MatchID = g.MatchID
"""

ROUNDS_SQL = "SELECT GameID, RoundHistory FROM Game_Rounds"


@dataclass
class CleanData:
    games: pd.DataFrame
    scoreboard: pd.DataFrame
    compositions: pd.DataFrame
    audit: dict = field(default_factory=dict)


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, float) and np.isnan(value)) or str(value).strip() == ""


def parse_round_history(value) -> dict[int, dict] | None:
    """Parse the Python-literal ``RoundHistory`` field stored as TEXT."""
    if _is_blank(value) or not isinstance(value, str):
        return None
    try:
        history = ast.literal_eval(value)
        if not isinstance(history, dict) or not history:
            return None
        return {int(k): v for k, v in history.items() if isinstance(v, dict)}
    except (ValueError, SyntaxError, TypeError):
        return None


def _parse_score(value) -> tuple[int, int] | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", value)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _round_summary(value) -> dict:
    history = parse_round_history(value)
    if history is None:
        return {
            "rh_rounds": np.nan,
            "rh_first_winner": None,
            "rh_first_team1_won": np.nan,
            "rh_final_1": np.nan,
            "rh_final_2": np.nan,
            "rh_consistent": False,
        }

    keys = sorted(history)
    first = history[keys[0]]
    last = history[keys[-1]]
    first_score = _parse_score(first.get("ScoreAfterRound"))
    final_score = _parse_score(last.get("ScoreAfterRound"))

    rounds = len(history)
    consistent = bool(
        final_score is not None
        and final_score[0] != final_score[1]
        and final_score[0] + final_score[1] == rounds
        and rounds >= 13
    )

    return {
        "rh_rounds": rounds,
        "rh_first_winner": str(first.get("RoundWinner", "")).strip() or None,
        "rh_first_team1_won": (first_score[0] > first_score[1]) if first_score else np.nan,
        "rh_final_1": final_score[0] if final_score else np.nan,
        "rh_final_2": final_score[1] if final_score else np.nan,
        "rh_consistent": consistent,
    }


def _norm_abbr(value) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value).upper())


def _norm_team(value) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _match_abbr(first_winner: str | None, abbreviations: list[str]) -> str | None:
    """Match the abbreviation used in RoundHistory to a scoreboard abbreviation."""
    if not first_winner:
        return None
    target = _norm_abbr(first_winner)

    exact = [a for a in abbreviations if _norm_abbr(a) == target]
    if len(exact) == 1:
        return exact[0]

    prefix = [
        a
        for a in abbreviations
        if _norm_abbr(a).startswith(target) or target.startswith(_norm_abbr(a))
    ]
    if len(prefix) == 1:
        return prefix[0]
    return None


def clean_scoreboard(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Normalize player rows and remove records that cannot identify a player."""
    df = raw.copy()
    n_raw = len(df)

    df["Agent"] = df["Agent"].fillna("").astype(str).str.strip().str.lower()
    df["TeamAbbreviation"] = (
        df["TeamAbbreviation"].fillna("").astype(str).str.strip()
    )
    df["PlayerName"] = df["PlayerName"].fillna("").astype(str).str.strip()
    df["GameID"] = df["GameID"].astype(str)

    df = df[df["PlayerID"].notna()].copy()
    df["PlayerID"] = (
        df["PlayerID"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    )
    n_after_pid = len(df)

    before = len(df)
    df = df[(df["Agent"] != "") & (df["TeamAbbreviation"] != "") & (df["PlayerID"] != "")]
    n_bad_identity = before - len(df)

    before = len(df)
    df = df.drop_duplicates(subset=["GameID", "PlayerID"], keep="first")
    n_duplicate_player_game = before - len(df)

    audit = {
        "scoreboard_rows_raw": int(n_raw),
        "dropped_missing_player_id": int(n_raw - n_after_pid),
        "dropped_bad_agent_or_team": int(n_bad_identity),
        "dropped_duplicate_player_game": int(n_duplicate_player_game),
        "scoreboard_rows_clean": int(len(df)),
    }
    return df, audit


def _valid_teams(scoreboard: pd.DataFrame) -> pd.DataFrame:
    teams = (
        scoreboard.groupby(["GameID", "TeamAbbreviation"], as_index=False)
        .agg(
            n_players=("PlayerID", "nunique"),
            n_agents=("Agent", "nunique"),
            agents=("Agent", lambda s: "|".join(sorted(set(s)))),
        )
    )
    teams = teams[(teams["n_players"] == 5) & (teams["n_agents"] == 5)]
    return teams


def _games_with_two_valid_teams(teams: pd.DataFrame) -> set[str]:
    counts = teams.groupby("GameID").agg(
        n_teams=("TeamAbbreviation", "nunique"),
        n_players=("n_players", "sum"),
    )
    ok = counts[(counts["n_teams"] == 2) & (counts["n_players"] == 10)]
    return set(ok.index)


def _learn_team_abbreviations(games: pd.DataFrame, teams: pd.DataFrame) -> dict[str, str]:
    """Learn full team name -> abbreviation from games with reliable RoundHistory.

    This is only used as a fallback for the small share of games without a
    RoundHistory record. It avoids fuzzy name matching.
    """
    valid = games[games["team1_abbr"].notna()]
    counter: dict[str, Counter] = {}
    for row in valid.itertuples():
        pairs = [
            (row.Team1, row.team1_abbr),
            (row.Team2, row.team2_abbr),
        ]
        for name, abbr in pairs:
            if _is_blank(name) or _is_blank(abbr):
                continue
            counter.setdefault(_norm_team(name), Counter())[abbr] += 1

    mapping = {}
    for name, counts in counter.items():
        abbr, n = counts.most_common(1)[0]
        total = sum(counts.values())
        if n / total >= 0.75:
            mapping[name] = abbr
    return mapping


def build_clean_data() -> CleanData:
    raw_scoreboard = read_sql(SCOREBOARD_SQL)
    games = read_sql(GAMES_SQL)
    rounds = read_sql(ROUNDS_SQL)

    scoreboard, sb_audit = clean_scoreboard(raw_scoreboard)

    teams = _valid_teams(scoreboard)
    valid_game_ids = _games_with_two_valid_teams(teams)
    teams = teams[teams["GameID"].isin(valid_game_ids)].copy()

    games["GameID"] = games["GameID"].astype(str)
    rounds["GameID"] = rounds["GameID"].astype(str)
    rh = pd.DataFrame([{"GameID": gid, **_round_summary(h)} for gid, h in zip(rounds["GameID"], rounds["RoundHistory"])])
    games = games.merge(rh, on="GameID", how="left")
    games["rh_consistent"] = games["rh_consistent"].eq(True)
    games["rh_first_team1_won"] = games["rh_first_team1_won"].eq(True)

    games["total_rounds_games"] = games["Team1_TotalRounds"] + games["Team2_TotalRounds"]
    games["rounds"] = np.where(games["rh_consistent"], games["rh_rounds"], games["total_rounds_games"])
    games["rounds_source"] = np.where(games["rh_consistent"], "round_history", "games_totals")
    games["rounds_valid"] = games["rounds"].between(13, 40)
    games["rh_present"] = games["rh_rounds"].notna()
    # When RoundHistory exists but contradicts itself, the round denominator is
    # unreliable. Drop it rather than mixing two definitions of a round.
    games["rounds_reliable"] = (~games["rh_present"]) | games["rh_consistent"]

    clean = games[games["GameID"].isin(valid_game_ids)].copy()
    n_valid_rosters = len(clean)
    clean = clean[clean["rounds_valid"] & clean["rounds_reliable"]].copy()
    clean = clean[clean["Map"].isin(VALID_MAPS)].copy()

    # --- map each team to Team1 / Team2 side and derive win label ---
    abbr_by_game = teams.groupby("GameID")["TeamAbbreviation"].apply(list)
    clean["team1_abbr"] = pd.Series(None, index=clean.index, dtype="object")
    clean["team2_abbr"] = pd.Series(None, index=clean.index, dtype="object")

    for idx, row in clean.iterrows():
        abbrs = abbr_by_game.get(row["GameID"], [])
        if len(abbrs) != 2:
            continue
        if bool(row["rh_consistent"]) and not _is_blank(row["rh_first_winner"]):
            matched = _match_abbr(row["rh_first_winner"], abbrs)
            if matched is not None:
                team1_abbr = matched
                team2_abbr = [a for a in abbrs if a != matched][0]
                if bool(row["rh_first_team1_won"]):
                    clean.at[idx, "team1_abbr"] = team1_abbr
                    clean.at[idx, "team2_abbr"] = team2_abbr
                else:
                    clean.at[idx, "team1_abbr"] = team2_abbr
                    clean.at[idx, "team2_abbr"] = team1_abbr

    # Fallback for games with a missing RoundHistory: use the learned team map.
    learned = _learn_team_abbreviations(clean, teams)
    missing = clean["team1_abbr"].isna()
    for idx, row in clean[missing].iterrows():
        abbrs = abbr_by_game.get(row["GameID"], [])
        if len(abbrs) != 2:
            continue
        a1 = learned.get(_norm_team(row["Team1"]))
        a2 = learned.get(_norm_team(row["Team2"]))
        if a1 in abbrs and a2 in abbrs and a1 != a2:
            clean.at[idx, "team1_abbr"] = a1
            clean.at[idx, "team2_abbr"] = a2

    clean["team1_won"] = np.where(
        clean["rh_consistent"],
        clean["rh_final_1"] > clean["rh_final_2"],
        clean["Team1_TotalRounds"] > clean["Team2_TotalRounds"],
    ).astype(float)
    clean.loc[clean["team1_abbr"].isna(), "team1_won"] = np.nan

    # Attach side / win label back to player rows.
    columns = [
        "GameID", "MatchID", "Map", "Date", "Patch", "EventID", "EventName", "EventStage",
        "rounds", "team1_abbr", "team2_abbr", "team1_won", "rounds_source",
    ]
    game_info = clean[columns].copy()
    scoreboard = scoreboard[scoreboard["GameID"].isin(clean["GameID"])].copy()
    scoreboard = scoreboard.merge(game_info, on="GameID", how="left")

    def _player_won(row):
        if _is_blank(row["team1_won"]):
            return np.nan
        if row["TeamAbbreviation"] == row["team1_abbr"]:
            return int(bool(row["team1_won"]))
        if row["TeamAbbreviation"] == row["team2_abbr"]:
            return int(not bool(row["team1_won"]))
        return np.nan

    scoreboard["won"] = scoreboard.apply(_player_won, axis=1)
    scoreboard["side"] = np.select(
        [
            scoreboard["TeamAbbreviation"] == scoreboard["team1_abbr"],
            scoreboard["TeamAbbreviation"] == scoreboard["team2_abbr"],
        ],
        ["Team1", "Team2"],
        default="unknown",
    )

    # --- team compositions, one row per team per game ---
    comps = teams[teams["GameID"].isin(clean["GameID"])].copy()
    comps = comps.merge(game_info, on="GameID", how="left")
    comps["agents_list"] = comps["agents"].str.split("|")
    comps["agents_sorted"] = comps["agents_list"].apply(lambda xs: tuple(sorted(xs)))
    comps["agents_str"] = comps["agents_sorted"].apply(lambda xs: "|".join(xs))
    comps["n_agents"] = comps["agents_sorted"].apply(len)

    def _team_won(row):
        if _is_blank(row["team1_won"]):
            return np.nan
        if row["TeamAbbreviation"] == row["team1_abbr"]:
            return int(bool(row["team1_won"]))
        if row["TeamAbbreviation"] == row["team2_abbr"]:
            return int(not bool(row["team1_won"]))
        return np.nan

    comps["won"] = comps.apply(_team_won, axis=1)
    comps["side"] = np.select(
        [comps["TeamAbbreviation"] == comps["team1_abbr"],
         comps["TeamAbbreviation"] == comps["team2_abbr"]],
        ["Team1", "Team2"],
        default="unknown",
    )

    comp_cols = [
        "GameID", "MatchID", "Date", "Patch", "EventID", "EventName", "EventStage",
        "Map", "TeamAbbreviation", "side", "agents_sorted", "agents_str", "n_agents",
        "won", "rounds", "rounds_source",
    ]
    comps = comps[comp_cols].rename(columns={"TeamAbbreviation": "team"})

    audit = {
        **sb_audit,
        "games_raw": int(len(games)),
        "games_with_round_history": int(rh["rh_rounds"].notna().sum()),
        "round_history_inconsistent": int((games["rh_present"] & ~games["rh_consistent"]).sum()),
        "games_with_valid_rosters": int(n_valid_rosters),
        "games_after_round_and_map_filter": int(len(clean)),
        "games_with_winner_mapping": int(clean["team1_abbr"].notna().sum()),
        "teams_in_compositions": int(len(comps)),
        "compositions_with_win_label": int(comps["won"].notna().sum()),
        "players_remaining": int(scoreboard["PlayerID"].nunique()),
        "maps_kept": sorted(clean["Map"].unique().tolist()),
    }

    return CleanData(games=clean, scoreboard=scoreboard, compositions=comps, audit=audit)


def save_clean_data(clean: CleanData) -> None:
    from .config import DATA_PROCESSED

    clean.games.to_csv(DATA_PROCESSED / "clean_games.csv", index=False)
    clean.scoreboard.to_csv(DATA_PROCESSED / "clean_scoreboard.csv", index=False)
    clean.compositions.drop(columns=["agents_sorted"]).to_csv(
        DATA_PROCESSED / "team_compositions.csv", index=False
    )
    pd.Series(clean.audit, name="value").rename_axis("metric").to_csv(
        DATA_PROCESSED / "cleaning_audit.csv"
    )
