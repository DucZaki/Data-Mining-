#!/usr/bin/env python
"""Build the Vietnamese presentation deck from the generated result tables."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

TABLES = ROOT / "outputs" / "tables"
SLIDES = ROOT / "slides"
ASSETS = SLIDES / "assets"

# ---------------------------------------------------------------------------
# Palette and typography
# ---------------------------------------------------------------------------

BG = RGBColor(247, 246, 242)
INK = RGBColor(17, 24, 39)
MUTED = RGBColor(91, 100, 112)
RED = RGBColor(255, 70, 85)
DARK_RED = RGBColor(190, 30, 45)
TEAL = RGBColor(15, 118, 110)
GOLD = RGBColor(217, 119, 6)
WHITE = RGBColor(255, 255, 255)
LINE = RGBColor(219, 216, 208)
PALE_RED = RGBColor(255, 232, 234)
PALE_TEAL = RGBColor(230, 244, 241)
PALE_GOLD = RGBColor(252, 243, 226)
DARK_BG = RGBColor(17, 24, 39)

FONT = "Arial"
MONO = "Consolas"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.unicode_minus": False,
        "axes.edgecolor": "#D9D6CE",
        "axes.labelcolor": "#111827",
        "xtick.color": "#5B6472",
        "ytick.color": "#5B6472",
        "text.color": "#111827",
    }
)


def _save(fig, name: str) -> None:
    fig.savefig(ASSETS / name, dpi=230, bbox_inches="tight", transparent=True)
    plt.close(fig)


def _short(feature: str) -> str:
    return {
        "kills_pr": "Kills/R",
        "deaths_pr": "Deaths/R",
        "assists_pr": "Assists/R",
        "kd": "K/D",
        "acs": "ACS",
        "adr": "ADR",
        "fk_pr": "First kills/R",
        "fd_pr": "First deaths/R",
        "multi_pr": "Multi-kill/R",
        "acs_sd": "SD ACS",
        "hs": "HS%",
    }.get(feature, feature)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------


def chart_correlations() -> None:
    df = pd.read_csv(TABLES / "feature_correlation_high.csv").head(8).iloc[::-1]
    labels = [f"{_short(a)}  ↔  {_short(b)}" for a, b in zip(df["feature_a"], df["feature_b"])]
    values = df["correlation"].to_numpy()

    fig, ax = plt.subplots(figsize=(6.1, 4.25))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    colors = ["#FF4655" if v >= 0.9 else "#E8A0A7" for v in values]
    ax.barh(labels, values, color=colors, height=0.62)
    for y, value in enumerate(values):
        ax.text(value + 0.012, y, f"{value:.2f}", va="center", fontsize=9.5, color="#111827")
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Hệ số tương quan |r|", fontsize=10)
    ax.tick_params(axis="y", labelsize=10)
    ax.tick_params(axis="x", labelsize=9)
    ax.grid(axis="x", color="#E5E2DA", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    _save(fig, "correlations.png")


def chart_silhouette() -> None:
    df = pd.read_csv(TABLES / "cluster_evaluation.csv")
    colors = []
    for k in df["k"]:
        if k == 3:
            colors.append("#FF4655")
        elif k == 2:
            colors.append("#D9A441")
        else:
            colors.append("#C9C5BC")

    fig, ax = plt.subplots(figsize=(6.4, 4.15))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    bars = ax.bar(df["k"], df["silhouette"], color=colors, width=0.62)
    for bar, value in zip(bars, df["silhouette"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.006,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=9.5,
            color="#111827",
            fontweight="bold" if value > 0.30 else "normal",
        )
    ax.axhline(0.278, color="#FF4655", linestyle=(0, (3, 3)), linewidth=1)
    ax.set_ylim(0.20, 0.39)
    ax.set_xticks(df["k"])
    ax.set_xlabel("Số cụm k", fontsize=10)
    ax.set_ylabel("Silhouette", fontsize=10)
    ax.tick_params(labelsize=9.5)
    ax.grid(axis="y", color="#E5E2DA", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    _save(fig, "silhouette.png")


def chart_cluster_heatmap() -> None:
    z = pd.read_csv(TABLES / "cluster_profiles_z.csv").set_index("cluster")
    cols = ["kills_pr", "deaths_pr", "assists_pr", "kd", "acs", "adr", "fk_pr"]
    labels = [_short(c) for c in cols]
    data = z.loc[[0, 1, 2], cols].to_numpy()

    fig, ax = plt.subplots(figsize=(7.6, 2.75))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    cmap = LinearSegmentedColormap.from_list("valorant_div", ["#2A9D8F", "#F7F6F2", "#FF4655"])
    im = ax.imshow(data, cmap=cmap, vmin=-1.3, vmax=1.3, aspect="auto")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = data[i, j]
            ax.text(
                j,
                i,
                f"{value:+.2f}",
                ha="center",
                va="center",
                fontsize=9,
                color="white" if abs(value) > 0.85 else "#111827",
            )
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["C0", "C1", "C2"], fontsize=11, fontweight="bold")
    ax.set_xlabel("z-score so với trung bình toàn mẫu", fontsize=9)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    _save(fig, "cluster_heatmap.png")


def chart_pick_heatmap() -> None:
    picks = pd.read_csv(TABLES / "agent_pick_rates_by_map.csv")
    agents = ["sova", "jett", "omen", "killjoy", "viper", "sage", "cypher"]
    maps = ["Ascent", "Haven", "Bind", "Split", "Icebox", "Breeze", "Fracture"]
    pivot = (
        picks.pivot_table(index="map", columns="agent", values="pick_rate", aggfunc="max")
        .reindex(index=maps, columns=agents)
        .fillna(0)
    )
    data = pivot.to_numpy() * 100

    fig, ax = plt.subplots(figsize=(12.0, 4.1))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    cmap = LinearSegmentedColormap.from_list("pick_rate", ["#F7F6F2", "#F7C6CB", "#FF4655", "#8E1B2A"])
    ax.imshow(data, cmap=cmap, vmin=0, vmax=100, aspect="auto")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = data[i, j]
            ax.text(
                j,
                i,
                f"{value:.0f}%",
                ha="center",
                va="center",
                fontsize=9.5,
                color="white" if value > 55 else "#111827",
                fontweight="bold" if value > 80 else "normal",
            )
    ax.set_xticks(range(len(agents)))
    ax.set_xticklabels([a.title() for a in agents], fontsize=10.5, fontweight="bold")
    ax.set_yticks(range(len(maps)))
    ax.set_yticklabels(maps, fontsize=10)
    ax.set_xlabel("Tỷ lệ đội hình có Agent", fontsize=9)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    _save(fig, "pick_heatmap.png")


def chart_icebox() -> None:
    comps = pd.read_csv(TABLES / "exact_compositions.csv")
    rows = [
        ("jett|killjoy|sage|sova|viper", "Killjoy–Sage–Sova–Jett–Viper"),
        ("jett|reyna|sage|sova|viper", "Reyna–Sage–Sova–Jett–Viper"),
    ]
    selected = []
    for key, label in rows:
        row = comps[(comps["map"] == "Icebox") & (comps["agents_str"] == key)].iloc[0]
        selected.append((label, row))

    fig, ax = plt.subplots(figsize=(6.35, 3.65))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    y = np.array([1, 0])
    values = np.array([float(r["win_rate"]) for _, r in selected]) * 100
    low = np.array([float(r["win_rate_ci_low"]) for _, r in selected]) * 100
    high = np.array([float(r["win_rate_ci_high"]) for _, r in selected]) * 100
    colors = ["#FF4655", "#9CA3AF"]
    ax.barh(y, values, color=colors, height=0.48)
    ax.errorbar(
        values,
        y,
        xerr=[values - low, high - values],
        fmt="none",
        ecolor="#111827",
        elinewidth=1.2,
        capsize=4,
    )
    ax.axvline(50, color="#111827", linestyle=(0, (3, 3)), linewidth=1)
    for yi, (label, row), value, hi in zip(y, selected, values, high):
        q = float(row["fisher_q_bh"])
        ax.text(
            hi + 0.6,
            yi,
            f"{value:.1f}%   q={q:.3f}",
            va="center",
            fontsize=10,
            color="#111827",
            fontweight="bold",
        )
    ax.set_yticks(y)
    ax.set_yticklabels([label for label, _ in selected], fontsize=10)
    ax.set_xlim(34, 66)
    ax.set_xlabel("Win rate (%)", fontsize=10)
    ax.tick_params(axis="x", labelsize=9)
    ax.grid(axis="x", color="#E5E2DA", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    _save(fig, "icebox_wr.png")


def chart_rules_by_map() -> None:
    rules = pd.read_csv(TABLES / "agent_rules_by_map.csv")
    counts = rules.groupby("map").size().sort_values()
    fig, ax = plt.subplots(figsize=(5.7, 3.45))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    colors = ["#FF4655" if m in {"Ascent", "Icebox"} else "#0F766E" for m in counts.index]
    bars = ax.barh(counts.index, counts.values, color=colors, height=0.62)
    for bar, value in zip(bars, counts.values):
        ax.text(value + 2, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=9.5)
    ax.set_xlim(0, max(counts.values) + 18)
    ax.set_xlabel("Số luật", fontsize=10)
    ax.tick_params(labelsize=9.5)
    ax.grid(axis="x", color="#E5E2DA", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    _save(fig, "rules_by_map.png")


# ---------------------------------------------------------------------------
# PowerPoint helpers
# ---------------------------------------------------------------------------


def _set_bg(slide, color: RGBColor) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _rect(slide, left, top, width, height, fill, line=None, radius=None, shape=MSO_SHAPE.RECTANGLE):
    shape_obj = slide.shapes.add_shape(shape, Inches(left), Inches(top), Inches(width), Inches(height))
    shape_obj.fill.solid()
    shape_obj.fill.fore_color.rgb = fill
    shape_obj.line.fill.background()
    if line is not None:
        shape_obj.line.color.rgb = line
        shape_obj.line.width = Pt(0.75)
    if radius is not None and shape_obj.adjustments:
        shape_obj.adjustments[0] = radius
    shape_obj.shadow.inherit = False
    return shape_obj


def _text(
    slide,
    text,
    left,
    top,
    width,
    height,
    size=16,
    bold=False,
    color=INK,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    font=FONT,
    line_spacing=1.0,
    margin=0.0,
):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.line_spacing = line_spacing
    p.font.name = font
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    return box


def _paras(
    slide,
    lines,
    left,
    top,
    width,
    height,
    size=16,
    color=INK,
    bold=False,
    space_after=4,
    line_spacing=1.0,
    align=PP_ALIGN.LEFT,
    font=FONT,
):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for index, line in enumerate(lines):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        p.font.name = font
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = color
    return box


def _bullets(slide, items, left, top, width, height, size=14, color=INK, bullet_color=RED, space_after=8, line_spacing=1.02):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for index, item in enumerate(items):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        r1 = p.add_run()
        r1.text = "•  "
        r1.font.name = FONT
        r1.font.size = Pt(size)
        r1.font.bold = True
        r1.font.color.rgb = bullet_color
        r2 = p.add_run()
        r2.text = item
        r2.font.name = FONT
        r2.font.size = Pt(size)
        r2.font.color.rgb = color
    return box


def _header(slide, index: int, kicker: str, title: str, subtitle: str | None = None) -> None:
    _set_bg(slide, BG)
    _text(slide, kicker.upper(), 0.6, 0.30, 9.5, 0.28, size=9.5, bold=True, color=RED)
    _text(slide, title, 0.6, 0.61, 12.1, 0.7, size=27, bold=True, color=INK)
    _rect(slide, 0.6, 1.33, 0.95, 0.045, RED)
    if subtitle:
        _text(slide, subtitle, 0.6, 1.44, 11.9, 0.35, size=12.5, color=MUTED)
    _text(
        slide,
        "Valorant Data Mining  ·  Đồ án khai phá dữ liệu",
        0.6,
        7.12,
        8.5,
        0.2,
        size=8,
        color=MUTED,
    )
    _text(slide, f"{index:02d}", 12.2, 7.12, 0.55, 0.2, size=8, color=MUTED, align=PP_ALIGN.RIGHT)


def _card(slide, left, top, width, height, fill=WHITE, line=LINE, radius=0.08):
    return _rect(slide, left, top, width, height, fill, line=line, radius=radius, shape=MSO_SHAPE.ROUNDED_RECTANGLE)


def _kpi(slide, left, top, width, height, value, label, accent=RED, fill=WHITE):
    _card(slide, left, top, width, height, fill=fill, line=LINE)
    _rect(slide, left, top, 0.06, height, accent)
    _text(slide, value, left + 0.18, top + 0.12, width - 0.3, 0.45, size=23, bold=True, color=accent)
    _text(slide, label, left + 0.18, top + 0.60, width - 0.3, 0.35, size=9.5, color=MUTED)


def _table(slide, data, left, top, width, height, col_widths=None, font_size=11, header_fill=INK, first_col_bold=False):
    rows, cols = len(data), len(data[0])
    table_shape = slide.shapes.add_table(rows, cols, Inches(left), Inches(top), Inches(width), Inches(height))
    table = table_shape.table
    table.first_row = True
    table.horz_banding = False
    if col_widths:
        for index, col_width in enumerate(col_widths):
            table.columns[index].width = Inches(col_width)
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = header_fill
            else:
                cell.fill.fore_color.rgb = WHITE if r % 2 else RGBColor(251, 250, 247)
            tf = cell.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            p.text = str(data[r][c])
            p.font.name = FONT
            p.font.size = Pt(font_size)
            p.font.bold = (r == 0) or (first_col_bold and c == 0)
            p.font.color.rgb = WHITE if r == 0 else INK
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
    return table


def _notes(slide, text: str) -> None:
    slide.notes_slide.notes_text_frame.text = text


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------


def build_deck() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    SLIDES.mkdir(parents=True, exist_ok=True)

    chart_correlations()
    chart_silhouette()
    chart_cluster_heatmap()
    chart_pick_heatmap()
    chart_icebox()
    chart_rules_by_map()

    summary = pd.read_csv(TABLES / "clustering_summary.csv")
    summary = summary.set_index(summary.columns[0])[summary.columns[1]]
    profiles = pd.read_csv(TABLES / "cluster_profiles_raw.csv").set_index("cluster")
    rules_summary = pd.read_csv(TABLES / "agent_rules_summary.csv").set_index("metric")["value"]
    comps = pd.read_csv(TABLES / "exact_compositions.csv")
    comp_highlights = pd.read_csv(TABLES / "composition_highlights.csv")
    rules = pd.read_csv(TABLES / "agent_rules_by_map.csv")

    n_players = int(float(summary["n_players"]))
    silhouette = float(summary["silhouette"])
    best_sil = float(summary["best_silhouette"])
    stability = float(summary["stability_mean_ari"])
    ward_ari = float(summary["ward_ari"])
    pca_variance = float(summary["pca_variance"])
    n_rules = int(float(rules_summary["rules"]))
    n_fdr_rules = int(float(rules_summary["rules_fdr_significant"]))
    n_tested = int(float(rules_summary["compositions_tested"]))
    n_fdr_comps = int(float(rules_summary["compositions_fdr_significant"]))
    n_raw_sig = int((comps["fisher_p_value"] < 0.05).sum())

    c0, c1, c2 = profiles.loc[0], profiles.loc[1], profiles.loc[2]

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    prs.core_properties.title = "Phân cụm người chơi Valorant và khai phá tổ hợp Agent"
    prs.core_properties.subject = "Đồ án khai phá dữ liệu"
    prs.core_properties.author = ""
    prs.core_properties.last_modified_by = ""
    prs.core_properties.comments = ""
    prs.core_properties.created = datetime(2026, 10, 23, 0, 0, 0)
    prs.core_properties.modified = datetime(2026, 10, 23, 0, 0, 0)

    # 1. Title -----------------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _set_bg(slide, DARK_BG)
    _rect(slide, 0, 0, 0.18, 7.5, RED)
    _rect(slide, 0.95, 1.25, 0.55, 0.055, RED)
    _text(slide, "ĐỒ ÁN KHAI PHÁ DỮ LIỆU  ·  2026", 0.95, 0.92, 7.0, 0.28, size=11, bold=True, color=RED)
    _paras(
        slide,
        ["Phân cụm người chơi Valorant", "và khai phá tổ hợp Agent"],
        0.95,
        1.62,
        8.7,
        1.7,
        size=38,
        bold=True,
        color=WHITE,
        space_after=0,
        line_spacing=1.02,
    )
    _text(
        slide,
        "Từ 14.005 ván đấu chuyên nghiệp đến các kết luận có kiểm định",
        0.97,
        3.55,
        7.6,
        0.45,
        size=16,
        color=RGBColor(190, 196, 205),
    )
    _text(
        slide,
        "Sinh viên thực hiện: ........................................",
        0.97,
        6.45,
        6.3,
        0.3,
        size=11,
        color=RGBColor(190, 196, 205),
    )
    _text(
        slide,
        "GVHD: ........................................",
        0.97,
        6.78,
        6.3,
        0.3,
        size=11,
        color=RGBColor(190, 196, 205),
    )
    _card(slide, 9.35, 1.55, 3.25, 1.28, fill=RGBColor(28, 37, 52), line=RGBColor(55, 65, 81))
    _text(slide, "14.005", 9.55, 1.68, 2.7, 0.48, size=27, bold=True, color=RED)
    _text(slide, "ván sạch / 15.888 ván gốc", 9.55, 2.22, 2.7, 0.28, size=9.5, color=RGBColor(190, 196, 205))
    _card(slide, 9.35, 2.98, 3.25, 1.28, fill=RGBColor(28, 37, 52), line=RGBColor(55, 65, 81))
    _text(slide, "2.599", 9.55, 3.11, 2.7, 0.48, size=27, bold=True, color=WHITE)
    _text(slide, "người chơi đủ điều kiện", 9.55, 3.65, 2.7, 0.28, size=9.5, color=RGBColor(190, 196, 205))
    _card(slide, 9.35, 4.41, 3.25, 1.28, fill=RGBColor(28, 37, 52), line=RGBColor(55, 65, 81))
    _text(slide, "580", 9.55, 4.54, 2.7, 0.48, size=27, bold=True, color=RGBColor(94, 234, 212))
    _text(slide, "luật kết hợp trên 7 bản đồ", 9.55, 5.08, 2.7, 0.28, size=9.5, color=RGBColor(190, 196, 205))
    _text(
        slide,
        "K-Means / PCA  ·  FP-Growth  ·  Fisher exact + Benjamini–Hochberg",
        0.97,
        5.55,
        7.8,
        0.3,
        size=10.5,
        color=RGBColor(148, 163, 184),
    )
    _notes(
        slide,
        "Chào thầy cô và các bạn. Đồ án gồm hai bài toán: phân cụm người chơi theo phong cách thi đấu và khai phá các tổ hợp Agent theo bản đồ. Điểm mình muốn nhấn mạnh là kết quả không dừng ở mô tả: có kiểm định thống kê, hiệu chỉnh đa so sánh và toàn bộ pipeline có thể chạy lại bằng make all.",
    )

    # 2. Problem ---------------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 2, "01 · Bài toán", "Bốn câu hỏi, hai bài toán khai phá", "Từ hành vi cá nhân đến cấu trúc đội hình trong dữ liệu thi đấu chuyên nghiệp.")
    questions = [
        ("01", "Có những nhóm người chơi nào?", "Dựa trên hạ gục, hỗ trợ, mở giao tranh và độ ổn định."),
        ("02", "Agent nào thường đi cùng nhau?", "Đồng xuất hiện theo từng bản đồ, không gộp toàn bộ meta."),
        ("03", "Tổ hợp phổ biến có thắng nhiều hơn?", "So sánh win rate với phần còn lại của cùng map."),
        ("04", "Kết quả khác nhau theo map/patch?", "Kiểm tra tính ổn định của meta theo thời gian."),
    ]
    positions = [(0.6, 1.62), (6.55, 1.62), (0.6, 3.42), (6.55, 3.42)]
    for (number, title, body), (left, top) in zip(questions, positions):
        _card(slide, left, top, 5.75, 1.62, fill=WHITE, line=LINE)
        _text(slide, number, left + 0.22, top + 0.18, 0.5, 0.3, size=13, bold=True, color=RED)
        _text(slide, title, left + 0.72, top + 0.17, 4.8, 0.34, size=14.5, bold=True, color=INK)
        _text(slide, body, left + 0.72, top + 0.60, 4.75, 0.62, size=10.5, color=MUTED)
    _rect(slide, 0.6, 5.38, 12.13, 0.82, INK, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    _text(slide, "Phạm vi", 0.8, 5.57, 1.1, 0.25, size=9.5, bold=True, color=RGBColor(148, 163, 184))
    _text(
        slide,
        "14.005 ván  ·  7 bản đồ  ·  28.010 đội hình  ·  2.599 người chơi",
        1.75,
        5.54,
        10.6,
        0.3,
        size=15,
        bold=True,
        color=WHITE,
    )
    _text(
        slide,
        "Không dừng ở mô tả: kiểm định Fisher, hiệu chỉnh FDR và pipeline tái lập bằng một lệnh.",
        0.6,
        6.45,
        12.1,
        0.3,
        size=10.5,
        color=MUTED,
    )
    _notes(
        slide,
        "Bốn câu hỏi tương ứng hai bài toán. Bài toán 1 là phân cụm người chơi; bài toán 2 là luật kết hợp Agent theo map. Câu hỏi 3 là phần kiểm định hiệu quả đội hình. Phạm vi gồm 14.005 ván sạch, 7 map, 28.010 đội hình và 2.599 người chơi đủ điều kiện.",
    )

    # 3. Data cleaning ---------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 3, "02 · Dữ liệu", "Làm sạch để mỗi dòng đều dùng được", "Mỗi đội phải đủ 5 người, 5 Agent khác nhau và mỗi ván phải có đúng 2 đội.")
    kpis = [
        ("15.888", "ván gốc", MUTED),
        ("14.005", "ván sạch (88,1%)", RED),
        ("28.010", "đội hình 5 Agent", TEAL),
        ("27.382", "đội hình có nhãn thắng/thua", GOLD),
    ]
    for index, (value, label, accent) in enumerate(kpis):
        left = 0.6 + (index % 2) * 3.0
        top = 1.72 + (index // 2) * 1.38
        _kpi(slide, left, top, 2.78, 1.18, value, label, accent=accent)
    _text(slide, "Ba quyết định làm sạch", 6.45, 1.62, 6.2, 0.3, size=12, bold=True, color=RED)
    _bullets(
        slide,
        [
            "Mỗi đội đúng 5 người và 5 Agent khác nhau; mỗi ván đúng 2 đội.",
            "Chỉ giữ ván 13–40 round; loại 4 ván 42 round.",
            "KAST thiếu 97,9% nên loại khỏi mô hình, không fill bằng 0.",
            "ACS/ADR/HS% lấy trung bình theo round; loại người chơi có độ phủ <80%.",
        ],
        6.45,
        2.05,
        6.0,
        2.9,
        size=12.5,
        space_after=10,
    )
    _card(slide, 6.45, 5.35, 6.05, 0.95, fill=PALE_RED, line=RGBColor(255, 205, 210))
    _text(slide, "126 người chơi bị loại", 6.65, 5.50, 2.7, 0.28, size=12, bold=True, color=DARK_RED)
    _text(slide, "vì độ phủ ADR/HS dưới 80% — không thể tính trung bình đáng tin cậy.", 6.65, 5.82, 5.6, 0.3, size=10.5, color=INK)
    _text(slide, "14.005 / 15.888 = 88,1% ván giữ lại", 0.6, 5.55, 5.3, 0.3, size=10.5, bold=True, color=MUTED)
    _notes(
        slide,
        "Điểm quan trọng là không fillna(0) cho ACS/ADR/HS. Mỗi chỉ số chỉ tính trên các ván có giá trị, theo trọng số round. Người chơi có độ phủ dưới 80% bị loại, còn 126 người. KAST thiếu gần như toàn bộ nên bị loại khỏi mô hình.",
    )

    # 4. Pipeline --------------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 4, "03 · Phương pháp", "Pipeline tái lập từ dữ liệu gốc đến kết quả", "Tất cả bước nằm trong một Makefile; kết quả cố định bằng random_state.")
    steps = [
        ("01", "SQLite", "4 bảng gốc"),
        ("02", "Audit", "kiểm tra dữ liệu"),
        ("03", "Build", "làm sạch, đội hình"),
        ("04", "Mine", "PCA + K-Means\nFP-Growth"),
        ("05", "Report", "bảng + hình"),
        ("06", "Validate", "19 kiểm tra"),
    ]
    box_w, gap, start_x = 1.76, 0.14, 0.63
    for index, (number, name, desc) in enumerate(steps):
        left = start_x + index * (box_w + gap)
        fill = RED if index in {3, 4} else WHITE
        text_color = WHITE if fill == RED else INK
        _card(slide, left, 1.78, box_w, 1.12, fill=fill, line=LINE)
        _text(slide, number, left + 0.14, 1.88, 0.4, 0.2, size=8, bold=True, color=WHITE if fill == RED else RED)
        _text(slide, name, left + 0.14, 2.08, box_w - 0.25, 0.28, size=12.5, bold=True, color=text_color)
        _paras(slide, desc.split("\n"), left + 0.14, 2.42, box_w - 0.25, 0.4, size=8.3, color=RGBColor(230, 232, 236) if fill == RED else MUTED, space_after=0, line_spacing=0.95)
        if index < len(steps) - 1:
            _rect(slide, left + box_w + 0.015, 2.22, 0.10, 0.22, RGBColor(201, 197, 188), shape=MSO_SHAPE.RIGHT_ARROW)
    _text(slide, "make all", 0.63, 3.28, 2.0, 0.35, size=18, bold=True, color=INK, font=MONO)
    _text(slide, "≈ 1–2 phút  ·  tự sinh bảng, hình và báo cáo", 2.55, 3.34, 5.6, 0.3, size=10.5, color=MUTED)
    _card(slide, 0.63, 5.82, 12.1, 0.82, fill=WHITE, line=LINE)
    _text(slide, "ĐIỂM KIỂM SOÁT", 0.83, 5.97, 1.55, 0.2, size=8.5, bold=True, color=RED)
    _text(
        slide,
        "19/19 kiểm tra đạt  ·  0 lỗi  ·  nhãn thắng khớp Games.Winner cho 27.382 đội hình",
        2.48,
        5.95,
        10.0,
        0.3,
        size=11,
        bold=True,
        color=INK,
    )
    tools = [
        ("Dữ liệu", "SQLite  ·  pandas", "Đọc, làm sạch, tổng hợp theo round"),
        ("Mô hình", "scikit-learn  ·  mlxtend", "PCA, K-Means, Ward, FP-Growth"),
        ("Kiểm định", "scipy  ·  BH", "Wilson CI, Fisher exact, FDR"),
    ]
    for index, (title, tool, desc) in enumerate(tools):
        left = 0.63 + index * 4.08
        _card(slide, left, 4.25, 3.85, 1.45, fill=WHITE, line=LINE)
        _text(slide, title.upper(), left + 0.18, 4.40, 3.4, 0.2, size=8.5, bold=True, color=RED)
        _text(slide, tool, left + 0.18, 4.70, 3.45, 0.3, size=13, bold=True, color=INK)
        _text(slide, desc, left + 0.18, 5.08, 3.45, 0.35, size=9.5, color=MUTED)
    _notes(
        slide,
        "Pipeline gồm 6 bước. Bước 3 và 4 là phần khai phá chính. Toàn bộ chạy bằng make all, khoảng 1-2 phút. Các bước report và validate sinh báo cáo cùng 19 kiểm tra bất biến.",
    )

    # 5. PCA -------------------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 5, "04 · Phân cụm", "Đa cộng tuyến: PCA trước K-Means", "Các chỉ số combat chồng lấn rất mạnh; PCA giảm việc đếm lặp “hiệu quả combat”.")
    slide.shapes.add_picture(str(ASSETS / "correlations.png"), Inches(0.55), Inches(1.62), width=Inches(5.9))
    _text(slide, "Tương quan |r| ≥ 0,70", 0.62, 5.75, 4.0, 0.28, size=10, bold=True, color=RED)
    _text(slide, "Kills, ACS, ADR, multi-kill và K/D gần như cùng một khối thông tin.", 0.62, 6.02, 5.7, 0.55, size=10, color=MUTED)
    _card(slide, 6.75, 1.62, 5.95, 1.15, fill=PALE_TEAL, line=RGBColor(190, 225, 218))
    _text(slide, f"PCA giữ {pca_variance:.1%} phương sai", 6.95, 1.77, 5.4, 0.32, size=16, bold=True, color=TEAL)
    _text(slide, "3 thành phần thay cho 11 biến; chân dung cụm vẫn mô tả bằng biến gốc.", 6.95, 2.16, 5.4, 0.3, size=10, color=INK)
    _text(slide, "Độ nhạy của kết quả", 6.75, 3.02, 5.6, 0.3, size=11, bold=True, color=INK)
    sens = pd.read_csv(TABLES / "clustering_sensitivity.csv")
    data = [["Phương pháp", "Chiều", "Silhouette", "ARI"]]
    for _, row in sens.iterrows():
        data.append([row["method"], str(int(row["n_features"])), f"{row['silhouette']:.3f}", f"{row['ari_vs_primary']:.3f}"])
    _table(slide, data, 6.75, 3.38, 5.85, 1.55, col_widths=[2.55, 0.8, 1.25, 1.25], font_size=10)
    _text(slide, "PCA gần với 11 biến gốc (ARI 0,968), nhưng 7 biến rút gọn đổi cụm nhiều (ARI 0,473).", 6.75, 5.18, 5.8, 0.55, size=10.5, color=MUTED)
    _rect(slide, 6.75, 5.90, 5.85, 0.04, LINE)
    _text(slide, "Kết quả không phải cấu trúc duy nhất → trình bày như mô tả khám phá.", 6.75, 6.03, 5.85, 0.5, size=10.5, bold=True, color=DARK_RED)
    _notes(
        slide,
        "Các biến combat tương quan rất mạnh, ví dụ Kills/R với ACS là 0,97. Nếu đưa thẳng vào K-Means, mô hình sẽ đếm hiệu quả combat nhiều lần. PCA giữ 82,1% phương sai với 3 thành phần. Bảng độ nhạy cho thấy PCA gần với 11 biến gốc nhưng bộ 7 biến rút gọn thay đổi nhiều, nên kết quả không phải duy nhất.",
    )

    # 6. Choose k --------------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 6, "05 · Phân cụm", "Vì sao chọn k = 3?", "Silhouette cao nhất ở k = 2, nhưng k = 3 nằm trong khung 3–5 cụm và dễ diễn giải.")
    slide.shapes.add_picture(str(ASSETS / "silhouette.png"), Inches(0.55), Inches(1.62), width=Inches(6.3))
    _kpi(slide, 7.15, 1.65, 2.75, 1.05, f"{silhouette:.3f}", "silhouette tại k = 3", accent=RED)
    _kpi(slide, 10.05, 1.65, 2.65, 1.05, f"{best_sil:.3f}", "silhouette cao nhất (k = 2)", accent=GOLD)
    _kpi(slide, 7.15, 2.88, 2.75, 1.05, f"{stability:.3f}", "bootstrap ARI", accent=TEAL)
    _kpi(slide, 10.05, 2.88, 2.65, 1.05, f"{ward_ari:.3f}", "Ward ARI", accent=MUTED)
    _text(slide, "Cách đọc", 7.15, 4.18, 5.5, 0.3, size=11, bold=True, color=INK)
    _bullets(
        slide,
        [
            "k = 3 tách được ba kiểu hồ sơ khác nhau, không chỉ hai nhóm quá rộng.",
            f"Silhouette {silhouette:.3f} là mức trung bình — không phải tách cụm mạnh.",
            f"Bootstrap ổn định ({stability:.3f}), nhưng Ward chỉ đồng thuận một phần ({ward_ari:.3f}).",
        ],
        7.15,
        4.50,
        5.55,
        1.85,
        size=10.5,
        space_after=7,
    )
    _card(slide, 7.15, 6.15, 5.55, 0.55, fill=PALE_RED, line=RGBColor(255, 205, 210))
    _text(slide, "Đây là lựa chọn khám phá có chủ đích, không phải k tối ưu tuyệt đối.", 7.32, 6.27, 5.2, 0.3, size=10, bold=True, color=DARK_RED)
    _notes(
        slide,
        "Silhouette cao nhất ở k=2 là 0,358. Trong khoảng 3-5, k=3 có silhouette 0,278. Nhóm chọn k=3 vì mục tiêu của đề tài là 3-5 cụm và ba chân dung diễn giải được. Bootstrap ARI 0,954 nhưng Ward ARI chỉ 0,354, nên không nên nói cụm rất ổn định.",
    )

    # 7. Cluster profiles ------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 7, "06 · Phân cụm", "Ba chân dung người chơi", "Tên cụm là mô tả theo z-score, không phải vai trò chính thức trong game.")
    cards = [
        ("C0", "Mở giao tranh · Sát thương cao", c0, RED, PALE_RED),
        ("C1", "Chết nhiều · Hiệu quả thấp", c1, MUTED, WHITE),
        ("C2", "Ít chết · Hiệu quả cao", c2, TEAL, PALE_TEAL),
    ]
    for index, (name, label, row, accent, fill) in enumerate(cards):
        left = 0.6 + index * 4.08
        _card(slide, left, 1.82, 3.85, 1.78, fill=fill, line=LINE)
        _text(slide, name, left + 0.18, 1.94, 0.45, 0.25, size=10, bold=True, color=accent)
        _text(slide, label, left + 0.58, 1.92, 3.05, 0.45, size=11.5, bold=True, color=INK)
        _text(slide, f"{int(row['n_players'])} người", left + 0.18, 2.43, 1.35, 0.25, size=9.5, color=MUTED)
        _text(slide, f"Win {row['win_rate']:.1%}", left + 2.55, 2.43, 1.1, 0.25, size=9.5, bold=True, color=accent, align=PP_ALIGN.RIGHT)
        if name == "C0":
            stat = f"ACS {row['acs']:.0f}  ·  FK/R {row['fk_pr']:.3f}  ·  K/D {row['kd']:.2f}"
        elif name == "C1":
            stat = f"ACS {row['acs']:.0f}  ·  Deaths/R {row['deaths_pr']:.3f}  ·  K/D {row['kd']:.2f}"
        else:
            stat = f"Assists/R {row['assists_pr']:.3f}  ·  K/D {row['kd']:.2f}  ·  Deaths/R {row['deaths_pr']:.3f}"
        _text(slide, stat, left + 0.18, 2.82, 3.45, 0.35, size=9.2, color=INK)
    slide.shapes.add_picture(str(ASSETS / "cluster_heatmap.png"), Inches(0.55), Inches(3.78), width=Inches(8.2))
    _card(slide, 9.0, 3.85, 3.72, 2.28, fill=WHITE, line=LINE)
    _text(slide, "Cảnh báo diễn giải", 9.2, 4.00, 3.2, 0.28, size=11, bold=True, color=RED)
    _paras(
        slide,
        [
            f"C0 dùng Duelist ở {c0['role_duelist_share']:.0%} số ván.",
            "Cụm phản ánh cả vai trò Agent lẫn phong cách.",
            "Không nên gọi C0 là “Duelist” hay C2 là “IGL”.",
        ],
        9.2,
        4.38,
        3.3,
        1.35,
        size=9.6,
        color=INK,
        space_after=7,
    )
    _notes(
        slide,
        "Ba cụm có kích thước 760, 849 và 990 người. C0 mạnh về first kill, ACS, kill và multi-kill nhưng assists thấp. C1 thấp toàn diện và chết nhiều. C2 ít chết, assists và K/D cao. C0 dùng Duelist 69% số ván, nên phải nói rõ cụm phản ánh cả role, không chỉ phong cách.",
    )

    # 8. Reliability -----------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 8, "07 · Phân cụm", "Cụm có đáng tin không?", "Ổn định khi lấy mẫu lại, nhưng không ổn định hoàn toàn khi đổi thuật toán hoặc tập biến.")
    reliability = [
        (f"{silhouette:.3f}", "Silhouette", "tách cụm trung bình", RED),
        (f"{stability:.3f}", "Bootstrap ARI", "ổn định khi lấy mẫu lại", TEAL),
        (f"{ward_ari:.3f}", "Ward ARI", "khác thuật toán", GOLD),
        ("0.473", "ARI — 7 biến", "khác tập biến", MUTED),
    ]
    for index, (value, label, desc, accent) in enumerate(reliability):
        left = 0.6 + index * 3.03
        _kpi(slide, left, 1.62, 2.85, 1.22, value, label, accent=accent)
        _text(slide, desc, left + 0.18, 2.56, 2.55, 0.22, size=8.8, color=MUTED)
    _card(slide, 0.6, 3.15, 5.9, 2.25, fill=PALE_TEAL, line=RGBColor(190, 225, 218))
    _text(slide, "Ổn định khi…", 0.82, 3.32, 4.8, 0.3, size=13, bold=True, color=TEAL)
    _bullets(slide, ["lấy mẫu lại 80% người chơi", "giữ nguyên không gian PCA", "dùng cùng K-Means và cùng k"], 0.82, 3.72, 5.25, 1.45, size=11, bullet_color=TEAL, space_after=7)
    _card(slide, 6.75, 3.15, 5.95, 2.25, fill=PALE_RED, line=RGBColor(255, 205, 210))
    _text(slide, "Không ổn định khi…", 6.97, 3.32, 4.8, 0.3, size=13, bold=True, color=DARK_RED)
    _bullets(slide, ["đổi sang Ward", "bỏ bớt biến → ARI 0,473", "diễn giải như vai trò cố định"], 6.97, 3.72, 5.35, 1.45, size=11, bullet_color=DARK_RED, space_after=7)
    _rect(slide, 0.6, 5.70, 12.1, 0.04, LINE)
    _text(slide, "Kết luận: ba cụm là mô tả khám phá có ích, không phải chân lý về người chơi.", 0.6, 5.88, 12.1, 0.4, size=13, bold=True, color=INK)
    _notes(
        slide,
        "Cần tách hai loại độ tin cậy. Bootstrap ARI 0,954 cho thấy cụm ổn định khi lấy mẫu lại. Nhưng Ward ARI 0,354 và ARI 0,473 khi dùng 7 biến cho thấy kết quả phụ thuộc thuật toán và tập biến. Vì vậy chỉ nên xem đây là mô tả khám phá.",
    )

    # 9. Rules method ----------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 9, "08 · Luật kết hợp", "FP-Growth: tìm cấu trúc trong 28.010 đội hình", "Mỗi đội là một giỏ 5 Agent; chạy riêng từng bản đồ để không trộn meta.")
    _text(slide, "Cách chạy", 0.62, 1.82, 5.5, 0.3, size=11, bold=True, color=RED)
    _bullets(
        slide,
        [
            "Mỗi đội trong một ván = một giỏ 5 Agent, không thứ tự.",
            "FP-Growth, tối đa 3 Agent trong một itemset.",
            "Support ≥ max(12 đội, 2%) cho mỗi map.",
            "Confidence ≥ 0,40 và lift ≥ 1,05.",
        ],
        0.62,
        2.16,
        5.65,
        2.3,
        size=11.2,
        space_after=9,
    )
    _text(slide, f"{n_rules} luật trên 7 bản đồ", 0.62, 4.42, 5.6, 0.4, size=20, bold=True, color=INK)
    _text(slide, "Bảng báo cáo lọc thêm n ≥ 30 và confidence ≥ 0,5.", 0.62, 4.80, 5.4, 0.3, size=10, color=MUTED)
    slide.shapes.add_picture(str(ASSETS / "rules_by_map.png"), Inches(6.55), Inches(1.55), width=Inches(6.1))
    definitions = [
        ("Support", "Tỷ lệ đội hình chứa toàn bộ vế trái + phải."),
        ("Confidence", "Xác suất có vế phải khi đã có vế trái."),
        ("Lift", "> 1: xuất hiện cùng nhau nhiều hơn kỳ vọng độc lập."),
    ]
    for index, (title, desc) in enumerate(definitions):
        left = 0.62 + index * 4.08
        _card(slide, left, 5.50, 3.85, 1.05, fill=WHITE, line=LINE)
        _text(slide, title, left + 0.15, 5.62, 3.4, 0.24, size=9.5, bold=True, color=TEAL)
        _text(slide, desc, left + 0.15, 5.90, 3.5, 0.5, size=9.2, color=MUTED)
    _notes(
        slide,
        "Luật kết hợp chạy riêng từng map. Mỗi đội là một giỏ 5 Agent. FP-Growth tìm itemset, sau đó sinh luật với confidence và lift. Có 580 luật. Cần nhấn mạnh support/confidence/lift chỉ đo đồng xuất hiện.",
    )

    # 10. Meta by map ----------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 10, "09 · Kết quả", "Meta Agent rất rõ theo từng bản đồ", "Tỷ lệ đội hình có Agent; các map nhỏ như Breeze/Fracture cần đọc thận trọng.")
    slide.shapes.add_picture(str(ASSETS / "pick_heatmap.png"), Inches(0.5), Inches(1.55), width=Inches(12.35))
    _text(slide, "Đọc nhanh", 0.62, 6.18, 3.0, 0.28, size=10, bold=True, color=RED)
    _text(
        slide,
        "Ascent: Sova 96% · Jett 79%     |     Icebox: Sova 91% · Jett 91% · Sage 85% · Viper 82%",
        1.55,
        6.15,
        10.9,
        0.3,
        size=10.5,
        color=INK,
    )
    _text(
        slide,
        "Cấu trúc này là đầu vào cho luật kết hợp, không phải bằng chứng hiệu quả.",
        0.62,
        6.48,
        11.8,
        0.3,
        size=9.5,
        color=MUTED,
    )
    _notes(
        slide,
        "Heatmap cho thấy meta rất khác nhau theo map. Ascent gần như luôn có Sova và Jett; Icebox gần như cố định Sova, Jett, Sage, Viper. Đây là tỷ lệ chọn, chưa nói gì về thắng thua.",
    )

    # 11. Icebox ---------------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 11, "10 · Hiệu quả", "Cùng map, khác một Agent: kết quả có khác?", "Hai đội hình Icebox phổ biến nhất chỉ khác Reyna/Killjoy.")
    slide.shapes.add_picture(str(ASSETS / "icebox_wr.png"), Inches(0.5), Inches(1.75), width=Inches(6.6))
    kill = comps[(comps["map"] == "Icebox") & (comps["agents_str"] == "jett|killjoy|sage|sova|viper")].iloc[0]
    reyna = comps[(comps["map"] == "Icebox") & (comps["agents_str"] == "jett|reyna|sage|sova|viper")].iloc[0]
    _kpi(slide, 7.35, 1.72, 2.55, 1.0, f"{kill['win_rate']:.1%}", "Killjoy  ·  q = 0,024", accent=RED)
    _kpi(slide, 10.1, 1.72, 2.55, 1.0, f"{reyna['win_rate']:.1%}", "Reyna  ·  q = 0,510", accent=MUTED)
    _text(slide, "Chênh lệch quan sát", 7.35, 2.98, 3.0, 0.25, size=9.5, bold=True, color=MUTED)
    _text(slide, "+9,4 điểm phần trăm", 7.35, 3.25, 4.5, 0.4, size=21, bold=True, color=INK)
    _text(slide, "n = 883", 7.35, 3.78, 1.0, 0.25, size=9, color=MUTED)
    _text(slide, "n = 896", 10.1, 3.78, 1.0, 0.25, size=9, color=MUTED)
    _card(slide, 7.35, 4.35, 5.3, 1.55, fill=PALE_RED, line=RGBColor(255, 205, 210))
    _text(slide, "Cách diễn giải", 7.53, 4.50, 4.8, 0.25, size=9.5, bold=True, color=DARK_RED)
    _paras(
        slide,
        [
            "Chỉ đội hình Killjoy còn khác biệt sau FDR.",
            "Đây là quan hệ quan sát, chưa kiểm soát chất lượng đội và patch.",
            "Không thể kết luận “Killjoy mạnh hơn Reyna”.",
        ],
        7.53,
        4.82,
        4.9,
        0.95,
        size=9.5,
        color=INK,
        space_after=4,
    )
    _card(slide, 0.6, 5.48, 6.55, 0.95, fill=WHITE, line=LINE)
    _text(slide, "Khoảng tin cậy 95% (Wilson)", 0.8, 5.62, 3.8, 0.22, size=9, bold=True, color=TEAL)
    _text(
        slide,
        f"Killjoy  {kill['win_rate_ci_low']:.1%}–{kill['win_rate_ci_high']:.1%}     ·     Reyna  {reyna['win_rate_ci_low']:.1%}–{reyna['win_rate_ci_high']:.1%}",
        0.8,
        5.92,
        6.1,
        0.3,
        size=12,
        bold=True,
        color=INK,
    )
    _text(slide, "Cùng 4 Agent: Jett–Sage–Sova–Viper", 0.62, 6.62, 5.8, 0.3, size=10.5, bold=True, color=MUTED)
    _notes(
        slide,
        "Đây là ví dụ dễ thấy nhất trên Icebox. Hai đội hình chỉ khác Reyna và Killjoy. Killjoy đạt 55,9%, Reyna 46,5%, chênh 9,4 điểm. Nhưng chỉ Killjoy còn q=0,024 sau FDR; Reyna q=0,510. Vẫn là quan hệ quan sát, không phải nhân quả.",
    )

    # 12. FDR ------------------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 12, "11 · Kiểm định", "Đa số khác biệt biến mất sau FDR", "So sánh từng đội hình với phần còn lại của cùng map, rồi hiệu chỉnh Benjamini–Hochberg.")
    stats = [
        (str(n_tested), "đội hình được kiểm định", INK),
        (str(n_raw_sig), "có p < 0,05 (chưa hiệu chỉnh)", GOLD),
        (str(n_fdr_comps), "còn q < 0,05 sau BH", RED),
        (f"{n_fdr_rules}/{n_rules}", "luật còn q < 0,05", TEAL),
    ]
    for index, (value, label, accent) in enumerate(stats):
        left = 0.6 + index * 3.03
        _kpi(slide, left, 1.62, 2.85, 1.18, value, label, accent=accent)
    top = comp_highlights[comp_highlights["significant_fdr"]].head(3)
    table_data = [["Map", "Đội hình", "n", "Win rate", "q (BH)"]]
    for _, row in top.iterrows():
        table_data.append(
            [
                row["map"],
                row["agents_str"].replace("|", " + "),
                str(int(row["n"])),
                f"{row['win_rate']:.1%}",
                f"{row['fisher_q_bh']:.3f}",
            ]
        )
    _table(slide, table_data, 0.6, 3.28, 12.1, 1.55, col_widths=[1.3, 6.6, 1.0, 1.5, 1.3], font_size=10.5)
    _text(slide, "Ba đội hình còn khác biệt sau hiệu chỉnh", 0.6, 5.05, 6.0, 0.3, size=10.5, bold=True, color=RED)
    _text(
        slide,
        "Các luật có vế trái trùng nhau rất nhiều, nên 17/580 không phải 17 phát hiện độc lập. Kết quả vẫn là khám phá, chưa có hold-out theo thời gian.",
        0.6,
        5.45,
        12.1,
        0.7,
        size=11,
        color=MUTED,
    )
    _rect(slide, 0.6, 6.35, 12.1, 0.04, LINE)
    _text(slide, "Đồng xuất hiện  ≠  hiệu quả", 0.6, 6.50, 12.1, 0.35, size=15, bold=True, color=INK)
    _notes(
        slide,
        "Có 473 đội hình đủ mẫu, 26 có p nhỏ hơn 0,05 nhưng chỉ 3 còn q nhỏ hơn 0,05 sau BH. Với luật, 17/580 còn significant. Con số 17 không phải 17 phát hiện độc lập vì các luật trùng antecedent. Thông điệp: đa số khác biệt win rate không bền.",
    )

    # 13. Answers --------------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 13, "12 · Kết luận", "Trả lời bốn câu hỏi nghiên cứu", "Kết quả có ích để mô tả dữ liệu, nhưng cần đọc cùng giới hạn.")
    answers = [
        ["Câu hỏi", "Trả lời", "Bằng chứng"],
        ["Nhóm người chơi?", "3 nhóm: mở giao tranh, chết nhiều, ít chết/hiệu quả.", "k=3; silhouette 0,278"],
        ["Agent đi cùng nhau?", "Meta rõ theo map, ví dụ Icebox Viper–Sage–Sova.", "580 luật; heatmap"],
        ["Tổ hợp phổ biến thắng nhiều?", "Không có bằng chứng mạnh; đa số không bền sau FDR.", "3/473 đội hình"],
        ["Khác theo map/patch?", "Có; tỷ lệ chọn Agent thay đổi theo map và patch.", "Bảng pick rate"],
    ]
    _table(slide, answers, 0.6, 1.65, 12.1, 3.2, col_widths=[3.2, 6.2, 2.7], font_size=11)
    _card(slide, 0.6, 5.15, 12.1, 1.05, fill=INK, line=INK)
    _text(slide, "Thông điệp chính", 0.82, 5.30, 2.0, 0.25, size=9, bold=True, color=RGBColor(148, 163, 184))
    _text(slide, "Meta Agent rất rõ, nhưng meta không đồng nghĩa với hiệu quả.", 0.82, 5.58, 11.4, 0.35, size=17, bold=True, color=WHITE)
    _text(slide, "Cần kiểm định trên hold-out và kiểm soát chất lượng đội trước khi kết luận nhân quả.", 0.6, 6.45, 12.0, 0.3, size=10, color=MUTED)
    _notes(
        slide,
        "Tóm lại bốn câu trả lời. Có ba nhóm người chơi nhưng tách cụm chỉ ở mức trung bình. Meta Agent rất rõ theo map. Tổ hợp phổ biến không chứng minh hiệu quả: chỉ 3/473 đội hình còn khác biệt sau FDR. Kết quả thay đổi theo map và patch.",
    )

    # 14. Limitations ----------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _header(slide, 14, "13 · Giới hạn", "Giới hạn và hướng phát triển", "Một kết quả tốt là kết quả nói rõ mình không thể kết luận điều gì.")
    _card(slide, 0.6, 1.62, 5.85, 3.30, fill=WHITE, line=LINE)
    _text(slide, "Giới hạn", 0.82, 1.78, 4.8, 0.3, size=13, bold=True, color=RED)
    _bullets(
        slide,
        [
            "Dữ liệu chỉ đến 01/2022; meta hiện tại đã khác.",
            "KAST thiếu 97,9%; không có vũ khí, tọa độ, kill log.",
            "126 người chơi bị loại vì coverage <80%.",
            "Breeze/Fracture ít trận; luật kém ổn định.",
            "FDR đã làm, nhưng chưa có hold-out theo thời gian.",
        ],
        0.82,
        2.18,
        5.35,
        2.55,
        size=10.8,
        space_after=10,
    )
    _card(slide, 6.75, 1.62, 5.95, 3.30, fill=PALE_TEAL, line=RGBColor(190, 225, 218))
    _text(slide, "Hướng phát triển", 6.97, 1.78, 5.0, 0.3, size=13, bold=True, color=TEAL)
    _bullets(
        slide,
        [
            "Hold-out theo thời gian cho các đội hình win rate cao.",
            "Mô hình thắng/thua có kiểm soát map, patch, đội.",
            "Phân cụm riêng trong từng nhóm vai trò Agent.",
            "PrefixSpan cho chuỗi round/mua sắm.",
            "Dashboard so sánh luật giữa map và patch.",
        ],
        6.97,
        2.18,
        5.35,
        2.55,
        size=10.8,
        bullet_color=TEAL,
        space_after=10,
    )
    _card(slide, 0.6, 5.20, 12.1, 0.82, fill=PALE_RED, line=RGBColor(255, 205, 210))
    _text(slide, "HỆ QUẢ", 0.82, 5.34, 1.4, 0.2, size=8.5, bold=True, color=DARK_RED)
    _text(
        slide,
        "Kết quả chỉ nên dùng để gợi ý giả thuyết, không dùng để xếp hạng người chơi hay tuyển chọn.",
        1.85,
        5.31,
        10.6,
        0.3,
        size=11.5,
        bold=True,
        color=INK,
    )
    _text(slide, "Điểm cần nhớ: đây là phân tích khám phá có kiểm định, không phải dự báo nhân quả.", 0.6, 6.35, 12.1, 0.35, size=11.5, bold=True, color=INK)
    _notes(
        slide,
        "Các giới hạn chính: dữ liệu cũ, KAST thiếu, mất 126 người chơi vì coverage, map nhỏ, và chưa có hold-out. Hướng phát triển là hold-out, mô hình có kiểm soát đội, phân cụm theo role và dashboard.",
    )

    # 15. Closing --------------------------------------------------------------
    slide = prs.slides.add_slide(blank)
    _set_bg(slide, DARK_BG)
    _rect(slide, 0, 0, 0.18, 7.5, RED)
    _text(slide, "CẢM ƠN", 0.95, 1.55, 5.0, 0.35, size=12, bold=True, color=RED)
    _text(slide, "Xin cảm ơn", 0.95, 2.05, 8.5, 0.8, size=44, bold=True, color=WHITE)
    _text(slide, "Câu hỏi & thảo luận", 0.97, 2.95, 7.0, 0.5, size=21, color=RGBColor(190, 196, 205))
    _rect(slide, 0.97, 3.75, 2.5, 0.045, RED)
    _text(slide, "Repo", 0.97, 4.20, 1.0, 0.25, size=9, bold=True, color=RGBColor(148, 163, 184))
    _text(slide, "github.com/DucZaki/Data-Mining-", 1.65, 4.17, 6.0, 0.3, size=12, color=WHITE, font=MONO)
    _text(slide, "Tái lập", 0.97, 4.70, 1.0, 0.25, size=9, bold=True, color=RGBColor(148, 163, 184))
    _text(slide, "make all", 1.65, 4.67, 3.0, 0.3, size=12, color=WHITE, font=MONO)
    _text(slide, "Kết quả", 0.97, 5.20, 1.0, 0.25, size=9, bold=True, color=RGBColor(148, 163, 184))
    _text(slide, "14.005 ván · 2.599 người chơi · 580 luật", 1.65, 5.17, 6.5, 0.3, size=11, color=RGBColor(190, 196, 205))
    _text(slide, "Đồ án khai phá dữ liệu  ·  2026", 0.97, 6.65, 6.0, 0.3, size=9, color=RGBColor(120, 132, 148))
    _notes(slide, "Cảm ơn thầy cô và các bạn. Mời đặt câu hỏi. Repo và lệnh tái lập nằm ở đây.")

    out = SLIDES / "valorant_mining_slides.pptx"
    prs.save(out)
    print(f"Đã ghi {out} ({len(prs.slides)} slide)")


if __name__ == "__main__":
    build_deck()
