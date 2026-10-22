"""Data audit: what is in the raw database and what survives cleaning."""

from __future__ import annotations

import pandas as pd

from .cleaning import build_clean_data, parse_round_history
from .db import read_sql, table_counts


def md_table(df: pd.DataFrame, floatfmt: str = ".2f") -> str:
    """Minimal markdown table writer (avoids a hard tabulate dependency)."""
    if df.empty:
        return "_Không có dữ liệu._"
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |"]
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for row in df.itertuples(index=False):
        cells = []
        for value in row:
            if isinstance(value, float):
                if pd.isna(value):
                    cells.append("")
                else:
                    cells.append(f"{value:{floatfmt}}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def collect_audit() -> dict:
    counts = table_counts()
    matches = read_sql("SELECT Date, Patch FROM Matches")
    maps = read_sql("SELECT Map, COUNT(*) AS games FROM Games GROUP BY Map ORDER BY games DESC")
    scoreboard = read_sql(
        """
        SELECT GameID, PlayerID, TeamAbbreviation, Agent, ACS, KAST_Percent,
               FirstKills, Num_2Ks
        FROM Game_Scoreboard
        """
    )
    games = read_sql(
        "SELECT GameID, Team1_TotalRounds, Team2_TotalRounds FROM Games"
    )
    rounds = read_sql("SELECT GameID, RoundHistory FROM Game_Rounds")

    n = len(scoreboard)
    missing = pd.DataFrame(
        [
            {"field": "PlayerID", "missing": int(scoreboard["PlayerID"].isna().sum())},
            {
                "field": "Agent (rỗng/null)",
                "missing": int(
                    (scoreboard["Agent"].isna() | (scoreboard["Agent"].astype(str).str.strip() == "")).sum()
                ),
            },
            {"field": "ACS", "missing": int(scoreboard["ACS"].isna().sum())},
            {"field": "KAST_Percent", "missing": int(scoreboard["KAST_Percent"].isna().sum())},
            {"field": "FirstKills", "missing": int(scoreboard["FirstKills"].isna().sum())},
            {"field": "Num_2Ks", "missing": int(scoreboard["Num_2Ks"].isna().sum())},
        ]
    )
    missing["missing_pct"] = 100 * missing["missing"] / n

    gp = (
        scoreboard[scoreboard["PlayerID"].notna()]
        .groupby("PlayerID")["GameID"]
        .nunique()
    )
    thresholds = [1, 5, 10, 15, 20, 30, 50]
    gp_table = pd.DataFrame(
        [
            {"min_games": t, "players": int((gp >= t).sum())}
            for t in thresholds
        ]
    )

    rows_per_game = (
        scoreboard.groupby("GameID").size().value_counts().sort_index().reset_index()
    )
    rows_per_game.columns = ["rows_per_game", "games"]

    # KAST coverage and range among non-missing rows.
    kast = scoreboard["KAST_Percent"].dropna()
    kast_summary = pd.DataFrame(
        [
            {
                "non_missing": int(len(kast)),
                "coverage_pct": 100 * len(kast) / n,
                "min": kast.min(),
                "median": kast.median(),
                "max": kast.max(),
            }
        ]
    )

    rh = rounds.copy()
    rh["rh_rounds"] = rh["RoundHistory"].apply(
        lambda x: len(parse_round_history(x)) if parse_round_history(x) else None
    )
    game_rounds = games.set_index("GameID")
    rh["games_rounds"] = rh["GameID"].map(
        game_rounds["Team1_TotalRounds"] + game_rounds["Team2_TotalRounds"]
    )
    rh_coverage = pd.DataFrame(
        [
            {
                "games": int(len(games)),
                "with_round_history": int(rh["rh_rounds"].notna().sum()),
                "coverage_pct": 100 * rh["rh_rounds"].notna().mean(),
                "round_count_mismatch": int(
                    ((rh["rh_rounds"].notna()) & (rh["rh_rounds"] != rh["games_rounds"])).sum()
                ),
            }
        ]
    ).astype(
        {
            "games": int,
            "with_round_history": int,
            "round_count_mismatch": int,
        }
    )

    # Team-level validity before the final clean dataset.
    sb = scoreboard.copy()
    sb["Agent"] = sb["Agent"].fillna("").astype(str).str.strip().str.lower()
    sb["TeamAbbreviation"] = sb["TeamAbbreviation"].fillna("").astype(str).str.strip()
    sb = sb[
        sb["PlayerID"].notna()
        & (sb["Agent"] != "")
        & (sb["TeamAbbreviation"] != "")
    ]
    teams = sb.groupby(["GameID", "TeamAbbreviation"]).agg(
        n=("PlayerID", "nunique"), a=("Agent", "nunique")
    )
    team_validity = pd.DataFrame(
        [
            {
                "team_group_size": int(size),
                "groups": int(len(group)),
                "groups_with_5_distinct_agents": int(
                    ((group["n"] == 5) & (group["a"] == 5)).sum()
                ),
            }
            for size, group in teams.groupby("n")
        ]
    ).sort_values("team_group_size")

    audit = {
        "counts": counts,
        "date_min": matches["Date"].min(),
        "date_max": matches["Date"].max(),
        "n_patches_raw": int(matches["Patch"].nunique(dropna=True)),
        "maps": maps,
        "missing": missing,
        "players_total": int(gp.size),
        "players_by_threshold": gp_table,
        "games_per_player": gp,
        "rows_per_game": rows_per_game,
        "kast_summary": kast_summary,
        "round_history": rh_coverage,
        "team_validity": team_validity,
        "games": int(len(games)),
        "games_rounds_gt_40": int(
            ((games["Team1_TotalRounds"] + games["Team2_TotalRounds"]) > 40).sum()
        ),
        "games_rounds_lt_13": int(
            ((games["Team1_TotalRounds"] + games["Team2_TotalRounds"]) < 13).sum()
        ),
        "scoreboard_rows": int(n),
    }
    return audit


def build_audit_report() -> tuple[str, dict]:
    audit = collect_audit()
    clean = build_clean_data()
    scores = clean.scoreboard
    comps = clean.compositions

    missing = audit["missing"].copy()
    missing["missing_pct"] = missing["missing_pct"].round(2)

    attrition = pd.DataFrame(
        [
            {"bước": "Bảng điểm gốc", "số dòng": audit["scoreboard_rows"]},
            {"bước": "Sau khi bỏ PlayerID/Agent/đội thiếu", "số dòng": clean.audit["scoreboard_rows_clean"]},
            {"bước": "Ván có 2 đội × 5 người chơi hợp lệ", "số dòng": clean.audit["games_with_valid_rosters"]},
            {"bước": "Ván còn lại sau kiểm tra số round và bản đồ", "số dòng": clean.audit["games_after_round_and_map_filter"]},
            {"bước": "Đội hình 5 Agent dùng cho luật kết hợp", "số dòng": clean.audit["teams_in_compositions"]},
        ]
    )

    map_pick = (
        comps["Map"].value_counts().rename_axis("map").reset_index(name="teams")
    )
    map_pick["games"] = (map_pick["teams"] / 2).astype(int)

    text = f"""# Kiểm tra dữ liệu Valorant

## 1. Quy mô và phạm vi

- Khoảng thời gian: **{audit['date_min']}** đến **{audit['date_max']}**.
- Số bảng: Matches, Games, Game_Scoreboard, Game_Rounds.
- Số patch thô trong bảng Matches: **{audit['n_patches_raw']}** (chuỗi patch chưa được chuẩn hóa, có cả giá trị thiếu).

{md_table(audit['counts'])}

## 2. Phân bố bản đồ

{md_table(audit['maps'])}

Bản đồ `TBD` không phải bản đồ thi đấu và bị loại khỏi phân tích đội hình. `Fracture` chỉ có 107 ván, nên các luật riêng cho Fracture có độ tin cậy thấp hơn các map còn lại.

## 3. Mức độ thiếu dữ liệu

{md_table(missing)}

**KAST không dùng làm biến trung tâm.** Chỉ {int(audit['kast_summary'].iloc[0]['non_missing'])} dòng có KAST ({audit['kast_summary'].iloc[0]['coverage_pct']:.1f}%), và giá trị nằm trong khoảng {audit['kast_summary'].iloc[0]['min']:.2f}–{audit['kast_summary'].iloc[0]['max']:.2f}. Việc thay giá trị thiếu bằng 0 sẽ tạo ra một biến giả có ý nghĩa sai, nên KAST bị loại khỏi mô hình.

Số dòng mỗi ván:

{md_table(audit['rows_per_game'])}

Các ván không có đúng 10 dòng thường thiếu người chơi, thiếu Agent hoặc có dòng huấn luyện viên/dự bị. Những ván này không thể tạo đội hình 5 Agent đầy đủ.

## 4. Người chơi và ngưỡng tối thiểu

Tổng số PlayerID khác nhau: **{audit['players_total']}**.

{md_table(audit['players_by_threshold'])}

Ngưỡng mặc định của dự án là **≥ 10 ván** và **≥ 100 round**. Ngưỡng này giữ được {int(audit['players_by_threshold'].loc[audit['players_by_threshold']['min_games']==10, 'players'].iloc[0])} người chơi trước khi áp thêm yêu cầu độ phủ ACS/ADR/HS ≥80% và đủ biến mô hình.

## 5. Lịch sử round

{md_table(audit['round_history'])}

Khoảng {audit['round_history'].iloc[0]['coverage_pct']:.1f}% ván có RoundHistory. Trong số này, một số ít ván có tổng round của bảng Games không khớp với độ dài lịch sử round; các ván đó bị loại để tránh chia sai mẫu số khi tính chỉ số theo round. Trong bảng Games gốc có **{audit['games_rounds_gt_40']} ván** vượt 40 round (đều là 42 round) và **{audit['games_rounds_lt_13']} ván** dưới 13 round; ngưỡng 13–40 loại các ván này sau bước kiểm tra đội hình.

## 6. Chất lượng nhóm đội

{md_table(audit['team_validity'])}

Một nhóm có 5 người chơi vẫn có thể không đủ 5 Agent khác nhau (ví dụ trùng Agent hoặc thiếu Agent). Các nhóm như vậy bị loại khỏi tập đội hình dùng cho luật kết hợp.

## 7. Kết quả làm sạch

{md_table(attrition)}

- Số ván còn lại: **{clean.audit['games_after_round_and_map_filter']}**.
- Số đội hình (team-map): **{clean.audit['teams_in_compositions']}**.
- Số đội hình có nhãn thắng/thua: **{clean.audit['compositions_with_win_label']}** ({100*clean.audit['compositions_with_win_label']/clean.audit['teams_in_compositions']:.1f}%).
- Số người chơi còn trong bảng điểm sạch: **{clean.audit['players_remaining']}**.
- Số đội hình theo bản đồ:

{md_table(map_pick)}

## 8. Hệ quả cho phân tích

1. **Đơn vị phân tích của phân cụm** là một PlayerID, tổng hợp qua các ván có đủ dữ liệu; không dùng từng dòng game.
2. **Đơn vị phân tích của luật kết hợp** là một đội trong một ván, với tập 5 Agent không có thứ tự.
3. **Không đưa KAST vào mô hình**; các biến thay thế là Kills/round, Deaths/round, ACS, ADR, FirstKills/Deaths và tần suất multi-kill.
4. **Không kết luận nhân quả** từ luật kết hợp. Một tổ hợp xuất hiện nhiều chỉ cho biết nó phổ biến, không chứng minh nó làm tăng tỷ lệ thắng.
5. Dữ liệu dừng ở **{audit['date_max'][:10]}**, nên kết quả không đại diện cho meta hiện tại.

## 9. File sinh ra

- `data/processed/clean_games.csv`
- `data/processed/clean_scoreboard.csv`
- `data/processed/team_compositions.csv`
- `data/processed/cleaning_audit.csv`
- `reports/figures/01_audit_overview.png`
- `reports/figures/01_audit_missing.png`
"""
    return text, audit
