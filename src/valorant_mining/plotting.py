"""Figures for the audit, clustering and association-rule stages."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .config import FEATURE_LABELS, FIGURE_DIR, MODEL_FEATURES

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 130
plt.rcParams["savefig.bbox"] = "tight"

PALETTE = "viridis"


def _save(fig, name: str) -> None:
    fig.savefig(FIGURE_DIR / name)
    plt.close(fig)


def plot_audit(audit: dict, map_counts: pd.Series, games_per_player: pd.Series) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    map_counts.sort_values().plot.barh(ax=axes[0], color="#4c72b0")
    axes[0].set_title("Số ván theo bản đồ (dữ liệu gốc)")
    axes[0].set_xlabel("Số ván")
    axes[0].set_ylabel("")

    clipped = games_per_player.clip(upper=40)
    axes[1].hist(clipped, bins=range(0, 42, 2), color="#dd8452", edgecolor="white")
    axes[1].set_title("Số ván / người chơi (cắt tại 40)")
    axes[1].set_xlabel("Số ván")
    axes[1].set_ylabel("Số người chơi")
    fig.tight_layout()
    _save(fig, "01_audit_overview.png")

    fig, ax = plt.subplots(figsize=(8, 4.2))
    keys = [
        ("KAST_Percent", "KAST"),
        ("Num_2Ks", "Multi-kill (2K-5K)"),
        ("Agent", "Agent"),
        ("ACS", "ACS"),
        ("PlayerID", "PlayerID"),
    ]
    values = [audit.get(k, np.nan) for k, _ in keys]
    labels = [label for _, label in keys]
    sns.barplot(x=values, y=labels, ax=ax, color="#55a868")
    ax.set_xlabel("Tỷ lệ dòng thiếu (%)")
    ax.set_title("Mức độ thiếu dữ liệu của các cột quan trọng")
    for i, v in enumerate(values):
        ax.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=9)
    _save(fig, "01_audit_missing.png")


def plot_clustering(result: dict) -> None:
    ev = result["evaluation"]
    chosen = result["summary"]["k"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    axes[0].plot(ev["k"], ev["inertia"], marker="o", color="#4c72b0")
    axes[0].set_title("Elbow: tổng bình phương khoảng cách trong cụm")
    axes[0].set_xlabel("Số cụm k")
    axes[0].set_ylabel("Inertia")
    axes[0].axvline(chosen, color="#c44e52", linestyle="--", label=f"k chọn = {chosen}")
    axes[0].legend()

    axes[1].plot(ev["k"], ev["silhouette"], marker="o", color="#55a868")
    axes[1].set_title("Silhouette theo số cụm")
    axes[1].set_xlabel("Số cụm k")
    axes[1].set_ylabel("Silhouette")
    axes[1].axvline(chosen, color="#c44e52", linestyle="--", label=f"k chọn = {chosen}")
    axes[1].legend()
    fig.tight_layout()
    _save(fig, "02_cluster_selection.png")

    players = result["players"]
    fig, ax = plt.subplots(figsize=(8.5, 6))
    sns.scatterplot(
        data=players,
        x="pca1",
        y="pca2",
        hue="cluster_label",
        palette="tab10",
        s=28,
        alpha=0.75,
        linewidth=0,
        ax=ax,
    )
    ax.set_title(
        f"PC1–PC2 của không gian cụm PCA (k = {chosen}, "
        f"{result['summary']['pca_variance']:.1%} phương sai, "
        f"{result['summary']['pca_components']} thành phần)"
    )
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.legend(title="Cụm", bbox_to_anchor=(1.02, 1), loc="upper left")
    _save(fig, "02_cluster_pca.png")

    z = result["z_profiles"][MODEL_FEATURES]
    z.index = [f"C{i}: {result['summary']['cluster_labels'][i]}" for i in z.index]
    fig, ax = plt.subplots(figsize=(10, 0.7 * len(z) + 2))
    sns.heatmap(
        z,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        cbar_kws={"label": "z-score so với trung bình toàn bộ"},
        ax=ax,
    )
    ax.set_xticklabels([FEATURE_LABELS[c] for c in z.columns], rotation=35, ha="right")
    ax.set_ylabel("")
    ax.set_title("Chân dung cụm theo z-score")
    _save(fig, "02_cluster_profiles.png")

    key = ["kills_pr", "deaths_pr", "assists_pr", "acs", "fk_pr", "acs_sd"]
    long = players.melt(
        id_vars=["cluster_label"], value_vars=key, var_name="feature", value_name="value"
    )
    long["feature"] = long["feature"].map(FEATURE_LABELS)
    fig, axes = plt.subplots(2, 3, figsize=(14, 7.5))
    for ax, feature in zip(axes.flat, long["feature"].unique()):
        sns.boxplot(
            data=long[long["feature"] == feature],
            x="cluster_label",
            y="value",
            ax=ax,
            color="#4c72b0",
        )
        ax.set_title(feature)
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    _save(fig, "02_cluster_boxplots.png")


def plot_rules(result: dict) -> None:
    pick = result["pick_rates"]
    top_agents = (
        pick.groupby("agent")["picks"].sum().sort_values(ascending=False).head(12).index
    )
    matrix = (
        pick[pick["agent"].isin(top_agents)]
        .pivot(index="agent", columns="map", values="pick_rate")
        .reindex(top_agents)
    )
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    sns.heatmap(
        matrix,
        annot=True,
        fmt=".0%",
        cmap="YlGnBu",
        cbar_kws={"label": "Tỷ lệ chọn trong đội hình"},
        ax=ax,
    )
    ax.set_title("Tỷ lệ chọn Agent theo bản đồ")
    ax.set_xlabel("")
    ax.set_ylabel("")
    _save(fig, "03_agent_pickrate_map.png")

    rules = result["rules"]
    if not rules.empty:
        fig, ax = plt.subplots(figsize=(8.5, 5.5))
        sc = ax.scatter(
            rules["support"],
            rules["confidence"],
            c=rules["lift"],
            cmap="viridis",
            s=np.clip(rules["support_count"] / 4, 12, 180),
            alpha=0.7,
            edgecolor="none",
        )
        fig.colorbar(sc, ax=ax, label="Lift")
        ax.set_xlabel("Support")
        ax.set_ylabel("Confidence")
        ax.set_title("Các luật kết hợp Agent (mỗi điểm là một luật, theo bản đồ)")
        _save(fig, "03_rules_support_confidence.png")

        top = rules.sort_values("lift", ascending=False).head(15).iloc[::-1]
        fig, ax = plt.subplots(figsize=(9.5, 0.4 * len(top) + 2))
        ax.barh(top["rule"] + "  [" + top["map"] + "]", top["lift"], color="#4c72b0")
        ax.axvline(1, color="black", linewidth=0.8)
        ax.set_xlabel("Lift")
        ax.set_title("15 luật có lift cao nhất")
        _save(fig, "03_rules_top_lift.png")

    comps = result["compositions"]
    if not comps.empty:
        top = comps.sort_values(["n", "win_rate"], ascending=False).head(12).iloc[::-1]
        labels = [f"{r.agents_str.replace('|', ' + ')}  ({r.map}, n={r.n})" for r in top.itertuples()]
        fig, ax = plt.subplots(figsize=(10.5, 0.45 * len(top) + 2))
        colors = ["#55a868" if w >= 0.5 else "#c44e52" for w in top["win_rate"]]
        ax.barh(labels, top["win_rate"], color=colors)
        ax.axvline(0.5, color="black", linewidth=0.8, linestyle="--")
        ax.set_xlim(0, 1)
        ax.set_xlabel("Tỷ lệ thắng (khoảng tin cậy Wilson 95% trong bảng)")
        ax.set_title("Các đội hình 5 Agent xuất hiện nhiều nhất")
        _save(fig, "03_compositions_winrate.png")


def plot_composition_volume(comps: pd.DataFrame) -> None:
    counts = comps.groupby(["Map", "agents_str"]).size().reset_index(name="n")
    g = counts.groupby("Map")["n"].agg(["count", "max", "median"]).sort_values("count")
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    g["count"].plot.barh(ax=ax, color="#8172b2")
    ax.set_xlabel("Số đội hình 5 Agent khác nhau")
    ax.set_ylabel("")
    ax.set_title("Độ đa dạng đội hình theo bản đồ")
    _save(fig, "03_composition_diversity.png")
