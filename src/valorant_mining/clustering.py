"""Z-score feature selection, K-Means and Average-linkage comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

from .config import (
    FEATURE_LABELS,
    MODEL_FEATURES,
    OUTPUT_TABLES,
    RANDOM_STATE,
    CLUSTER_FEATURES,
)


def winsorize(X: pd.DataFrame, lower: float = 0.01, upper: float = 0.99) -> pd.DataFrame:
    lo = X.quantile(lower)
    hi = X.quantile(upper)
    return X.clip(lower=lo, upper=hi, axis=1)


def _scale(players: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, np.ndarray]:
    raw = players[features].astype(float)
    clipped = winsorize(raw)
    scaled = StandardScaler().fit_transform(clipped)
    return clipped, scaled


def prepare_matrix(players: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Clip the 1st/99th percentiles and apply Z-score to selected features."""
    return _scale(players, CLUSTER_FEATURES)


def evaluate_k(X_cluster: np.ndarray, k_min: int = 2, k_max: int = 8) -> pd.DataFrame:
    rows = []
    for k in range(k_min, k_max + 1):
        model = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE)
        labels = model.fit_predict(X_cluster)
        rows.append(
            {
                "k": k,
                "inertia": model.inertia_,
                "silhouette": silhouette_score(X_cluster, labels),
                "calinski_harabasz": calinski_harabasz_score(X_cluster, labels),
                "davies_bouldin": davies_bouldin_score(X_cluster, labels),
                "smallest_cluster": int(np.bincount(labels).min()),
                "largest_cluster": int(np.bincount(labels).max()),
            }
        )
    return pd.DataFrame(rows)


def choose_k(evaluation: pd.DataFrame, k_min: int = 2, k_max: int = 8) -> int:
    candidates = evaluation[evaluation["k"].between(k_min, k_max)]
    return int(candidates.loc[candidates["silhouette"].idxmax(), "k"])


def fit_kmeans(X_cluster: np.ndarray, k: int) -> tuple[np.ndarray, KMeans]:
    model = KMeans(n_clusters=k, n_init=50, random_state=RANDOM_STATE)
    labels = model.fit_predict(X_cluster)
    return labels, model


def stability_bootstrap(
    X_cluster: np.ndarray,
    base_labels: np.ndarray,
    k: int,
    n_boot: int = 30,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    rows = []
    n = len(X_cluster)
    for i in range(n_boot):
        idx = rng.choice(n, size=int(n * 0.8), replace=False)
        model = KMeans(n_clusters=k, n_init=10, random_state=int(rng.integers(1_000_000)))
        labels = model.fit_predict(X_cluster[idx])
        rows.append(
            {
                "bootstrap": i,
                "n": len(idx),
                "ari_vs_full": adjusted_rand_score(base_labels[idx], labels),
            }
        )
    return pd.DataFrame(rows)


def hierarchical_comparison(X_cluster: np.ndarray, k: int, base_labels: np.ndarray) -> dict:
    model = AgglomerativeClustering(n_clusters=k, linkage="average")
    labels = model.fit_predict(X_cluster)
    return {
        "cluster_sizes": np.bincount(labels).tolist(),
        "ari_kmeans_vs_average": adjusted_rand_score(base_labels, labels),
        "silhouette_average": silhouette_score(X_cluster, labels),
    }


def correlation_tables(players: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    corr = players[MODEL_FEATURES].corr().round(3)
    rows = []
    for i, left in enumerate(MODEL_FEATURES):
        for right in MODEL_FEATURES[i + 1 :]:
            value = corr.loc[left, right]
            if abs(value) >= 0.70:
                rows.append(
                    {
                        "feature_a": left,
                        "feature_b": right,
                        "correlation": float(value),
                        "abs_correlation": float(abs(value)),
                    }
                )
    high = pd.DataFrame(rows).sort_values("abs_correlation", ascending=False)
    return corr, high


def sensitivity_analysis(
    players: pd.DataFrame, primary_labels: np.ndarray, k: int
) -> pd.DataFrame:
    """Compare selected and full feature sets at the same cluster count."""
    rows = []
    for name, features in (("Selected Z-score features", CLUSTER_FEATURES),
                           ("All 11 Z-score features", MODEL_FEATURES)):
        _, matrix = _scale(players, features)
        labels, _ = fit_kmeans(matrix, k)
        rows.append({"method": name, "n_features": len(features),
                     "silhouette": silhouette_score(matrix, labels),
                     "ari_vs_primary": adjusted_rand_score(primary_labels, labels),
                     "cluster_sizes": np.bincount(labels).tolist(),
                     "silhouette_space": "Z-score features"})
    return pd.DataFrame(rows)


def cluster_profiles(players: pd.DataFrame, labels: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = players.copy()
    df["cluster"] = labels

    overall_mean = df[MODEL_FEATURES].mean()
    overall_sd = df[MODEL_FEATURES].std(ddof=0).replace(0, np.nan)

    raw = df.groupby("cluster")[MODEL_FEATURES].mean()
    z = (raw - overall_mean) / overall_sd
    sizes = df.groupby("cluster").size().rename("n_players")
    role_cols = [c for c in df.columns if c.startswith("role_")]
    roles = df.groupby("cluster")[role_cols].mean()
    win_rate = df.groupby("cluster")["win_rate"].mean().rename("win_rate")

    raw = raw.join(sizes).join(roles).join(win_rate).round(4)
    z = z.round(3)
    z = z.join(sizes)

    def _top(row: pd.Series, n: int = 3) -> str:
        ordered = row.drop(labels=["n_players"], errors="ignore").sort_values(ascending=False)
        return ", ".join(FEATURE_LABELS.get(k, k) for k in ordered.head(n).index)

    def _bottom(row: pd.Series, n: int = 2) -> str:
        ordered = row.drop(
            labels=["n_players", "top_features", "low_features"], errors="ignore"
        ).sort_values()
        return ", ".join(FEATURE_LABELS.get(k, k) for k in ordered.head(n).index)

    z["top_features"] = z.apply(_top, axis=1)
    z["low_features"] = z.apply(_bottom, axis=1)
    return raw, z


def label_clusters(z: pd.DataFrame) -> dict[int, str]:
    """Short data-driven labels based on each cluster's strongest z-scores.

    These are descriptions of the measured profile, not claims about in-game
    roles such as "duelist" or "IGL".
    """
    names = {}
    for cluster, row in z.iterrows():
        values = row.drop(
            labels=["n_players", "top_features", "low_features"], errors="ignore"
        )
        impact = values[["kills_pr", "acs", "adr", "fk_pr", "multi_pr"]].mean()
        risk = values[["deaths_pr", "fd_pr"]].mean()
        efficiency = values[["kd", "assists_pr", "hs"]].mean() - values["deaths_pr"]

        if impact > 0.5 and values["fk_pr"] > 0.5:
            names[int(cluster)] = "Mở giao tranh · Sát thương cao"
        elif (risk > 0.1 or values["kd"] < -0.5) and impact < 0:
            names[int(cluster)] = "Chết nhiều · Hiệu quả thấp"
        elif efficiency > 0.1 and risk < 0:
            names[int(cluster)] = "Ít chết · Hiệu quả cao"
        elif impact > 0.2:
            names[int(cluster)] = "Sát thương cao"
        else:
            names[int(cluster)] = "Cân bằng"
    return names


def run_clustering(players: pd.DataFrame) -> dict:
    clipped, X_cluster = prepare_matrix(players)

    evaluation = evaluate_k(X_cluster, 2, 8)
    k = choose_k(evaluation)
    labels, model = fit_kmeans(X_cluster, k)

    evaluation["chosen"] = evaluation["k"] == k
    silhouette_final = silhouette_score(X_cluster, labels)
    stability = stability_bootstrap(X_cluster, labels, k)
    average = hierarchical_comparison(X_cluster, k, labels)
    sensitivity = sensitivity_analysis(players, labels, k)
    correlation, high_correlation = correlation_tables(players)

    players = players.copy()
    players["cluster"] = labels
    players["plot_x"] = X_cluster[:, 0]
    players["plot_y"] = X_cluster[:, 1]

    raw, z = cluster_profiles(players, labels)
    names = label_clusters(z)
    players["cluster_label"] = players["cluster"].map(names)
    raw["cluster_label"] = raw.index.map(names)
    z["cluster_label"] = z.index.map(names)

    summary = {
        "k": k,
        "best_silhouette_k": int(evaluation.loc[evaluation["silhouette"].idxmax(), "k"]),
        "best_silhouette": float(evaluation["silhouette"].max()),
        "silhouette": silhouette_final,
        "stability_mean_ari": stability["ari_vs_full"].mean(),
        "stability_min_ari": stability["ari_vs_full"].min(),
        "average_cluster_sizes": average["cluster_sizes"],
        "average_ari": average["ari_kmeans_vs_average"],
        "average_silhouette": average["silhouette_average"],
        "features": CLUSTER_FEATURES,
        "n_features": len(CLUSTER_FEATURES),
        "n_players": int(len(players)),
        "cluster_sizes": players.groupby("cluster").size().to_dict(),
        "cluster_labels": names,
        "feature_variance": clipped.var().round(4).to_dict(),
    }

    return {
        "players": players,
        "evaluation": evaluation,
        "stability": stability,
        "raw_profiles": raw,
        "z_profiles": z,
        "summary": summary,
        "sensitivity": sensitivity,
        "correlation": correlation,
        "high_correlation": high_correlation,
    }


def save_clustering(result: dict) -> None:
    result["players"].to_csv(OUTPUT_TABLES / "player_clusters.csv", index=False)
    result["evaluation"].to_csv(OUTPUT_TABLES / "cluster_evaluation.csv", index=False)
    result["stability"].to_csv(OUTPUT_TABLES / "cluster_stability.csv", index=False)
    result["raw_profiles"].to_csv(OUTPUT_TABLES / "cluster_profiles_raw.csv")
    result["z_profiles"].to_csv(OUTPUT_TABLES / "cluster_profiles_z.csv")
    result["sensitivity"].to_csv(OUTPUT_TABLES / "clustering_sensitivity.csv", index=False)
    result["correlation"].to_csv(OUTPUT_TABLES / "feature_correlation.csv")
    result["high_correlation"].to_csv(OUTPUT_TABLES / "feature_correlation_high.csv", index=False)
    pd.Series(result["summary"], name="value").rename_axis("metric").to_csv(
        OUTPUT_TABLES / "clustering_summary.csv", header=True
    )
