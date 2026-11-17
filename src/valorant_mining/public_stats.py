"""Visitor-facing historical map, Agent, and composition statistics."""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from math import sqrt

import pandas as pd

from .config import AGENT_ROLES, VALID_MAPS

PERIODS = {
    "all": ("2020–2022", None, None),
    "2020": ("Năm 2020", "2020-01-01", "2021-01-01"),
    "2021": ("Năm 2021", "2021-01-01", "2022-01-01"),
    "late": ("Từ 07/2021", "2021-07-01", None),
}


def wilson_interval(wins: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    p = wins / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def summarize_slice(frame: pd.DataFrame) -> dict:
    """Every denominator is a team-map; results use only rows with a win label."""
    teams = len(frame)
    labeled = frame[frame["won"].notna()]
    agent_counts: Counter[str] = Counter()
    agent_wins: Counter[str] = Counter()
    agent_labeled: Counter[str] = Counter()
    comp_counts: Counter[tuple[str, ...]] = Counter()
    comp_wins: Counter[tuple[str, ...]] = Counter()
    comp_labeled: Counter[tuple[str, ...]] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    event_counts: Counter[str] = Counter()

    for row in frame.itertuples(index=False):
        agents = tuple(sorted(set(str(row.agents_str).split("|"))))
        if len(agents) != 5:
            continue
        agent_counts.update(agents)
        comp_counts[agents] += 1
        pair_counts.update(combinations(agents, 2))
        if pd.notna(row.EventName) and str(row.EventName).strip():
            event_counts[str(row.EventName)] += 1
        if pd.notna(row.won):
            agent_labeled.update(agents)
            comp_labeled[agents] += 1
            if int(row.won) == 1:
                agent_wins.update(agents)
                comp_wins[agents] += 1

    agents = []
    for name, picks in agent_counts.items():
        n = agent_labeled[name]
        wins = agent_wins[name]
        low, high = wilson_interval(wins, n)
        agents.append({"name": name, "role": AGENT_ROLES.get(name, "other"),
                       "picks": picks, "pick_rate": picks / teams if teams else 0,
                       "labeled": n, "wins": wins, "win_rate": wins / n if n else None,
                       "ci_low": low, "ci_high": high})
    agents.sort(key=lambda x: (-x["picks"], x["name"]))

    comps = []
    for names, picks in comp_counts.items():
        n = comp_labeled[names]
        wins = comp_wins[names]
        low, high = wilson_interval(wins, n)
        comps.append({"agents": list(names), "picks": picks,
                      "pick_rate": picks / teams if teams else 0,
                      "labeled": n, "wins": wins,
                      "win_rate": wins / n if n else None,
                      "ci_low": low, "ci_high": high})
    comps.sort(key=lambda x: (-x["picks"], x["agents"]))
    enough = [c for c in comps if c["labeled"] >= 100]
    strongest = max(enough, key=lambda c: (c["ci_low"], c["labeled"])) if enough else None

    pairs = [{"agents": list(names), "picks": count,
              "share": count / teams if teams else 0}
             for names, count in pair_counts.most_common(8)]
    events = [{"name": name, "teams": count, "games": count // 2}
              for name, count in event_counts.most_common(6)]
    return {"teams": teams, "games": frame["GameID"].nunique(),
            "unique_comps": len(comp_counts),
            "labeled_teams": len(labeled), "first_date": str(frame["Date"].min())[:10] if teams else None,
            "last_date": str(frame["Date"].max())[:10] if teams else None,
            "agents": agents, "comps": comps[:12], "strongest_comp": strongest,
            "pairs": pairs, "events": events}


def build_public_data(frame: pd.DataFrame) -> dict:
    frame = frame[frame["Map"].isin(VALID_MAPS)].copy()
    frame["Date"] = pd.to_datetime(frame["Date"])
    data = {"periods": {key: label for key, (label, _, _) in PERIODS.items()}, "maps": {}}
    for map_name in VALID_MAPS:
        mapped = frame[frame["Map"] == map_name]
        data["maps"][map_name] = {}
        for key, (_, start, stop) in PERIODS.items():
            subset = mapped
            if start:
                subset = subset[subset["Date"] >= pd.Timestamp(start)]
            if stop:
                subset = subset[subset["Date"] < pd.Timestamp(stop)]
            data["maps"][map_name][key] = summarize_slice(subset)
    data["total_games"] = int(frame["GameID"].nunique())
    data["first_date"] = str(frame["Date"].min())[:10]
    data["last_date"] = str(frame["Date"].max())[:10]
    return data
