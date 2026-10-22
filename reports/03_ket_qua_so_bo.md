# Kết quả khai phá sơ bộ

> Báo cáo được sinh tự động từ các bảng trong `outputs/tables/`. Số liệu dưới đây là kết quả trên **14.005 ván** còn lại sau làm sạch, không phải toàn bộ 15.888 ván gốc.

## 0. Tóm tắt điều hành

- **Phân cụm:** 2,724 người chơi đủ ≥10 ván và ≥100 round. Chọn **k = 3** cụm; silhouette = **0.202**, độ ổn định bootstrap (ARI) = **0.966**.
- **Luật kết hợp:** 28,010 đội hình 5 Agent trên 7 bản đồ; 27,382 đội hình có nhãn thắng/thua; **580 luật** vượt ngưỡng support/confidence/lift.
- **Phát hiện chính:** các tổ hợp Agent phổ biến mang tính meta rất rõ theo map (ví dụ Icebox gần như cố định Viper–Sage–Sova), nhưng **tỷ lệ thắng của các tổ hợp phổ biến phần lớn không khác 50% một cách có ý nghĩa thống kê**. Đồng xuất hiện không đồng nghĩa với hiệu quả.
- **Lưu ý phương pháp:** silhouette cao nhất ở k = 2 (0.282); nhóm chọn k = 3 vì khung phân tích đặt trước 3–5 cụm và k = 3 tách được ba kiểu hồ sơ có thể diễn giải. Đây là lựa chọn có chủ đích, cần ghi rõ trong báo cáo.

## 1. Bài toán 1 — Phân cụm người chơi

### 1.1. Dữ liệu đầu vào

| Bước | Số người chơi |
|---|---|
| Người chơi trong bảng điểm sạch | 7476 |
| Đủ ≥10 ván | 2724 |
| Đủ ≥100 round | 2724 |
| Đủ biến mô hình | 2724 |

Biến dùng cho mô hình: Kills/round, Deaths/round, Assists/round, K/D, ACS, ADR, First kills/round, First deaths/round, multi-kill/round, độ lệch chuẩn ACS, HS%. Các biến được winsorize 1%–99% trước khi chuẩn hóa bằng StandardScaler.

KAST bị loại vì thiếu 97,9% và không thể thay bằng 0.

### 1.2. Chọn số cụm

| k | inertia | silhouette | calinski_harabasz | davies_bouldin |
|---|---|---|---|---|
| 2 | 20153 | 0.28 | 1325 | 1.32 |
| 3 | 16928 | 0.20 | 1048 | 1.54 |
| 4 | 15156 | 0.19 | 886 | 1.49 |
| 5 | 13958 | 0.17 | 779 | 1.55 |
| 6 | 13181 | 0.16 | 692 | 1.61 |
| 7 | 12551 | 0.15 | 628 | 1.58 |
| 8 | 11959 | 0.15 | 584 | 1.59 |

- Silhouette cao nhất ở **k = 2** (0.282), nhưng đây là phương án chỉ chia người chơi thành hai nhóm rất rộng.
- Trong khoảng 3–5 cụm, **k = 3** có silhouette cao nhất (0.202) và cho ba chân dung khác nhau về hành vi đo được.
- Độ ổn định bootstrap 80% (30 lần): ARI trung bình **0.966**, thấp nhất **0.876**. Các cụm gần như giữ nguyên khi lấy mẫu lại.
- So sánh với Hierarchical Ward (cùng k): ARI = **0.319**. Hai thuật toán không hoàn toàn đồng nhất, nên cấu trúc cụm chỉ nên được xem là một mô tả khám phá, không phải chân lý.

### 1.3. Chân dung cụm

| Cụm | Tên gợi ý | n | Kills/R | Deaths/R | Assists/R | K/D | ACS | ADR | FK/R | FD/R | Multi/R | SD ACS | Win rate | Duelist share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C0 | Mở giao tranh · Sát thương cao | 772 | 0.79 | 0.73 | 0.21 | 1.09 | 228.40 | 143.50 | 0.15 | 0.13 | 0.20 | 64.10 | 48.7% | 69.4% |
| C1 | Chết nhiều · Hiệu quả thấp | 871 | 0.60 | 0.74 | 0.26 | 0.82 | 175.50 | 109.10 | 0.07 | 0.09 | 0.13 | 49.50 | 36.9% | 14.1% |
| C2 | Ít chết · Hiệu quả cao | 1081 | 0.70 | 0.69 | 0.28 | 1.02 | 200.30 | 128.50 | 0.08 | 0.08 | 0.17 | 55.40 | 52.4% | 12.5% |

Diễn giải dựa trên z-score:

- **C0 — Mở giao tranh · Sát thương cao** (772 người): First kills/round, ACS, Kills/round và multi-kill cao nhất; assists thấp. Đây là nhóm tạo áp lực mở giao tranh, nhưng cũng chết ở mức trên trung bình. Khoảng **69.4%** số ván của nhóm dùng Agent Duelist — cần nhấn mạnh đây là đặc điểm mô tả, không phải nhãn vai trò.
- **C1 — Chết nhiều · Hiệu quả thấp** (871 người): Kills/round, ACS, ADR và K/D thấp nhất; Deaths/round và First deaths/round cao. Win rate chỉ **36.9%**, thấp hơn hai nhóm còn lại. Có thể đây là nhóm người chơi bị kéo xuống bởi đội yếu hoặc mẫu trận thua, không thể quy kết chỉ do phong cách cá nhân.
- **C2 — Ít chết · Hiệu quả cao** (1081 người): Assists/round, K/D và HS% cao; Deaths/round, First deaths/round thấp. ACS chỉ ở mức trung bình, cho thấy nhóm này tạo giá trị bằng độ ổn định và hỗ trợ hơn là số kill thô. Win rate **52.4%**.

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

| Map | Luật | n đội hình | Support | Confidence | Lift | Win rate khi có vế trái |
|---|---|---|---|---|---|---|
| Ascent | kayo → astra, jett | 248 | 0.04 | 0.71 | 2.66 | 0.53 |
| Ascent | kayo, killjoy → astra | 205 | 0.03 | 0.86 | 2.64 | 0.52 |
| Ascent | jett, kayo → astra | 248 | 0.04 | 0.81 | 2.48 | 0.53 |
| Ascent | killjoy, skye → astra | 544 | 0.08 | 0.80 | 2.44 | 0.51 |
| Bind | brimstone, viper → skye | 374 | 0.06 | 0.79 | 2.88 | 0.50 |
| Bind | brimstone, skye → viper | 374 | 0.06 | 0.75 | 2.77 | 0.51 |
| Bind | jett, viper → astra | 356 | 0.06 | 0.70 | 2.60 | 0.51 |
| Bind | jett, skye → astra | 420 | 0.07 | 0.66 | 2.43 | 0.51 |
| Breeze | kayo → cypher, sova | 52 | 0.04 | 0.63 | 1.29 | 0.42 |
| Breeze | kayo, sova → cypher | 52 | 0.04 | 0.68 | 1.19 | 0.43 |
| Breeze | chamber → sova, viper | 56 | 0.05 | 1.00 | 1.19 | 0.52 |
| Breeze | chamber → sova | 56 | 0.05 | 1.00 | 1.18 | 0.52 |
| Fracture | raze → breach, cypher | 36 | 0.18 | 0.62 | 1.52 | 0.47 |
| Fracture | breach, raze → cypher | 36 | 0.18 | 0.63 | 1.41 | 0.47 |
| Fracture | raze → cypher | 36 | 0.18 | 0.62 | 1.38 | 0.47 |
| Fracture | raze → astra, breach | 37 | 0.19 | 0.64 | 1.36 | 0.47 |
| Haven | astra, sage → skye | 148 | 0.02 | 0.61 | 2.71 | 0.56 |
| Haven | killjoy, sage → skye | 199 | 0.03 | 0.58 | 2.58 | 0.59 |
| Haven | skye, sova → astra | 658 | 0.11 | 0.77 | 2.34 | 0.48 |
| Haven | sage, skye → killjoy | 199 | 0.03 | 0.78 | 2.34 | 0.61 |
| Icebox | omen → killjoy | 372 | 0.11 | 0.54 | 1.10 | 0.48 |
| Icebox | reyna, sage → viper | 1011 | 0.29 | 0.89 | 1.08 | 0.46 |
| Icebox | jett, omen → killjoy | 293 | 0.08 | 0.53 | 1.08 | 0.47 |
| Icebox | reyna → sova, viper | 1181 | 0.34 | 0.82 | 1.07 | 0.47 |
| Split | astra, viper → skye | 303 | 0.07 | 0.61 | 3.38 | 0.51 |
| Split | astra, skye → viper | 303 | 0.07 | 0.58 | 3.19 | 0.49 |
| Split | jett, viper → skye | 198 | 0.05 | 0.54 | 3.01 | 0.52 |
| Split | skye, viper → astra | 303 | 0.07 | 0.80 | 2.55 | 0.55 |

Đọc bảng: `Support` là tỷ lệ đội hình chứa toàn bộ Agent trong luật; `Confidence` là xác suất có vế phải khi đã có vế trái; `Lift` > 1 nghĩa là hai vế xuất hiện cùng nhau nhiều hơn so với kỳ vọng độc lập. Các map nhỏ (Breeze, Fracture) có n nhỏ, không nên so sánh trực tiếp độ lớn lift với Ascent/Haven.

### 2.3. Các cặp/tổ hợp có support cao nhất

| Map | Luật | n | Support | Confidence | Lift |
|---|---|---|---|---|---|
| Ascent | cypher → omen | 1993 | 29.3% | 82.7% | 1.30 |
| Ascent | omen → cypher | 1993 | 29.3% | 46.0% | 1.30 |
| Bind | omen → sova | 2356 | 40.0% | 89.5% | 1.05 |
| Bind | sova → omen | 2356 | 40.0% | 46.9% | 1.05 |
| Breeze | kayo → sova, viper | 76 | 6.5% | 91.6% | 1.09 |
| Breeze | kayo → sova | 76 | 6.5% | 91.6% | 1.08 |
| Fracture | viper → jett | 84 | 42.4% | 71.8% | 1.05 |
| Fracture | jett → viper | 84 | 42.4% | 62.2% | 1.05 |
| Haven | cypher → omen | 2741 | 44.1% | 71.2% | 1.17 |
| Haven | omen → cypher | 2741 | 44.1% | 72.5% | 1.17 |
| Icebox | sage, sova → viper | 2368 | 67.8% | 87.6% | 1.06 |
| Icebox | viper → sage, sova | 2368 | 67.8% | 82.3% | 1.06 |
| Split | omen → raze | 2170 | 51.4% | 83.9% | 1.05 |
| Split | raze → omen | 2170 | 51.4% | 64.6% | 1.05 |

Đây là các tổ hợp gần như “mặc định” của meta trong giai đoạn dữ liệu: ví dụ Icebox có Viper–Sage–Sova, Bind có Sova–Omen, Haven có Omen–Cypher. Support cao phản ánh mức độ phổ biến, **không** phản ánh sức mạnh.

### 2.4. Tỷ lệ chọn Agent theo map

| Map | Agent | Tỷ lệ chọn |
|---|---|---|
| Ascent | sova | 95.6% |
| Ascent | jett | 79.4% |
| Ascent | omen | 63.6% |
| Bind | sova | 85.1% |
| Bind | raze | 75.2% |
| Bind | cypher | 50.1% |
| Breeze | viper | 99.5% |
| Breeze | jett | 93.3% |
| Breeze | sova | 84.7% |
| Fracture | breach | 90.4% |
| Fracture | jett | 68.2% |
| Fracture | viper | 59.1% |
| Haven | sova | 85.3% |
| Haven | jett | 80.0% |
| Haven | cypher | 61.9% |
| Icebox | sova | 91.0% |
| Icebox | jett | 90.7% |
| Icebox | sage | 84.6% |
| Split | raze | 79.6% |
| Split | jett | 61.2% |
| Split | omen | 61.2% |

### 2.5. So sánh theo phiên bản lớn

| Giai đoạn | Agent được chọn nhiều |
|---|---|
| Patch 1.x | omen (88.4%), sova (73.2%), cypher (71.6%), jett (69.8%), raze (48.2%) |
| Patch 2.x | sova (76.9%), jett (68.6%), omen (57.0%), raze (53.1%), killjoy (42.5%) |
| Patch 3.x | jett (78.5%), sova (76.4%), astra (48.3%), viper (47.3%), killjoy (42.2%) |

Bảng này cho thấy meta thay đổi theo patch; vì vậy mọi kết luận “Agent X mạnh” cần gắn với một giai đoạn cụ thể.

## 3. Tổ hợp phổ biến có thắng nhiều hơn không?

### 3.1. Các đội hình 5 Agent xuất hiện nhiều nhất

| Map | Đội hình | n | Win rate | CI 95% |
|---|---|---|---|---|
| Icebox | jett + reyna + sage + sova + viper | 896 | 46.5% | 43.3%–49.8% |
| Icebox | jett + killjoy + sage + sova + viper | 883 | 55.9% | 52.7%–59.2% |
| Haven | cypher + jett + omen + phoenix + sova | 617 | 48.9% | 45.0%–52.9% |
| Bind | cypher + jett + omen + raze + sova | 544 | 52.0% | 47.8%–56.2% |
| Ascent | astra + jett + killjoy + skye + sova | 462 | 54.3% | 49.8%–58.8% |
| Split | breach + cypher + jett + omen + raze | 428 | 48.6% | 43.9%–53.3% |
| Haven | breach + cypher + jett + omen + sova | 424 | 46.0% | 41.3%–50.7% |
| Breeze | cypher + jett + skye + sova + viper | 416 | 53.6% | 48.8%–58.3% |
| Haven | cypher + jett + omen + reyna + sova | 411 | 49.9% | 45.1%–54.7% |
| Ascent | jett + killjoy + omen + reyna + sova | 393 | 45.8% | 40.9%–50.7% |
| Ascent | cypher + jett + omen + reyna + sova | 368 | 49.5% | 44.4%–54.5% |
| Ascent | breach + cypher + jett + omen + sova | 365 | 43.6% | 38.6%–48.7% |

Ví dụ đáng chú ý trên Icebox: hai đội hình phổ biến nhất chỉ khác nhau ở vị trí Reyna/Killjoy, nhưng tỷ lệ thắng quan sát được là **46.5% (n = 896)** so với **55.9% (n = 883)**. Khoảng tin cậy 95% của hai tỷ lệ này không chồng lên nhau, nhưng đây vẫn là quan hệ quan sát: đội mạnh có thể tự chọn đội hình tốt hơn.

### 3.2. Các đội hình có khoảng tin cậy không chứa 50%

| Map | Đội hình | n | Win rate | CI 95% |
|---|---|---|---|---|
| Ascent | breach + cypher + omen + sage + sova | 39 | 76.9% | 61.7%–87.4% |
| Haven | cypher + jett + omen + sage + skye | 21 | 76.2% | 54.9%–89.4% |
| Haven | cypher + omen + raze + sage + sova | 54 | 74.1% | 61.1%–83.9% |
| Ascent | breach + killjoy + omen + reyna + sova | 22 | 72.7% | 51.8%–86.8% |
| Bind | astra + cypher + raze + sage + skye | 28 | 71.4% | 52.9%–84.7% |
| Bind | killjoy + omen + raze + sage + sova | 29 | 69.0% | 50.8%–82.7% |
| Haven | astra + killjoy + raze + sage + skye | 64 | 68.8% | 56.6%–78.8% |
| Icebox | jett + killjoy + raze + sage + viper | 52 | 67.3% | 53.8%–78.5% |

Đây là danh sách **khám phá**, không phải kết luận nhân quả. Có nhiều phép so sánh được thực hiện, nên một vài khoảng tin cậy “có ý nghĩa” có thể xuất hiện do ngẫu nhiên. Cần kiểm định lại trên tập hold-out hoặc mô hình có kiểm soát đội, map, patch.

## 4. Trả lời câu hỏi nghiên cứu

1. **Có những nhóm người chơi nào?** Ba nhóm: mở giao tranh/sát thương cao, chết nhiều/hiệu quả thấp, ít chết/hiệu quả cao. Độ ổn định cao (ARI 0.966), nhưng silhouette chỉ ở mức trung bình (0.202).
2. **Agent nào thường đi cùng nhau theo map?** Có cấu trúc rõ: Ascent (Kayo–Astra–Jett/Killjoy), Bind (Brimstone–Viper–Skye), Haven (Cypher–Omen–Sova), Icebox (Viper–Sage–Sova), Split (Astra–Viper–Skye), Breeze (Cypher–Sova–Viper), Fracture (Breach–Cypher–Raze).
3. **Tổ hợp phổ biến có thắng nhiều hơn?** Nhìn chung không có bằng chứng mạnh: phần lớn luật có win rate 46–55% và khoảng tin cậy chứa 50%. Một số đội hình ít phổ biến hơn có win rate cao, nhưng n nhỏ và có thể do chọn đội.
4. **Khác nhau theo map/patch?** Có. Tỷ lệ chọn Agent thay đổi theo map và theo patch lớn; một số tổ hợp chỉ tồn tại trong một giai đoạn meta.

## 5. Giới hạn

- Dữ liệu chỉ đến **2022-01-08**; meta hiện tại đã khác.
- KAST thiếu **97,9%**, không dùng trong mô hình.
- Không có dữ liệu vũ khí, tọa độ giao tranh, kỹ năng Agent, kill log.
- Chỉ **14.005/15.888 ván** có đủ 2 đội × 5 người × 5 Agent; các ván thiếu bị loại, có thể tạo thiên lệch chọn mẫu.
- Nhãn thắng/thua chỉ có cho **97.8%** đội hình.
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
