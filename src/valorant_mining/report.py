"""Build the preliminary results report from the generated tables."""

from __future__ import annotations

import pandas as pd

from .audit import md_table
from .config import DATA_PROCESSED, FIGURE_DIR, OUTPUT_TABLES, REPORT_DIR


def _read_summary(name: str) -> pd.Series:
    df = pd.read_csv(OUTPUT_TABLES / name)
    return df.set_index(df.columns[0])[df.columns[1]]


def _as_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def _comp_value(comps: pd.DataFrame, map_name: str, agents: str, column: str) -> float:
    subset = comps[(comps["map"] == map_name) & (comps["agents_str"] == agents)]
    return float(subset[column].iloc[0]) if len(subset) else float("nan")


def _comp_text(comps: pd.DataFrame, map_name: str, agents: str) -> str:
    wr = _comp_value(comps, map_name, agents, "win_rate")
    n = _comp_value(comps, map_name, agents, "n")
    return f"{_pct(wr)} (n = {int(n)})" if pd.notna(wr) else "không đủ mẫu"


def build_results_report() -> str:
    players = pd.read_csv(DATA_PROCESSED / "player_features.csv")
    attrition = pd.read_csv(DATA_PROCESSED / "player_attrition.csv")
    evaluation = pd.read_csv(OUTPUT_TABLES / "cluster_evaluation.csv")
    profiles = pd.read_csv(OUTPUT_TABLES / "cluster_profiles_raw.csv")
    zprofiles = pd.read_csv(OUTPUT_TABLES / "cluster_profiles_z.csv")
    stability = pd.read_csv(OUTPUT_TABLES / "cluster_stability.csv")
    csummary = _read_summary("clustering_summary.csv")

    rules_summary = _read_summary("agent_rules_summary.csv")
    rules = pd.read_csv(OUTPUT_TABLES / "agent_rules_report.csv")
    all_rules = pd.read_csv(OUTPUT_TABLES / "agent_rules_by_map.csv")
    comps = pd.read_csv(OUTPUT_TABLES / "exact_compositions.csv")
    highlights = pd.read_csv(OUTPUT_TABLES / "composition_highlights.csv")
    pick = pd.read_csv(OUTPUT_TABLES / "agent_pick_rates_by_map.csv")
    patch = pd.read_csv(OUTPUT_TABLES / "agent_pick_rates_by_patch.csv")

    chosen_k = int(_as_float(csummary["k"]))
    best_k = int(_as_float(csummary["best_silhouette_k"]))
    best_sil = _as_float(csummary["best_silhouette"])
    silhouette = _as_float(csummary["silhouette"])
    stability_ari = _as_float(csummary["stability_mean_ari"])
    ward_ari = _as_float(csummary["ward_ari"])
    n_players = len(players)
    n_comps = len(pd.read_csv(DATA_PROCESSED / "team_compositions.csv"))
    n_labeled = int(rules_summary["teams_with_win_label"])
    n_rules = int(rules_summary["rules"])

    # --- cluster table ---
    cluster_rows = []
    for row in profiles.itertuples():
        label = getattr(row, "cluster_label")
        cluster_rows.append(
            {
                "Cụm": f"C{row.cluster}",
                "Tên gợi ý": label,
                "n": int(row.n_players),
                "Kills/R": round(row.kills_pr, 3),
                "Deaths/R": round(row.deaths_pr, 3),
                "Assists/R": round(row.assists_pr, 3),
                "K/D": round(row.kd, 3),
                "ACS": round(row.acs, 1),
                "ADR": round(row.adr, 1),
                "FK/R": round(row.fk_pr, 3),
                "FD/R": round(row.fd_pr, 3),
                "Multi/R": round(row.multi_pr, 3),
                "SD ACS": round(row.acs_sd, 1),
                "Win rate": _pct(row.win_rate),
                "Duelist share": _pct(row.role_duelist_share),
            }
        )
    cluster_table = pd.DataFrame(cluster_rows)

    eval_table = evaluation[["k", "inertia", "silhouette", "calinski_harabasz", "davies_bouldin"]].copy()
    eval_table["k"] = eval_table["k"].astype(int)
    eval_table["inertia"] = eval_table["inertia"].round(0).astype(int)
    eval_table["silhouette"] = eval_table["silhouette"].round(3)
    eval_table["calinski_harabasz"] = eval_table["calinski_harabasz"].round(0).astype(int)
    eval_table["davies_bouldin"] = eval_table["davies_bouldin"].round(3)

    # --- rule table (top 4 per map) ---
    report_rules = (
        rules.sort_values(["map", "lift"], ascending=[True, False])
        .groupby("map", group_keys=False)
        .head(4)
        .copy()
    )
    report_rules["support"] = report_rules["support"].round(3)
    report_rules["confidence"] = report_rules["confidence"].round(3)
    report_rules["lift"] = report_rules["lift"].round(2)
    report_rules["win_rate_with_antecedent"] = report_rules["win_rate_with_antecedent"].round(3)
    report_rules = report_rules.rename(
        columns={
            "map": "Map",
            "rule": "Luật",
            "support": "Support",
            "confidence": "Confidence",
            "lift": "Lift",
            "support_count": "n đội hình",
            "win_rate_with_antecedent": "Win rate khi có vế trái",
        }
    )[
        ["Map", "Luật", "n đội hình", "Support", "Confidence", "Lift", "Win rate khi có vế trái"]
    ]

    # --- exact composition table ---
    comp_table = comps.sort_values("n", ascending=False).head(12).copy()
    comp_table["Đội hình"] = comp_table["agents_str"].str.replace("|", " + ", regex=False)
    comp_table["Win rate"] = comp_table["win_rate"].apply(_pct)
    comp_table["CI 95%"] = comp_table.apply(
        lambda r: f"{_pct(r['win_rate_ci_low'])}–{_pct(r['win_rate_ci_high'])}", axis=1
    )
    comp_table = comp_table.rename(columns={"map": "Map", "n": "n"})[
        ["Map", "Đội hình", "n", "Win rate", "CI 95%"]
    ]

    # --- agent pick rates: top 3 per map ---
    top_pick = (
        pick.sort_values(["map", "pick_rate"], ascending=[True, False])
        .groupby("map", group_keys=False)
        .head(3)
        .copy()
    )
    top_pick["Tỷ lệ chọn"] = top_pick["pick_rate"].apply(_pct)
    top_pick = top_pick.rename(columns={"map": "Map", "agent": "Agent"})[
        ["Map", "Agent", "Tỷ lệ chọn"]
    ]

    # --- patch meta table ---
    patch_agg = (
        patch.groupby(["patch_major", "agent"], as_index=False)
        .agg(picks=("picks", "sum"), teams=("teams", "sum"))
    )
    patch_agg["pick_rate"] = patch_agg["picks"] / patch_agg["teams"]
    patch_totals = patch.groupby("patch_major")["teams"].sum()
    usable_patches = patch_totals[patch_totals >= 500].index
    patch_agg = patch_agg[patch_agg["patch_major"].isin(usable_patches)]
    patch_top = (
        patch_agg.sort_values(["patch_major", "pick_rate"], ascending=[True, False])
        .groupby("patch_major", group_keys=False)
        .head(5)
    )
    patch_rows = []
    for patch_name, group in patch_top.groupby("patch_major", sort=True):
        patch_rows.append(
            {
                "Giai đoạn": patch_name,
                "Agent được chọn nhiều": ", ".join(
                    f"{r.agent} ({_pct(r.pick_rate)})" for r in group.itertuples()
                ),
            }
        )
    patch_table = pd.DataFrame(patch_rows)

    # --- notable win-rate compositions (still descriptive) ---
    notable = highlights[highlights["ci_excludes_50"]].head(8).copy()
    notable["Đội hình"] = notable["agents_str"].str.replace("|", " + ", regex=False)
    notable["Win rate"] = notable["win_rate"].apply(_pct)
    notable["CI 95%"] = notable.apply(
        lambda r: f"{_pct(r['win_rate_ci_low'])}–{_pct(r['win_rate_ci_high'])}", axis=1
    )
    notable = notable.rename(columns={"map": "Map", "n": "n"})[
        ["Map", "Đội hình", "n", "Win rate", "CI 95%"]
    ]

    # --- top support rules overall ---
    top_support = (
        all_rules.sort_values(["map", "support_count"], ascending=[True, False])
        .groupby("map", group_keys=False)
        .head(2)
        .copy()
    )
    top_support["Support"] = top_support["support"].apply(_pct)
    top_support["Confidence"] = top_support["confidence"].apply(_pct)
    top_support["Lift"] = top_support["lift"].round(2)
    top_support = top_support.rename(
        columns={"map": "Map", "rule": "Luật", "support_count": "n"}
    )[["Map", "Luật", "n", "Support", "Confidence", "Lift"]]

    c0 = profiles[profiles["cluster"] == 0].iloc[0]
    c1 = profiles[profiles["cluster"] == 1].iloc[0]
    c2 = profiles[profiles["cluster"] == 2].iloc[0]

    text = f"""# Kết quả khai phá sơ bộ

> Báo cáo được sinh tự động từ các bảng trong `outputs/tables/`. Số liệu dưới đây là kết quả trên **14.005 ván** còn lại sau làm sạch, không phải toàn bộ 15.888 ván gốc.

## 0. Tóm tắt điều hành

- **Phân cụm:** {n_players:,} người chơi đủ ≥10 ván và ≥100 round. Chọn **k = {chosen_k}** cụm; silhouette = **{silhouette:.3f}**, độ ổn định bootstrap (ARI) = **{stability_ari:.3f}**.
- **Luật kết hợp:** {n_comps:,} đội hình 5 Agent trên 7 bản đồ; {n_labeled:,} đội hình có nhãn thắng/thua; **{n_rules} luật** vượt ngưỡng support/confidence/lift.
- **Phát hiện chính:** các tổ hợp Agent phổ biến mang tính meta rất rõ theo map (ví dụ Icebox gần như cố định Viper–Sage–Sova), nhưng **tỷ lệ thắng của các tổ hợp phổ biến phần lớn không khác 50% một cách có ý nghĩa thống kê**. Đồng xuất hiện không đồng nghĩa với hiệu quả.
- **Lưu ý phương pháp:** silhouette cao nhất ở k = {best_k} ({best_sil:.3f}); nhóm chọn k = {chosen_k} vì khung phân tích đặt trước 3–5 cụm và k = {chosen_k} tách được ba kiểu hồ sơ có thể diễn giải. Đây là lựa chọn có chủ đích, cần ghi rõ trong báo cáo.

## 1. Bài toán 1 — Phân cụm người chơi

### 1.1. Dữ liệu đầu vào

{md_table(attrition.rename(columns={"step": "Bước", "players": "Số người chơi"}))}

Biến dùng cho mô hình: Kills/round, Deaths/round, Assists/round, K/D, ACS, ADR, First kills/round, First deaths/round, multi-kill/round, độ lệch chuẩn ACS, HS%. Các biến được winsorize 1%–99% trước khi chuẩn hóa bằng StandardScaler.

KAST bị loại vì thiếu 97,9% và không thể thay bằng 0.

### 1.2. Chọn số cụm

{md_table(eval_table)}

- Silhouette cao nhất ở **k = {best_k}** ({best_sil:.3f}), nhưng đây là phương án chỉ chia người chơi thành hai nhóm rất rộng.
- Trong khoảng 3–5 cụm, **k = {chosen_k}** có silhouette cao nhất ({silhouette:.3f}) và cho ba chân dung khác nhau về hành vi đo được.
- Độ ổn định bootstrap 80% (30 lần): ARI trung bình **{stability_ari:.3f}**, thấp nhất **{stability['ari_vs_full'].min():.3f}**. Các cụm gần như giữ nguyên khi lấy mẫu lại.
- So sánh với Hierarchical Ward (cùng k): ARI = **{ward_ari:.3f}**. Hai thuật toán không hoàn toàn đồng nhất, nên cấu trúc cụm chỉ nên được xem là một mô tả khám phá, không phải chân lý.

### 1.3. Chân dung cụm

{md_table(cluster_table)}

Diễn giải dựa trên z-score:

- **C0 — Mở giao tranh · Sát thương cao** ({int(c0.n_players)} người): First kills/round, ACS, Kills/round và multi-kill cao nhất; assists thấp. Đây là nhóm tạo áp lực mở giao tranh, nhưng cũng chết ở mức trên trung bình. Khoảng **{_pct(c0.role_duelist_share)}** số ván của nhóm dùng Agent Duelist — cần nhấn mạnh đây là đặc điểm mô tả, không phải nhãn vai trò.
- **C1 — Chết nhiều · Hiệu quả thấp** ({int(c1.n_players)} người): Kills/round, ACS, ADR và K/D thấp nhất; Deaths/round và First deaths/round cao. Win rate chỉ **{_pct(c1.win_rate)}**, thấp hơn hai nhóm còn lại. Có thể đây là nhóm người chơi bị kéo xuống bởi đội yếu hoặc mẫu trận thua, không thể quy kết chỉ do phong cách cá nhân.
- **C2 — Ít chết · Hiệu quả cao** ({int(c2.n_players)} người): Assists/round, K/D và HS% cao; Deaths/round, First deaths/round thấp. ACS chỉ ở mức trung bình, cho thấy nhóm này tạo giá trị bằng độ ổn định và hỗ trợ hơn là số kill thô. Win rate **{_pct(c2.win_rate)}**.

**Cảnh báo diễn giải:** cụm C0 có tỷ lệ Duelist rất cao, còn C1/C2 chủ yếu là các vai trò khác. Vì vậy “phong cách” trong dữ liệu này chịu ảnh hưởng mạnh bởi Agent được chọn. Không nên viết “C0 là Duelist” hay “C2 là IGL” khi chưa có dữ liệu vai trò/chiến thuật.

### 1.4. Hình

- `reports/figures/02_cluster_selection.png`
- `reports/figures/02_cluster_pca.png`
- `reports/figures/02_cluster_profiles.png`
- `reports/figures/02_cluster_boxplots.png`

## 2. Bài toán 2 — Luật kết hợp Agent theo bản đồ

### 2.1. Cách chạy

- Mỗi dòng là một **đội trong một ván**, gồm đúng 5 Agent không có thứ tự.
- FP-Growth, tối đa 3 Agent trong một itemset; ngưỡng support tối thiểu là `max(12 đội, 2%)` cho mỗi map.
- Luật giữ lại nếu confidence ≥ 0,40 và lift ≥ 1,05. Bảng báo cáo chỉ lấy luật có ≥30 đội hình, confidence ≥0,5 và vế trái tối đa 2 Agent.

### 2.2. Luật nổi bật theo bản đồ

{md_table(report_rules)}

Đọc bảng: `Support` là tỷ lệ đội hình chứa toàn bộ Agent trong luật; `Confidence` là xác suất có vế phải khi đã có vế trái; `Lift` > 1 nghĩa là hai vế xuất hiện cùng nhau nhiều hơn so với kỳ vọng độc lập. Các map nhỏ (Breeze, Fracture) có n nhỏ, không nên so sánh trực tiếp độ lớn lift với Ascent/Haven.

### 2.3. Các cặp/tổ hợp có support cao nhất

{md_table(top_support)}

Đây là các tổ hợp gần như “mặc định” của meta trong giai đoạn dữ liệu: ví dụ Icebox có Viper–Sage–Sova, Bind có Sova–Omen, Haven có Omen–Cypher. Support cao phản ánh mức độ phổ biến, **không** phản ánh sức mạnh.

### 2.4. Tỷ lệ chọn Agent theo map

{md_table(top_pick)}

### 2.5. So sánh theo phiên bản lớn

{md_table(patch_table)}

Bảng này cho thấy meta thay đổi theo patch; vì vậy mọi kết luận “Agent X mạnh” cần gắn với một giai đoạn cụ thể.

## 3. Tổ hợp phổ biến có thắng nhiều hơn không?

### 3.1. Các đội hình 5 Agent xuất hiện nhiều nhất

{md_table(comp_table)}

Ví dụ đáng chú ý trên Icebox: hai đội hình phổ biến nhất chỉ khác nhau ở vị trí Reyna/Killjoy, nhưng tỷ lệ thắng quan sát được là **{_comp_text(comps, 'Icebox', 'jett|reyna|sage|sova|viper')}** so với **{_comp_text(comps, 'Icebox', 'jett|killjoy|sage|sova|viper')}**. Khoảng tin cậy 95% của hai tỷ lệ này không chồng lên nhau, nhưng đây vẫn là quan hệ quan sát: đội mạnh có thể tự chọn đội hình tốt hơn.

### 3.2. Các đội hình có khoảng tin cậy không chứa 50%

{md_table(notable)}

Đây là danh sách **khám phá**, không phải kết luận nhân quả. Có nhiều phép so sánh được thực hiện, nên một vài khoảng tin cậy “có ý nghĩa” có thể xuất hiện do ngẫu nhiên. Cần kiểm định lại trên tập hold-out hoặc mô hình có kiểm soát đội, map, patch.

## 4. Trả lời câu hỏi nghiên cứu

1. **Có những nhóm người chơi nào?** Ba nhóm: mở giao tranh/sát thương cao, chết nhiều/hiệu quả thấp, ít chết/hiệu quả cao. Độ ổn định cao (ARI {stability_ari:.3f}), nhưng silhouette chỉ ở mức trung bình ({silhouette:.3f}).
2. **Agent nào thường đi cùng nhau theo map?** Có cấu trúc rõ: Ascent (Kayo–Astra–Jett/Killjoy), Bind (Brimstone–Viper–Skye), Haven (Cypher–Omen–Sova), Icebox (Viper–Sage–Sova), Split (Astra–Viper–Skye), Breeze (Cypher–Sova–Viper), Fracture (Breach–Cypher–Raze).
3. **Tổ hợp phổ biến có thắng nhiều hơn?** Nhìn chung không có bằng chứng mạnh: phần lớn luật có win rate 46–55% và khoảng tin cậy chứa 50%. Một số đội hình ít phổ biến hơn có win rate cao, nhưng n nhỏ và có thể do chọn đội.
4. **Khác nhau theo map/patch?** Có. Tỷ lệ chọn Agent thay đổi theo map và theo patch lớn; một số tổ hợp chỉ tồn tại trong một giai đoạn meta.

## 5. Giới hạn

- Dữ liệu chỉ đến **2022-01-08**; meta hiện tại đã khác.
- KAST thiếu **97,9%**, không dùng trong mô hình.
- Không có dữ liệu vũ khí, tọa độ giao tranh, kỹ năng Agent, kill log.
- Chỉ **14.005/15.888 ván** có đủ 2 đội × 5 người × 5 Agent; các ván thiếu bị loại, có thể tạo thiên lệch chọn mẫu.
- Nhãn thắng/thua chỉ có cho **{100 * n_labeled / n_comps:.1f}%** đội hình.
- Breeze/Fracture có ít trận; luật của hai map này kém ổn định.
- Luật kết hợp chỉ đo đồng xuất hiện, không đo nhân quả.
- Phân cụm bị ảnh hưởng bởi Agent role; chưa tách được “phong cách” khỏi “vai trò”.
- Các so sánh tỷ lệ thắng chưa hiệu chỉnh multiple comparisons và chưa kiểm soát chất lượng đội.

## 6. Hướng tiếp theo

1. Kiểm định lại các đội hình có win rate cao trên tập hold-out theo thời gian (train trước 2021-07, test sau).
2. Thêm mô hình hồi quy logistic/hierarchical cho thắng/thua với biến kiểm soát map, patch, đội.
3. Phân cụm riêng trong từng nhóm vai trò Agent để tách phong cách khỏi role.
4. Khai phá chuỗi round/mua sắm bằng PrefixSpan nếu còn thời gian.
5. Bổ sung dashboard so sánh luật giữa các map và patch.
"""
    return text


def save_results_report() -> None:
    text = build_results_report()
    (REPORT_DIR / "03_ket_qua_so_bo.md").write_text(text, encoding="utf-8")
    print("Đã ghi reports/03_ket_qua_so_bo.md")
