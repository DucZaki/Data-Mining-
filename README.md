# Valorant Competitive Data Mining

**Phân cụm người chơi theo phong cách thi đấu và khai phá tổ hợp Agent theo bản đồ**

Dự án khai phá dữ liệu trên các trận đấu Valorant chuyên nghiệp giai đoạn **05/2020 – 01/2022**. Mục tiêu không chỉ là mô tả dữ liệu, mà là xây dựng các kết quả có thể kiểm chứng, có kiểm định thống kê và có thể tái lập bằng một lệnh.

[GitHub](https://github.com/DucZaki/Data-Mining-) · [Báo cáo kết quả](reports/03_ket_qua_so_bo.md) · [Kiểm tra chất lượng](reports/04_kiem_tra_chat_luong.md)

> **Tóm tắt nhanh:** 14.005 ván sạch · 28.010 đội hình 5 Agent · 2.599 người chơi · 3 cụm · 580 luật kết hợp · 473 đội hình được kiểm định.

---

## 1. Bài toán và phạm vi

Dự án trả lời bốn câu hỏi:

1. Có những nhóm người chơi nào dựa trên khả năng hạ gục, hỗ trợ, mở giao tranh và độ ổn định?
2. Agent nào thường xuất hiện cùng nhau trên từng bản đồ?
3. Những tổ hợp Agent phổ biến có hiệu suất thắng khác nhau không?
4. Kết quả thay đổi thế nào giữa các bản đồ và các phiên bản game?

| Bài toán | Đơn vị phân tích | Quy mô | Phương pháp chính |
|---|---|---|---|
| Phân cụm người chơi | Một `PlayerID` | 2.599 người chơi | PCA + K-Means, đánh giá bằng silhouette, bootstrap ARI và Ward |
| Luật kết hợp Agent | Một đội trong một ván | 28.010 đội hình | FP-Growth theo từng bản đồ, lọc support/confidence/lift |
| Kiểm định hiệu quả | Một đội hình 5 Agent | 27.382 đội hình có nhãn thắng/thua | Wilson CI, Fisher exact, hiệu chỉnh Benjamini–Hochberg |

**Phạm vi dữ liệu:** 4 bảng gốc `Matches`, `Games`, `Game_Scoreboard`, `Game_Rounds`; 7 bản đồ thi đấu Ascent, Bind, Breeze, Fracture, Haven, Icebox, Split. Bản đồ `TBD` bị loại.

---

## 2. Kết quả nổi bật

| Hạng mục | Kết quả |
|---|---|
| Ván còn sau làm sạch | **14.005 / 15.888** ván |
| Đội hình 5 Agent | **28.010** team-map, **27.382** có nhãn thắng/thua |
| Người chơi đủ điều kiện | **2.599** (≥10 ván, ≥100 round, độ phủ ACS/ADR/HS ≥80%) |
| Phân cụm | **k = 3**, silhouette = **0,278**, bootstrap ARI = **0,954**, Ward ARI = **0,354** |
| Luật kết hợp | **580 luật** trên 7 bản đồ; **17** luật còn q < 0,05 sau BH |
| Đội hình kiểm định | **473** đội hình đủ n ≥ 8; **3** còn khác biệt sau FDR |

### 2.1. Ba nhóm người chơi

| Cụm | Tên diễn giải | Số người | Đặc điểm chính | Win rate* |
|---|---|---:|---|---:|
| C0 | Mở giao tranh · Sát thương cao | 760 | First kills/round, ACS, Kills/round và multi-kill cao nhất; assists thấp | 48,6% |
| C1 | Chết nhiều · Hiệu quả thấp | 849 | K/D, ACS, ADR thấp nhất; Deaths/round và First deaths/round cao | 37,6% |
| C2 | Ít chết · Hiệu quả cao | 990 | Assists/round, K/D, HS% cao; Deaths/round thấp | 52,6% |

\* Win rate trung bình theo người chơi trong cụm, không phải xác suất thắng của cả cụm.

**Cách đọc:** silhouette **0,278** là mức trung bình, không phải bằng chứng về ba cụm tách biệt hoàn toàn. Silhouette cao nhất ở **k = 2 (0,358)**, nhưng k = 3 được chọn vì mục tiêu 3–5 nhóm và ba chân dung có thể diễn giải. Kết quả cũng phụ thuộc thuật toán (Ward ARI 0,354) và tập biến (7 biến rút gọn cho ARI 0,473), nên đây là **mô tả khám phá**, không phải chân lý.

Cụm C0 dùng Agent Duelist ở khoảng **69%** số ván. Vì vậy “phong cách” trong dữ liệu này chịu ảnh hưởng mạnh bởi vai trò Agent; không nên gọi C0 là “Duelist” hay C2 là “IGL” như một kết luận.

### 2.2. Meta Agent theo bản đồ

Các tổ hợp phổ biến thể hiện meta rất rõ:

- **Icebox:** Viper–Sage–Sova gần như cố định.
- **Bind:** Brimstone–Viper–Skye.
- **Haven:** Cypher–Omen–Sova.
- **Split:** Astra–Viper–Skye.
- **Ascent:** Kayo–Astra–Jett/Killjoy.
- **Breeze:** Cypher–Sova–Viper.
- **Fracture:** Breach–Cypher–Raze (ít trận, độ tin cậy thấp hơn).

Tuy nhiên, **đồng xuất hiện không chứng minh hiệu quả**. Sau kiểm định Fisher và hiệu chỉnh BH, chỉ **3/473** đội hình còn khác biệt có ý nghĩa. Ví dụ trên Icebox, đội hình Killjoy–Sage–Sova–Jett–Viper đạt 55,9% (q = 0,024), trong khi đội hình thay bằng Reyna đạt 46,5% (q = 0,510). Đây là quan hệ quan sát, chưa kiểm soát chất lượng đội, patch và lựa chọn đội hình.

---

## 3. Cấu trúc dự án

```text
.
├── data/
│   ├── raw/valorant.sqlite          # dữ liệu gốc, không commit (~76 MB)
│   ├── processed/                   # dữ liệu sinh bởi pipeline, không commit
│   └── README.md                    # mô tả các bảng gốc
├── src/valorant_mining/
│   ├── cleaning.py                  # làm sạch, ánh xạ thắng/thua, đội hình
│   ├── features.py                  # hồ sơ người chơi theo round
│   ├── clustering.py                # PCA + K-Means, chọn k, độ ổn định
│   ├── rules.py                     # FP-Growth, luật kết hợp, hiệu suất đội hình
│   ├── audit.py                     # kiểm tra dữ liệu
│   ├── report.py                    # sinh báo cáo kết quả
│   └── plotting.py                  # hình audit, cụm, luật
├── scripts/
│   ├── 00_audit_data.py
│   ├── 01_build_datasets.py
│   ├── 02_cluster_players.py
│   ├── 03_agent_rules.py
│   ├── 04_make_report.py
│   └── 05_validate.py
├── notebooks/
│   ├── 01_tong_quan_du_lieu.ipynb
│   ├── 02_phan_cum_nguoi_choi.ipynb
│   ├── 03_luat_ket_hop_agent.ipynb
│   └── 04_dashboard_truc_quan.ipynb
├── outputs/tables/                  # bảng kết quả
├── reports/                         # báo cáo markdown + figures
├── docs/ke_hoach.md                 # kế hoạch triển khai
├── Makefile
├── requirements.txt
└── pyproject.toml
```

### Luồng chạy

```text
SQLite
  │
  ▼
00_audit_data ──► 01_build_datasets ──► 02_cluster_players
                         │
                         └──────────► 03_agent_rules
                                              │
                                              ▼
                                     04_make_report
                                              │
                                              ▼
                                     05_validate
```

---

## 4. Cài đặt và chạy

### Yêu cầu

- Python **3.11+**
- Dữ liệu gốc tại `data/raw/valorant.sqlite`

### Cài đặt

```bash
git clone https://github.com/DucZaki/Data-Mining-.git valorant-mining
cd valorant-mining

python3 -m venv .venv
source .venv/bin/activate

make setup
# hoặc: pip install -r requirements.txt
```

Nếu chưa có dữ liệu, copy file `valorant.sqlite` vào `data/raw/`. File này không được commit vì dung lượng khoảng 76 MB.

### Chạy toàn bộ pipeline

```bash
make all
```

Pipeline lần lượt chạy:

| Bước | Lệnh | Đầu ra chính |
|---|---|---|
| 1 | `make audit` | `reports/01_kiem_tra_du_lieu.md`, hình audit |
| 2 | `make build` | `clean_games`, `team_compositions`, `player_features`, `player_attrition` |
| 3 | `make cluster` | cụm người chơi, bảng đánh giá, hình PCA |
| 4 | `make rules` | luật kết hợp theo map, bảng đội hình, hình |
| 5 | `make report` | `reports/03_ket_qua_so_bo.md` |
| 6 | `make validate` | `reports/04_kiem_tra_chat_luong.md` |

Thời gian chạy khoảng **1–2 phút** trên laptop thông thường. Kết quả được cố định bằng `random_state`, nên chạy lại cho cùng số liệu.

> `make clean` sẽ xoá dữ liệu đã xử lý, bảng kết quả và hình. Chỉ dùng khi muốn chạy lại từ đầu.

---

## 5. Phương pháp

### 5.1. Làm sạch dữ liệu

- Giữ `PlayerID` làm khóa, không dùng `PlayerName`.
- Bỏ dòng thiếu PlayerID, Agent hoặc đội.
- Mỗi đội phải có đúng 5 người chơi và 5 Agent khác nhau; mỗi ván phải có đúng 2 đội như vậy.
- Số round lấy từ `RoundHistory` nếu có; nếu không, lấy tổng round của bảng `Games`. Ván có RoundHistory mâu thuẫn bị loại.
- Chỉ giữ 7 bản đồ thi đấu; loại `TBD`.
- Loại các ván có tổng round ngoài khoảng **13–40** (4 ván 42 round).
- Không thay KAST thiếu bằng 0; loại KAST khỏi mô hình vì thiếu 97,9%.
- Nhãn thắng/thua được suy ra từ điểm cuối và ánh xạ đội qua RoundHistory; `scripts/05_validate.py` đối chiếu lại với cột gốc `Games.Winner`.

### 5.2. Phân cụm người chơi

- Tổng hợp theo `PlayerID`, chia theo **tổng số round** để không ưu tiên ván overtime.
- Biến đầu vào: Kills/round, Deaths/round, Assists/round, K/D, ACS, ADR, First kills/round, First deaths/round, multi-kill/round, độ lệch chuẩn ACS, HS%.
- ACS/ADR/HS% chỉ lấy trung bình trên các ván có giá trị, không thay giá trị thiếu bằng 0. Người chơi có độ phủ dưới 80% bị loại.
- Winsorize 1%–99%, sau đó `StandardScaler`.
- Giảm đa cộng tuyến bằng **PCA trước K-Means**: giữ các thành phần giải thích ≥80% phương sai (3 thành phần, 82,1%). Chân dung cụm vẫn mô tả bằng 11 biến gốc.
- K-Means với `k = 2..8`; chọn k trong khoảng 3–5 theo silhouette và khả năng diễn giải.
- Đánh giá: silhouette, Calinski–Harabasz, Davies–Bouldin, elbow, bootstrap ARI (30 lần), so sánh Ward; bảng độ nhạy với 11 biến gốc và 7 biến rút gọn.
- Tỷ lệ vai trò Agent chỉ dùng để mô tả cụm, **không** đưa vào mô hình.

### 5.3. Luật kết hợp Agent

- Mỗi đội trong một ván là một “giỏ” 5 Agent, không có thứ tự.
- FP-Growth, tối đa 3 Agent/itemset, support tối thiểu `max(12 đội, 2%)` cho mỗi map.
- Giữ luật confidence ≥ 0,40 và lift ≥ 1,05; bảng báo cáo lọc thêm n ≥ 30 và confidence ≥ 0,5.
- Báo cáo support, confidence, lift, số đội hình và tỷ lệ thắng khi có vế trái (kèm Wilson 95%).
- So sánh win rate với phần còn lại của cùng map bằng Fisher exact; hiệu chỉnh Benjamini–Hochberg cho toàn bộ luật và toàn bộ đội hình.
- Phân tích riêng từng map; so sánh patch lớn và tỷ lệ chọn Agent.

### 5.4. Kiểm định và kiểm tra chất lượng

- 19 kiểm tra bất biến dữ liệu đầu ra, tất cả PASS.
- Nhãn thắng/thua khớp `Games.Winner`: **27.382 đội hình / 13.691 ván, 0 lệch**.
- Độ phủ ACS/ADR/HS của mọi người chơi còn lại đều ≥80%.
- FDR được áp dụng cho cả 580 luật và 473 đội hình; kết quả vẫn được xem là khám phá vì chưa có hold-out theo thời gian.

---

## 6. Notebook và báo cáo

### Báo cáo

- [`reports/01_kiem_tra_du_lieu.md`](reports/01_kiem_tra_du_lieu.md) — kiểm tra chất lượng dữ liệu, lý do loại KAST.
- [`reports/02_du_lieu_khai_pha.md`](reports/02_du_lieu_khai_pha.md) — nhật ký xây dựng tập dữ liệu khai phá.
- [`reports/03_ket_qua_so_bo.md`](reports/03_ket_qua_so_bo.md) — kết quả, bảng số liệu và diễn giải.
- [`reports/04_kiem_tra_chat_luong.md`](reports/04_kiem_tra_chat_luong.md) — kiểm tra bất biến dữ liệu đầu ra.

### Notebook

- `notebooks/01_tong_quan_du_lieu.ipynb` — khảo sát dữ liệu và làm sạch.
- `notebooks/02_phan_cum_nguoi_choi.ipynb` — phân cụm, chọn k, diễn giải.
- `notebooks/03_luat_ket_hop_agent.ipynb` — luật kết hợp theo map và hiệu suất đội hình.
- `notebooks/04_dashboard_truc_quan.ipynb` — dashboard đọc kết quả có sẵn; không chạy lại mô hình. Cần chạy `make all` trước.

Các notebook dùng lại module trong `src/`, nên kết quả luôn khớp với pipeline. Hình được lưu tại `reports/figures/`; bảng kết quả tại `outputs/tables/`.

---

## 7. Giới hạn

- Dữ liệu chỉ đến **2022-01-08**, không đại diện meta hiện tại.
- KAST thiếu **97,9%**, không dùng.
- Không có dữ liệu vũ khí, tọa độ giao tranh, kỹ năng Agent hoặc kill log.
- Chỉ **14.005/15.888 ván** đủ điều kiện đội hình; có thể có thiên lệch chọn mẫu.
- **126 người chơi** bị loại vì độ phủ ADR/HS dưới 80%; thiếu dữ liệu có thể không ngẫu nhiên.
- Breeze/Fracture ít trận; luật của hai map này kém ổn định.
- Luật kết hợp chỉ là đồng xuất hiện, không phải nhân quả.
- Phân cụm chịu ảnh hưởng của Agent role; chưa tách hoàn toàn “phong cách” khỏi “vai trò”. Kết quả thay đổi khi dùng tập biến rút gọn (ARI 0,473 so với mô hình chính).
- Đã kiểm định Fisher và hiệu chỉnh BH, nhưng đây vẫn là phân tích khám phá; chưa có hold-out theo thời gian và chưa kiểm soát chất lượng đội.

---

## 8. Hướng phát triển

1. Hold-out theo thời gian cho các đội hình có win rate cao.
2. Mô hình thắng/thua có kiểm soát map, patch, đội (logistic/hierarchical).
3. Phân cụm trong từng nhóm vai trò để tách phong cách khỏi role.
4. PrefixSpan cho chuỗi round/mua sắm.
5. Dashboard so sánh luật giữa map và patch.

---

## 9. Dữ liệu và tham khảo

### Dữ liệu

Dữ liệu được cung cấp trong `valorant.sqlite`, gồm các trận đấu chuyên nghiệp từ tháng 5/2020 đến tháng 1/2022. Dự án không tải lại dữ liệu từ nguồn ngoài.

| Bảng | Ý nghĩa |
|---|---|
| `Matches` | trận, ngày, patch, giải, thể thức |
| `Games` | từng map trong trận, điểm, thông tin mua sắm |
| `Game_Scoreboard` | một dòng / người chơi / map, gồm Agent và chỉ số |
| `Game_Rounds` | lịch sử round dạng chuỗi (Python literal) |

### Tham khảo phương pháp

- scikit-learn — K-Means, PCA và các metric đánh giá cụm: <https://scikit-learn.org/stable/modules/clustering.html>
- mlxtend — FP-Growth và association rules: <https://rasbt.github.io/mlxtend/user_guide/frequent_patterns/fpgrowth/>
- Benjamini, Y., & Hochberg, Y. (1995). *Controlling the false discovery rate: a practical and powerful approach to multiple testing.* Journal of the Royal Statistical Society: Series B, 57(1), 289–300. <https://doi.org/10.1111/j.2517-6161.1995.tb02031.x>
