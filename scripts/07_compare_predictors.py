#!/usr/bin/env python
"""Compare pregame composition models on a strictly later test period.

One row represents a game, using the alphabetically first team as the focal side.
Only map, patch and both locked Agent compositions are available to models.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

from valorant_mining.config import DATA_PROCESSED, FIGURE_DIR, OUTPUT_TABLES


def make_game_table(comps: pd.DataFrame) -> pd.DataFrame:
    comps = comps.dropna(subset=["won", "Date"]).copy()
    comps["date"] = pd.to_datetime(comps["Date"], errors="coerce").dt.normalize()
    comps = comps.dropna(subset=["date"])
    comps = comps[comps.groupby("GameID")["GameID"].transform("size") == 2]
    comps = comps.sort_values(["GameID", "team"])
    comps["team_order"] = comps.groupby("GameID").cumcount()
    a = comps[comps["team_order"] == 0].set_index("GameID")
    b = comps[comps["team_order"] == 1].set_index("GameID")
    ids = a.index.intersection(b.index)
    a, b = a.loc[ids], b.loc[ids]
    if len(ids) != len(set(ids)) or not ((a["won"].to_numpy() + b["won"].to_numpy()) == 1).all():
        raise ValueError("Each game must contain two opposing win labels")
    for column in ("MatchID", "date", "Map", "Patch"):
        if not a[column].fillna("unknown").equals(b[column].fillna("unknown")):
            raise ValueError(f"Opposing teams disagree on {column}")
    agents = sorted(set("|".join(comps["agents_str"]).split("|")))
    data = pd.DataFrame({"GameID": ids, "MatchID": a["MatchID"].to_numpy(),
                         "date": a["date"].to_numpy(), "Map": a["Map"].to_numpy(),
                         "Patch": a["Patch"].fillna("unknown").astype(str).to_numpy(),
                         "won": a["won"].astype(int).to_numpy()})
    for agent in agents:
        data[f"agent_{agent}"] = (
            a["agents_str"].str.split("|").apply(lambda xs: int(agent in xs)).to_numpy()
            - b["agents_str"].str.split("|").apply(lambda xs: int(agent in xs)).to_numpy()
        )
    return data.sort_values(["date", "GameID"]).reset_index(drop=True)


def temporal_split(games: pd.DataFrame, train_date_fraction: float = 0.8) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split on whole calendar dates and keep all maps from a match together."""
    if not 0 < train_date_fraction < 1:
        raise ValueError("train_date_fraction must be between zero and one")
    dates = np.sort(games["date"].unique())
    if len(dates) < 2:
        raise ValueError("At least two distinct dates are required")
    boundary = dates[min(int(len(dates) * train_date_fraction), len(dates) - 1)]
    train = games[games["date"] < boundary].copy()
    test = games[games["date"] >= boundary].copy()
    if train.empty or test.empty or train["date"].max() >= test["date"].min():
        raise ValueError("Train and test periods must be strictly separated")
    if set(train["GameID"]) & set(test["GameID"]):
        raise ValueError("GameID appears on both sides of the split")
    if set(train["MatchID"]) & set(test["MatchID"]):
        raise ValueError("MatchID appears on both sides of the split")
    return train, test


def block_bootstrap_log_loss(pred: pd.DataFrame, model_names: list[str],
                             n_boot: int = 2000, seed: int = 42) -> pd.DataFrame:
    """Paired log-loss improvement CIs, resampling whole matches."""
    y = pred["won"].to_numpy(dtype=float)
    groups, group_index = np.unique(pred["MatchID"].to_numpy(), return_inverse=True)
    n_groups = len(groups)
    group_sizes = np.bincount(group_index, minlength=n_groups)
    sample = np.random.default_rng(seed).integers(0, n_groups, size=(n_boot, n_groups))
    denominator = group_sizes[sample].sum(axis=1)

    def losses(name: str) -> np.ndarray:
        p = np.clip(pred[name].to_numpy(dtype=float), 1e-15, 1 - 1e-15)
        return -(y * np.log(p) + (1 - y) * np.log1p(-p))

    base = losses("Train prevalence")
    rows = []
    for name in model_names:
        improvement = base - losses(name)
        group_sums = np.bincount(group_index, weights=improvement, minlength=n_groups)
        replicates = group_sums[sample].sum(axis=1) / denominator
        rows.append({"model": name, "delta_log_loss_vs_baseline": float(improvement.mean()),
                     "delta_ci_low": float(np.quantile(replicates, 0.025)),
                     "delta_ci_high": float(np.quantile(replicates, 0.975)),
                     "bootstrap_groups": n_groups, "bootstrap_replicates": n_boot})
    return pd.DataFrame(rows)


def diagnostic_tables(pred: pd.DataFrame, model_names: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Out-of-time performance by map/month and reliability deciles."""
    frame = pred.copy()
    frame["month"] = frame["date"].dt.to_period("M").astype(str)
    by_map = diagnostic_tables_group(frame, "Map", model_names)
    by_month = diagnostic_tables_group(frame, "month", model_names)
    calibration = []
    for model in model_names:
        if model == "Train prevalence":
            continue
        bins = pd.qcut(frame[model].rank(method="first"), q=10, labels=False)
        grouped = frame.assign(bin=bins).groupby("bin", sort=True)
        for bin_id, group in grouped:
            calibration.append({"model": model, "decile": int(bin_id) + 1,
                                "n_games": len(group), "mean_predicted": group[model].mean(),
                                "observed_win_rate": group["won"].mean()})
    return by_map, by_month, pd.DataFrame(calibration)


def diagnostic_tables_group(frame: pd.DataFrame, column: str, model_names: list[str]) -> pd.DataFrame:
    rows = []
    for key, group in frame.groupby(column, sort=True):
        y = group["won"]
        baseline_loss = log_loss(y, group["Train prevalence"], labels=[0, 1])
        for model in model_names:
            probability = group[model]
            loss = log_loss(y, probability, labels=[0, 1])
            rows.append({column: key, "model": model, "n_games": len(group),
                         "win_rate": float(y.mean()),
                         "roc_auc": roc_auc_score(y, probability) if y.nunique() == 2 else np.nan,
                         "log_loss": loss, "delta_log_loss_vs_baseline": baseline_loss - loss})
    return pd.DataFrame(rows)


def main() -> None:
    compositions = pd.read_csv(DATA_PROCESSED / "team_compositions.csv")
    games = make_game_table(compositions)
    train, test = temporal_split(games)
    numeric = [c for c in games if c.startswith("agent_")]
    categorical = ["Map", "Patch"]
    features = categorical + numeric
    X_train, X_test = train[features], test[features]
    y_train, y_test = train["won"], test["won"]
    prep = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
                              ("num", "passthrough", numeric)])
    models = {
        "Logistic Regression": make_pipeline(prep, LogisticRegression(max_iter=1000, C=1.0)),
        "Random Forest": make_pipeline(prep, RandomForestClassifier(
            n_estimators=300, max_depth=8, min_samples_leaf=30,
            max_features="sqrt", random_state=42, n_jobs=4)),
        "AdaBoost": make_pipeline(prep, AdaBoostClassifier(
            estimator=DecisionTreeClassifier(max_depth=1, random_state=42),
            n_estimators=200, learning_rate=0.05, random_state=42)),
    }
    rows = []
    pred = test[["GameID", "MatchID", "date", "Map", "won"]].copy()
    baseline_p = np.full(len(test), float(y_train.mean()))
    pred["Train prevalence"] = baseline_p
    rows.append({"model": "Train prevalence", "n_train": len(train), "n_test": len(test),
                 "test_accuracy": accuracy_score(y_test, baseline_p >= 0.5),
                 "test_roc_auc": 0.5, "test_log_loss": log_loss(y_test, baseline_p),
                 "test_brier": brier_score_loss(y_test, baseline_p),
                 "fit_predict_seconds": 0.0})
    for name, model in models.items():
        start = time.perf_counter()
        model.fit(X_train, y_train)
        p = model.predict_proba(X_test)[:, 1]
        elapsed = time.perf_counter() - start
        pred[name] = p
        rows.append({"model": name, "n_train": len(train), "n_test": len(test),
                     "test_accuracy": accuracy_score(y_test, p >= 0.5),
                     "test_roc_auc": roc_auc_score(y_test, p),
                     "test_log_loss": log_loss(y_test, p),
                     "test_brier": brier_score_loss(y_test, p),
                     "fit_predict_seconds": elapsed})
    result = pd.DataFrame(rows).sort_values("test_log_loss")
    ci = block_bootstrap_log_loss(pred, result["model"].tolist())
    result = result.merge(ci, on="model", validate="one_to_one")
    by_map, by_month, calibration = diagnostic_tables(pred, result["model"].tolist())
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_TABLES / "predictor_comparison.csv", index=False)
    pred.to_csv(OUTPUT_TABLES / "predictor_test_predictions.csv", index=False)
    by_map.to_csv(OUTPUT_TABLES / "predictor_by_map.csv", index=False)
    by_month.to_csv(OUTPUT_TABLES / "predictor_by_month.csv", index=False)
    calibration.to_csv(OUTPUT_TABLES / "predictor_calibration.csv", index=False)
    team1 = compositions[(compositions["side"] == "Team1") & compositions["won"].notna()]
    known_patches = set(train["Patch"])
    meta = {"train_first": str(train.date.min().date()), "train_last": str(train.date.max().date()),
            "test_first": str(test.date.min().date()), "test_last": str(test.date.max().date()),
            "n_games": len(games), "n_train": len(train), "n_test": len(test),
            "n_train_matches": int(train.MatchID.nunique()), "n_test_matches": int(test.MatchID.nunique()),
            "positive_rate_train": float(y_train.mean()), "positive_rate_test": float(y_test.mean()),
            "features": features, "split": "80% of unique dates for training; remaining dates for test",
            "raw_team1_win_rate": float(team1["won"].mean()),
            "unseen_patch_test_games": int((~test["Patch"].isin(known_patches)).sum()),
            "unseen_patch_test_labels": sorted(set(test["Patch"]) - known_patches)}
    (OUTPUT_TABLES / "predictor_split.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    baseline_loss = float(result.loc[result.model == "Train prevalence", "test_log_loss"].iloc[0])
    improvement = baseline_loss - result["test_log_loss"]
    ax.bar(result["model"], improvement, color=["#23395b", "#587a9b", "#9db4c9", "#b6bec7"])
    ax.axhline(0, color="#333333", linewidth=1)
    ax.set(ylabel="Mức giảm log loss so với mốc tần suất train", title="Dự đoán thắng trên tập test thời gian sau")
    fig.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / "predictor_comparison.png", dpi=160)
    plt.close(fig)
    print(meta)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
