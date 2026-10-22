#!/usr/bin/env python
"""Step 5: invariant checks on the generated mining datasets."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from valorant_mining.config import (
    DATA_PROCESSED,
    MIN_STAT_COVERAGE,
    MODEL_FEATURES,
    OUTPUT_TABLES,
    REPORT_DIR,
    VALID_MAPS,
)


def main() -> None:
    players = pd.read_csv(DATA_PROCESSED / "player_features.csv")
    comps = pd.read_csv(DATA_PROCESSED / "team_compositions.csv")
    games = pd.read_csv(DATA_PROCESSED / "clean_games.csv")
    rules = pd.read_csv(OUTPUT_TABLES / "agent_rules_by_map.csv")
    comps_detail = pd.read_csv(OUTPUT_TABLES / "exact_compositions.csv")

    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append((name, bool(condition), detail))

    check("Mỗi ván có đúng 2 đội hình", (comps.groupby("GameID").size() == 2).all(), "team_compositions")
    check(
        "Không trùng khóa (GameID, team)",
        not comps.duplicated(subset=["GameID", "team"]).any(),
        "team_compositions",
    )
    check("Mỗi đội có đúng 5 Agent", (comps["n_agents"] == 5).all(), "team_compositions")
    check(
        "Mỗi đội hình có 5 Agent khác nhau",
        comps["agents_str"].apply(lambda s: len(set(s.split("|"))) == 5).all(),
        "team_compositions",
    )
    check("Chỉ còn bản đồ thi đấu", comps["Map"].isin(VALID_MAPS).all(), "team_compositions")
    check("Số round trong khoảng 13–40", comps["rounds"].between(13, 40).all(), "team_compositions")
    check(
        "Nhãn thắng/thua chỉ là 0/1/NaN",
        set(comps["won"].dropna().unique()).issubset({0, 1}),
        "team_compositions",
    )

    # Compare the derived team label with the independent Games.Winner column.
    winner_check = comps.merge(
        games[["GameID", "Team1", "Team2", "Winner", "team1_abbr", "team2_abbr"]],
        on="GameID",
        how="left",
        validate="many_to_one",
    )
    winner_check["won_expected"] = pd.Series(float("nan"), index=winner_check.index)
    is_team1 = winner_check["Winner"].eq(winner_check["Team1"])
    is_team2 = winner_check["Winner"].eq(winner_check["Team2"])
    winner_check.loc[is_team1, "won_expected"] = (
        winner_check.loc[is_team1, "team"].eq(winner_check.loc[is_team1, "team1_abbr"]).astype(float)
    )
    winner_check.loc[is_team2, "won_expected"] = (
        winner_check.loc[is_team2, "team"].eq(winner_check.loc[is_team2, "team2_abbr"]).astype(float)
    )
    comparable = winner_check[
        winner_check["won"].notna() & winner_check["won_expected"].notna()
    ].copy()
    n_mismatch = int(
        (comparable["won"].astype(int) != comparable["won_expected"].astype(int)).sum()
    )
    check(
        "Nhãn thắng/thua khớp Games.Winner",
        n_mismatch == 0,
        f"{len(comparable):,} đội hình / {comparable['GameID'].nunique():,} ván, "
        f"{n_mismatch} lệch",
    )

    check("Người chơi đủ ≥10 ván", (players["games"] >= 10).all(), "player_features")
    check("Người chơi đủ ≥100 round", (players["rounds"] >= 100).all(), "player_features")
    check(
        f"Độ phủ ACS/ADR/HS ≥{MIN_STAT_COVERAGE:.0%}",
        players[["acs_coverage", "adr_coverage", "hs_coverage"]]
        .ge(MIN_STAT_COVERAGE)
        .all()
        .all(),
        "player_features",
    )
    check(
        "Không thiếu biến mô hình",
        players[MODEL_FEATURES].notna().all().all(),
        "player_features",
    )
    check("Không trùng PlayerID", not players["PlayerID"].duplicated().any(), "player_features")
    if not rules.empty:
        check("Support trong (0, 1]", rules["support"].between(0, 1, inclusive="right").all(), "rules")
        check("Confidence trong (0, 1]", rules["confidence"].between(0, 1, inclusive="right").all(), "rules")
        check("Lift ≥ 1", (rules["lift"] >= 1).all(), "rules")
        check("Support count ≤ số đội hình", (rules["support_count"] <= rules["n_teams"]).all(), "rules")
    if not comps_detail.empty:
        check(
            "Đội hình chi tiết có đúng 5 Agent",
            comps_detail["agents_str"].apply(lambda s: len(set(s.split("|"))) == 5).all(),
            "exact_compositions",
        )
        check(
            "Win rate trong [0, 1]",
            comps_detail["win_rate"].between(0, 1).all(),
            "exact_compositions",
        )

    lines = [
        "# Kiểm tra chất lượng đầu ra",
        "",
        "| Kiểm tra | Kết quả | Nguồn |",
        "|---|---|---|",
    ]
    for name, ok, source in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {source} |")

    failed = [c for c in checks if not c[1]]
    lines += [
        "",
        f"**Tổng:** {len(checks)} kiểm tra, {len(failed)} lỗi.",
        "",
        "Các kiểm tra này chỉ xác nhận tính nhất quán của dữ liệu đầu ra; không thay thế kiểm định thống kê cho các kết luận về thắng/thua.",
    ]
    (REPORT_DIR / "04_kiem_tra_chat_luong.md").write_text("\n".join(lines), encoding="utf-8")

    for name, ok, _ in checks:
        print(("PASS" if ok else "FAIL"), "-", name)
    if failed:
        raise SystemExit(f"{len(failed)} kiểm tra thất bại")
    print(f"\nĐã ghi reports/04_kiem_tra_chat_luong.md ({len(checks)} kiểm tra)")


if __name__ == "__main__":
    main()
