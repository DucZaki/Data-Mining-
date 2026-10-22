#!/usr/bin/env python
"""Step 2: K-Means player clustering."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from valorant_mining.clustering import run_clustering, save_clustering
from valorant_mining.config import DATA_PROCESSED, FIGURE_DIR
from valorant_mining.plotting import plot_clustering


def main() -> None:
    players = pd.read_csv(DATA_PROCESSED / "player_features.csv")
    result = run_clustering(players)
    save_clustering(result)
    plot_clustering(result)

    ev = result["evaluation"].copy()
    print("\nĐánh giá k theo silhouette:")
    print(ev[["k", "inertia", "silhouette", "calinski_harabasz", "davies_bouldin"]].to_string(index=False))
    summary = result["summary"]
    print(f"\nk chọn: {summary['k']}")
    print(f"Silhouette: {summary['silhouette']:.3f}")
    print(f"Độ ổn định bootstrap (ARI trung bình): {summary['stability_mean_ari']:.3f}")
    print(f"ARI K-Means vs Ward: {summary['ward_ari']:.3f}")
    print("\nKích thước cụm:")
    for cluster, size in summary["cluster_sizes"].items():
        print(f"  C{cluster}: {size} người chơi — {summary['cluster_labels'][cluster]}")
    print("\nChân dung cụm (z-score):")
    z = result["z_profiles"].copy()
    print(z[["n_players", "top_features", "low_features"]].to_string())
    print(f"\nHình: {FIGURE_DIR}")


if __name__ == "__main__":
    main()
