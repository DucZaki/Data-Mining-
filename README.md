# Valorant Competitive Data Mining

Đề tài: **Phân cụm người chơi Valorant theo phong cách thi đấu và khai phá các tổ hợp Agent phổ biến theo bản đồ.**

Dự án dùng cơ sở dữ liệu `data/raw/valorant.sqlite` (4 bảng: `Matches`, `Games`, `Game_Scoreboard`, `Game_Rounds`) để xây dựng hai bài toán khai phá dữ liệu có thể bảo vệ được bằng số liệu, thay vì chỉ vẽ biểu đồ mô tả.

## 1. Câu hỏi nghiên cứu

1. Có những nhóm người chơi nào dựa trên khả năng hạ gục, hỗ trợ, mở giao tranh và độ ổn định?
2. Agent nào thường xuất hiện cùng nhau trên từng bản đồ?
3. Những tổ hợp Agent phổ biến có hiệu suất thắng khác nhau không?
4. Kết quả thay đổi thế nào giữa các bản đồ và các phiên bản game?

## 2. Kết quả sơ bộ

| Hạng mục | Kết quả |
|---|---|
| Ván còn sau làm sạch | **14.005 / 15.888** ván |
| Đội hình 5 Agent | **28.010** team-map, **27.382** có nhãn thắng/thua |
| Người chơi đủ điều kiện | **2.724** (≥10 ván, ≥100 round) |
| Phân cụm | **k = 3**, silhouette = **0,202**, bootstrap ARI = **0,966** |
| Luật kết hợp | **580 luật** trên 7 bản đồ |

Ba nhóm người chơi:

- **C0 — Mở giao tranh · Sát thương cao** (772 người): First kills/round, ACS, Kills/round cao nhất.
- **C1 — Chết nhiều · Hiệu quả thấp** (871 người): K/D, ACS, ADR thấp nhất; Deaths/round cao.
- **C2 — Ít chết · Hiệu quả cao** (1.081 người): Assists/round, K/D, HS% cao; Deaths/round thấp.

Phát hiện chính: các tổ hợp Agent rất phổ biến theo map (Icebox gần như cố định Viper–Sage–Sova), nhưng **tỷ lệ thắng của các tổ hợp phổ biến phần lớn không khác 50% có ý nghĩa thống kê**. Đồng xuất hiện không chứng minh hiệu quả.

Xem báo cáo đầy đủ:

- [`reports/01_kiem_tra_du_lieu.md`](reports/01_kiem_tra_du_lieu.md) — kiểm tra chất lượng dữ liệu, lý do loại KAST.
- [`reports/02_du_lieu_khai_pha.md`](reports/02_du_lieu_khai_pha.md) — nhật ký xây dựng tập dữ liệu.
- [`reports/03_ket_qua_so_bo.md`](reports/03_ket_qua_so_bo.md) — kết quả, bảng số liệu và diễn giải.
- [`reports/04_kiem_tra_chat_luong.md`](reports/04_kiem_tra_chat_luong.md) — kiểm tra bất biến dữ liệu đầu ra.

## 3. Cấu trúc dự án

```
.
├── data/
│   ├── raw/valorant.sqlite          # dữ liệu gốc, không commit
│   └── processed/                   # dữ liệu khai phá sinh tự động
├── src/valorant_mining/
│   ├── cleaning.py                  # làm sạch, ánh xạ thắng/thua, đội hình
│   ├── features.py                  # player_features
│   ├── clustering.py                # K-Means, chọn k, độ ổn định, hồ sơ cụm
│   ├── rules.py                     # FP-Growth, luật kết hợp, hiệu suất đội hình
│   ├── audit.py                     # kiểm tra dữ liệu
│   ├── report.py                    # sinh báo cáo kết quả
│   └── plotting.py                  # hình
├── scripts/
│   ├── 00_audit_data.py
│   ├── 01_build_datasets.py
│   ├── 02_cluster_players.py
│   ├── 03_agent_rules.py
│   ├── 04_make_report.py
│   └── 05_validate.py
├── notebooks/                       # notebook trình bày
├── outputs/tables/                  # bảng kết quả
├── reports/                         # báo cáo markdown + figures
└── docs/ke_hoach.md                 # kế hoạch 10 ngày
```

## 4. Cài đặt

Yêu cầu: Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dữ liệu gốc được đặt tại `data/raw/valorant.sqlite`. File này không được commit vì dung lượng ~76 MB. Nếu clone dự án, hãy copy file vào đúng đường dẫn trên.

## 5. Chạy toàn bộ pipeline

```bash
make all
```

Hoặc chạy từng bước:

```bash
python scripts/00_audit_data.py        # kiểm tra dữ liệu + hình audit
python scripts/01_build_datasets.py    # clean_games, team_compositions, player_features
python scripts/02_cluster_players.py   # K-Means + hình cụm
python scripts/03_agent_rules.py       # FP-Growth theo bản đồ + hình
python scripts/04_make_report.py       # reports/03_ket_qua_so_bo.md
python scripts/05_validate.py          # kiểm tra bất biến dữ liệu đầu ra
```

Thời gian chạy toàn bộ khoảng 1–3 phút trên laptop thông thường (tùy tốc độ đọc SQLite và bootstrap).

## 6. Phương pháp

### 6.1. Làm sạch

- Giữ `PlayerID` làm khóa, không dùng `PlayerName`.
- Bỏ dòng thiếu PlayerID, Agent hoặc đội.
- Mỗi đội phải có đúng 5 người chơi và 5 Agent khác nhau; mỗi ván phải có đúng 2 đội như vậy.
- Số round lấy từ `RoundHistory` nếu có; nếu không, lấy tổng round của bảng `Games`. Ván có RoundHistory mâu thuẫn bị loại.
- Chỉ giữ 7 bản đồ thi đấu; loại `TBD`.
- Không thay KAST thiếu bằng 0; loại KAST khỏi mô hình.
- Nhãn thắng/thua được suy ra từ điểm cuối và ánh xạ đội qua RoundHistory.

### 6.2. Phân cụm người chơi

- Tổng hợp theo PlayerID, chia theo **tổng số round** để không ưu tiên ván overtime.
- Biến: Kills/round, Deaths/round, Assists/round, K/D, ACS, ADR, FK/round, FD/round, multi-kill/round, độ lệch chuẩn ACS, HS%.
- Winsorize 1%–99%, sau đó StandardScaler.
- K-Means với k = 2..8, chọn k trong khoảng 3–5 theo silhouette và khả năng diễn giải.
- Đánh giá: silhouette, Calinski–Harabasz, Davies–Bouldin, elbow, bootstrap ARI (30 lần), so sánh Ward.
- Tỷ lệ vai trò Agent chỉ dùng để mô tả cụm, **không** đưa vào mô hình.

### 6.3. Luật kết hợp Agent

- Mỗi đội trong một ván là một “giỏ” 5 Agent, không có thứ tự.
- FP-Growth, tối đa 3 Agent/itemset, support tối thiểu `max(12 đội, 2%)` mỗi map.
- Giữ luật confidence ≥ 0,40 và lift ≥ 1,05; bảng báo cáo lọc thêm n ≥ 30, confidence ≥ 0,5.
- Báo cáo support, confidence, lift, số đội hình và tỷ lệ thắng khi có vế trái (kèm Wilson 95%).
- Phân tích riêng từng map; so sánh patch lớn và tỷ lệ chọn Agent.

## 7. Notebook

- `notebooks/01_tong_quan_du_lieu.ipynb` — khảo sát dữ liệu và làm sạch.
- `notebooks/02_phan_cum_nguoi_choi.ipynb` — phân cụm, chọn k, diễn giải.
- `notebooks/03_luat_ket_hop_agent.ipynb` — luật kết hợp theo map và hiệu suất đội hình.

Các notebook dùng lại module trong `src/`, nên kết quả luôn khớp với pipeline.

## 8. Giới hạn

- Dữ liệu chỉ đến **2022-01-08**, không đại diện meta hiện tại.
- KAST thiếu **97,9%**, không dùng.
- Không có vũ khí, tọa độ giao tranh, kỹ năng Agent, kill log.
- Chỉ 14.005/15.888 ván đủ điều kiện đội hình; có thể có thiên lệch chọn mẫu.
- Breeze/Fracture ít trận; luật hai map này kém ổn định.
- Luật kết hợp chỉ là đồng xuất hiện, không phải nhân quả.
- Phân cụm chịu ảnh hưởng của Agent role; chưa tách hoàn toàn “phong cách” khỏi “vai trò”.
- Các so sánh tỷ lệ thắng chưa hiệu chỉnh multiple comparisons.

## 9. Hướng phát triển

1. Hold-out theo thời gian cho các đội hình có win rate cao.
2. Mô hình thắng/thua có kiểm soát map, patch, đội (logistic/hierarchical).
3. Phân cụm trong từng nhóm vai trò để tách phong cách khỏi role.
4. PrefixSpan cho chuỗi round/mua sắm.
5. Dashboard so sánh luật giữa map và patch.

## 10. Ghi công dữ liệu

Dữ liệu được cung cấp trong `valorant.sqlite`, gồm các trận đấu chuyên nghiệp từ tháng 5/2020 đến tháng 1/2022. Dự án không tải lại dữ liệu từ nguồn ngoài.
