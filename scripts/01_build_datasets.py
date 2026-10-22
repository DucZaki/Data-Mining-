#!/usr/bin/env python
"""Step 1: build clean games, team compositions and player features."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from valorant_mining.cleaning import build_clean_data, save_clean_data
from valorant_mining.config import OUTPUT_TABLES, REPORT_DIR
from valorant_mining.features import build_player_features, save_player_features


def main() -> None:
    clean = build_clean_data()
    save_clean_data(clean)

    players, attrition = build_player_features(clean.scoreboard)
    save_player_features(players, attrition)
    attrition.to_csv(OUTPUT_TABLES / "player_attrition.csv", index=False)

    comps = clean.compositions
    map_summary = (
        comps.groupby("Map")
        .agg(teams=("GameID", "size"), games=("GameID", "nunique"), win_label=("won", "count"))
        .reset_index()
        .sort_values("teams", ascending=False)
    )
    map_summary.to_csv(OUTPUT_TABLES / "composition_map_summary.csv", index=False)

    lines = [
        "# Dữ liệu khai phá đã xây dựng",
        "",
        "## 1. Nhật ký làm sạch",
        "",
        "| Chỉ số | Giá trị |",
        "|---|---|",
    ]
    for key, value in clean.audit.items():
        lines.append(f"| {key} | {value} |")

    lines += [
        "",
        "## 2. Người chơi sau ngưỡng tối thiểu",
        "",
        "| Bước | Số người chơi |",
        "|---|---|",
    ]
    for row in attrition.itertuples():
        lines.append(f"| {row.step} | {row.players} |")

    lines += [
        "",
        "## 3. Đội hình theo bản đồ",
        "",
        "| Bản đồ | Số ván | Số đội hình | Có nhãn thắng |",
        "|---|---|---|---|",
    ]
    for row in map_summary.itertuples():
        lines.append(f"| {row.Map} | {row.games} | {row.teams} | {row.win_label} |")

    lines += [
        "",
        "## 4. Biến dùng cho phân cụm",
        "",
        "Các biến được tổng hợp theo PlayerID, chia theo tổng số round để tránh ưu tiên các ván có overtime:",
        "",
        "- Kills/round, Deaths/round, Assists/round, K/D",
        "- ACS, ADR, HS%",
        "- First kills/round, First deaths/round",
        "- Số multi-kill (2K–5K) trên mỗi round",
        "- Độ lệch chuẩn ACS giữa các ván (độ ổn định)",
        "",
        "KAST bị loại vì thiếu gần như toàn bộ. ACS/ADR/HS% chỉ lấy trung bình trên các ván có giá trị, không thay giá trị thiếu bằng 0; người chơi có độ phủ dưới 80% bị loại. Trước K-Means, các biến được winsorize, chuẩn hóa và giảm chiều bằng PCA giữ ≥80% phương sai. Tỷ lệ chọn vai trò Agent chỉ dùng để mô tả cụm, không đưa vào mô hình.",
        "",
        "## 5. File sinh ra",
        "",
        "- `data/processed/clean_games.csv`",
        "- `data/processed/clean_scoreboard.csv`",
        "- `data/processed/team_compositions.csv`",
        "- `data/processed/player_features.csv`",
        "- `data/processed/player_attrition.csv`",
    ]
    (REPORT_DIR / "02_du_lieu_khai_pha.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Ván sạch: {len(clean.games):,}")
    print(f"Đội hình: {len(comps):,}")
    print(f"Người chơi đủ điều kiện: {len(players):,}")
    print(map_summary.to_string(index=False))


if __name__ == "__main__":
    main()
