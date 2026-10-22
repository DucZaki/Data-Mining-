"""Agent co-occurrence mining and composition performance summaries."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder
from scipy.stats import fisher_exact

from .config import DATA_PROCESSED, OUTPUT_TABLES, VALID_MAPS


def benjamini_hochberg(p_values) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (q-values), no extra dependency."""
    p = np.asarray(p_values, dtype=float)
    n = len(p)
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q)
    out[order] = np.clip(q, 0, 1)
    return out


def wilson_interval(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (np.nan, np.nan)
    p = wins / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def _rule_text(items) -> str:
    return ", ".join(sorted(str(x) for x in items))


def mine_map_rules(
    comps: pd.DataFrame,
    map_name: str,
    max_len: int = 3,
    min_count: int = 12,
    min_confidence: float = 0.40,
    min_lift: float = 1.05,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run FP-Growth on one map's team compositions.

    Returns (rules, frequent_itemsets, augmented_compositions).
    """
    df = comps[comps["Map"] == map_name].copy()
    df = df[df["n_agents"] == 5].copy()
    df["agents_tuple"] = df["agents_str"].str.split("|").apply(tuple)
    n_teams = len(df)

    baskets = df["agents_tuple"].tolist()
    encoder = TransactionEncoder()
    onehot = encoder.fit(baskets).transform(baskets, sparse=False)
    basket_df = pd.DataFrame(onehot, columns=encoder.columns_)

    min_support = max(min_count / n_teams, 0.02) if n_teams else 0.02
    itemsets = fpgrowth(
        basket_df,
        min_support=min_support,
        use_colnames=True,
        max_len=max_len,
    )
    if itemsets.empty:
        return pd.DataFrame(), pd.DataFrame(), df

    itemsets["length"] = itemsets["itemsets"].apply(len)
    itemsets["support_count"] = (itemsets["support"] * n_teams).round().astype(int)
    itemsets["itemset"] = itemsets["itemsets"].apply(_rule_text)
    itemsets = itemsets.sort_values(["length", "support"], ascending=[True, False])

    rules = association_rules(itemsets, metric="confidence", min_threshold=min_confidence)
    if rules.empty:
        return pd.DataFrame(), itemsets, df

    rules = rules[rules["lift"] >= min_lift].copy()
    rules["antecedent"] = rules["antecedents"].apply(_rule_text)
    rules["consequent"] = rules["consequents"].apply(_rule_text)
    rules["rule"] = rules["antecedent"] + " → " + rules["consequent"]
    rules["antecedent_len"] = rules["antecedents"].apply(len)
    rules["consequent_len"] = rules["consequents"].apply(len)
    rules["support_count"] = (rules["support"] * n_teams).round().astype(int)
    rules["map"] = map_name
    rules["n_teams"] = n_teams
    rules["min_support"] = round(min_support, 4)

    # Win rate when the antecedent is present. Descriptive only: co-occurrence
    # does not identify a causal effect on winning.
    df["agents_set"] = df["agents_tuple"].apply(frozenset)
    baseline = df["won"].mean() if df["won"].notna().any() else np.nan
    perf = []
    for row in rules.itertuples():
        mask = df["agents_set"].apply(lambda s: row.antecedents.issubset(s))
        subset = df[mask & df["won"].notna()]
        rest = df[(~mask) & df["won"].notna()]
        n = len(subset)
        wins = int(subset["won"].sum()) if n else 0
        rest_n = len(rest)
        rest_wins = int(rest["won"].sum()) if rest_n else 0
        if n and rest_n:
            _, p_value = fisher_exact(
                [[wins, n - wins], [rest_wins, rest_n - rest_wins]],
                alternative="two-sided",
            )
        else:
            p_value = np.nan
        lo, hi = wilson_interval(wins, n)
        perf.append(
            {
                "n_with_antecedent": n,
                "wins_with_antecedent": wins,
                "win_rate_with_antecedent": wins / n if n else np.nan,
                "win_rate_ci_low": lo,
                "win_rate_ci_high": hi,
                "win_rate_without_antecedent": rest_wins / rest_n if rest_n else np.nan,
                "fisher_p_value": p_value,
                "map_baseline_win_rate": baseline,
            }
        )
    perf = pd.DataFrame(perf, index=rules.index)
    rules = rules.join(perf)

    rules = rules.sort_values(["lift", "confidence", "support"], ascending=False)
    return rules, itemsets, df


def exact_compositions(comps: pd.DataFrame, min_teams: int = 8) -> pd.DataFrame:
    rows = []
    for map_name, df in comps.groupby("Map"):
        labeled = df[df["won"].notna()]
        grouped = labeled.groupby("agents_str").agg(
            n=("won", "size"), wins=("won", "sum")
        )
        grouped = grouped[grouped["n"] >= min_teams].reset_index()
        if grouped.empty:
            continue
        grouped["win_rate"] = grouped["wins"] / grouped["n"]
        intervals = grouped.apply(
            lambda r: wilson_interval(int(r["wins"]), int(r["n"])), axis=1
        )
        grouped["win_rate_ci_low"] = [x[0] for x in intervals]
        grouped["win_rate_ci_high"] = [x[1] for x in intervals]
        grouped["map"] = map_name
        grouped["map_teams_labeled"] = len(labeled)
        grouped["map_win_rate"] = labeled["won"].mean()
        rows.append(grouped)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out = out.sort_values(["map", "n", "win_rate"], ascending=[True, False, False])

    # Compare each composition with the other teams on the same map. This is a
    # descriptive association test, not a causal estimate: team strength and
    # composition choice are confounded.
    p_values = []
    rest_rates = []
    for row in out.itertuples():
        n = int(row.n)
        wins = int(row.wins)
        map_n = int(row.map_teams_labeled)
        map_wins = int(round(row.map_win_rate * map_n))
        rest_n = map_n - n
        rest_wins = map_wins - wins
        rest_rates.append(rest_wins / rest_n if rest_n else np.nan)
        if n and rest_n:
            _, p_value = fisher_exact(
                [[wins, n - wins], [rest_wins, rest_n - rest_wins]],
                alternative="two-sided",
            )
        else:
            p_value = np.nan
        p_values.append(p_value)
    out["rest_win_rate"] = rest_rates
    out["win_rate_diff_vs_rest"] = out["win_rate"] - out["rest_win_rate"]
    out["fisher_p_value"] = p_values
    out["fisher_q_bh"] = benjamini_hochberg(p_values)
    out["significant_fdr"] = out["fisher_q_bh"] < 0.05
    return out.sort_values(["map", "n", "win_rate"], ascending=[True, False, False])


def agent_pick_rates(comps: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for map_name, df in comps.groupby("Map"):
        n = len(df)
        counts = df["agents_str"].str.split("|").explode().value_counts()
        for agent, count in counts.items():
            rows.append(
                {
                    "map": map_name,
                    "agent": agent,
                    "picks": int(count),
                    "teams": int(n),
                    "pick_rate": count / n,
                }
            )
    out = pd.DataFrame(rows)
    return out.sort_values(["map", "pick_rate"], ascending=[True, False])


def patch_pick_rates(comps: pd.DataFrame) -> pd.DataFrame:
    df = comps.copy()
    df["patch_major"] = (
        df["Patch"].astype(str).str.extract(r"Patch\s+(\d+)", expand=False).fillna("unknown")
    )
    df = df[df["patch_major"] != "unknown"]
    rows = []
    for (major, map_name), group in df.groupby(["patch_major", "Map"]):
        n = len(group)
        counts = group["agents_str"].str.split("|").explode().value_counts()
        for agent, count in counts.items():
            rows.append(
                {
                    "patch_major": f"Patch {major}.x",
                    "map": map_name,
                    "agent": agent,
                    "teams": n,
                    "picks": int(count),
                    "pick_rate": count / n,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["patch_major", "map", "pick_rate"], ascending=[True, True, False])


def report_rule_table(rules: pd.DataFrame, min_count: int = 30, top_n: int = 6) -> pd.DataFrame:
    """Rules worth putting in the written report: enough support to interpret."""
    if rules.empty:
        return rules
    filtered = rules[
        (rules["support_count"] >= min_count)
        & (rules["confidence"] >= 0.5)
        & (rules["antecedent_len"] <= 2)
    ].copy()
    filtered = filtered.sort_values(["map", "lift"], ascending=[True, False])
    return filtered.groupby("map", group_keys=False).head(top_n).reset_index(drop=True)


def composition_highlights(compositions: pd.DataFrame, min_n: int = 20) -> pd.DataFrame:
    if compositions.empty:
        return compositions
    out = compositions[compositions["n"] >= min_n].copy()
    out["ci_excludes_50"] = (out["win_rate_ci_low"] > 0.5) | (out["win_rate_ci_high"] < 0.5)
    return out.sort_values(
        ["significant_fdr", "fisher_q_bh", "n"], ascending=[False, True, False]
    )


def run_rules(comps: pd.DataFrame) -> dict:
    all_rules = []
    all_itemsets = []
    for map_name in VALID_MAPS:
        if (comps["Map"] == map_name).sum() == 0:
            continue
        rules, itemsets, _ = mine_map_rules(comps, map_name)
        if not rules.empty:
            all_rules.append(rules)
        if not itemsets.empty:
            itemsets = itemsets.copy()
            itemsets["map"] = map_name
            all_itemsets.append(itemsets)

    rules = pd.concat(all_rules, ignore_index=True) if all_rules else pd.DataFrame()
    itemsets = pd.concat(all_itemsets, ignore_index=True) if all_itemsets else pd.DataFrame()

    if not rules.empty:
        keep = [
            "map", "antecedent", "consequent", "rule", "support", "confidence", "lift",
            "support_count", "n_teams", "antecedent_len", "consequent_len",
            "n_with_antecedent", "win_rate_with_antecedent", "win_rate_ci_low",
            "win_rate_ci_high", "win_rate_without_antecedent", "fisher_p_value",
            "map_baseline_win_rate",
        ]
        rules = rules[keep].sort_values(["map", "lift"], ascending=[True, False])
        rules["fisher_q_bh"] = benjamini_hochberg(rules["fisher_p_value"])
        rules["significant_fdr"] = rules["fisher_q_bh"] < 0.05

        cross = (
            rules.groupby(["antecedent", "consequent", "rule"], as_index=False)
            .agg(
                maps=("map", "nunique"),
                mean_lift=("lift", "mean"),
                max_lift=("lift", "max"),
                mean_confidence=("confidence", "mean"),
                total_support_count=("support_count", "sum"),
            )
            .sort_values(["maps", "mean_lift"], ascending=False)
        )
    else:
        cross = pd.DataFrame()

    compositions = exact_compositions(comps)
    pick_rates = agent_pick_rates(comps)
    patch_rates = patch_pick_rates(comps)
    report_rules = report_rule_table(rules)
    highlights = composition_highlights(compositions)

    return {
        "rules": rules,
        "report_rules": report_rules,
        "cross_map_rules": cross,
        "itemsets": itemsets,
        "compositions": compositions,
        "composition_highlights": highlights,
        "pick_rates": pick_rates,
        "patch_rates": patch_rates,
        "summary": {
            "maps": sorted(comps["Map"].unique().tolist()),
            "teams": int(len(comps)),
            "teams_with_win_label": int(comps["won"].notna().sum()),
            "rules": int(len(rules)),
            "maps_with_rules": int(rules["map"].nunique()) if not rules.empty else 0,
            "top_rule": rules.iloc[0]["rule"] if not rules.empty else None,
            "top_lift": float(rules["lift"].max()) if not rules.empty else None,
            "exact_compositions_min8": int(len(compositions)),
            "rules_fdr_significant": int(rules["significant_fdr"].sum()) if not rules.empty else 0,
            "compositions_fdr_significant": int(compositions["significant_fdr"].sum())
            if not compositions.empty
            else 0,
            "compositions_tested": int(len(compositions)),
        },
    }


def save_rules(result: dict) -> None:
    result["rules"].to_csv(OUTPUT_TABLES / "agent_rules_by_map.csv", index=False)
    result["report_rules"].to_csv(OUTPUT_TABLES / "agent_rules_report.csv", index=False)
    result["cross_map_rules"].to_csv(OUTPUT_TABLES / "agent_rules_cross_map.csv", index=False)
    result["itemsets"].to_csv(OUTPUT_TABLES / "agent_frequent_itemsets.csv", index=False)
    result["compositions"].to_csv(OUTPUT_TABLES / "exact_compositions.csv", index=False)
    result["composition_highlights"].to_csv(
        OUTPUT_TABLES / "composition_highlights.csv", index=False
    )
    result["pick_rates"].to_csv(OUTPUT_TABLES / "agent_pick_rates_by_map.csv", index=False)
    result["patch_rates"].to_csv(OUTPUT_TABLES / "agent_pick_rates_by_patch.csv", index=False)
    pd.Series(result["summary"], name="value").rename_axis("metric").to_csv(
        OUTPUT_TABLES / "agent_rules_summary.csv", header=True
    )
