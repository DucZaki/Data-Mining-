# Kết quả khai phá sơ bộ

> Báo cáo được sinh tự động từ các bảng trong `outputs/tables/`. Số liệu dưới đây là kết quả trên **14.005 ván** còn lại sau làm sạch, không phải toàn bộ 15.888 ván gốc.

## 0. Tóm tắt điều hành

- **Phân cụm:** 2.599 người chơi đủ ≥10 ván, ≥100 round và ≥80% độ phủ ACS/ADR/HS. Chọn **k = 3** cụm; silhouette = **0.278**, độ ổn định bootstrap (ARI) = **0.954**.
- **Luật kết hợp:** 28.010 đội hình 5 Agent trên 7 bản đồ; 27.382 đội hình có nhãn thắng/thua; **580 luật** vượt ngưỡng support/confidence/lift. Sau hiệu chỉnh Benjamini–Hochberg (BH), **17/580** luật có win rate khác phần còn lại của map ở mức q < 0,05.
- **Đội hình:** trong **473** đội hình đủ n ≥ 8, chỉ **3** còn khác biệt có ý nghĩa sau BH. Đây là bằng chứng mô tả, không phải hiệu ứng nhân quả.
- **Phát hiện chính:** các tổ hợp Agent phổ biến mang tính meta rất rõ theo map (ví dụ Icebox gần như cố định Viper–Sage–Sova), nhưng **phần lớn khác biệt tỷ lệ thắng không bền sau kiểm định và hiệu chỉnh đa so sánh**. Đồng xuất hiện không đồng nghĩa với hiệu quả.
- **Lưu ý phương pháp:** silhouette cao nhất ở k = 2 (0.358); nhóm chọn k = 3 vì khung phân tích đặt trước 3–5 cụm và k = 3 tách được ba kiểu hồ sơ có thể diễn giải. Đây là **lựa chọn khám phá có chủ đích**, không phải số cụm tối ưu tuyệt đối.

## 1. Bài toán 1 — Phân cụm người chơi

### 1.1. Dữ liệu đầu vào và xử lý giá trị thiếu

| Bước | Số người chơi |
|---|---|
| Người chơi trong bảng điểm sạch | 7481 |
| Đủ ≥10 ván | 2725 |
| Đủ ≥100 round | 2725 |
| Độ phủ ACS/ADR/HS ≥80% | 2599 |
| Đủ biến mô hình | 2599 |

Biến dùng cho mô hình: Kills/round, Deaths/round, Assists/round, K/D, ACS, ADR, First kills/round, First deaths/round, multi-kill/round, độ lệch chuẩn ACS, HS%. Các biến được winsorize 1%–99% trước khi chuẩn hóa.

ACS, ADR và HS% **không được thay bằng 0** khi thiếu. Mỗi chỉ số chỉ được tính trung bình trên các ván có giá trị, với trọng số là số round của ván đó:

`ACS = Σ(ACS × rounds) / Σ(rounds có ACS)`

Người chơi có độ phủ dưới 80% ở bất kỳ chỉ số nào bị loại (**126 người**), vì khi đó trung bình không còn đại diện cho phong cách của họ. KAST vẫn bị loại vì thiếu 97,9% và không thể thay bằng 0.

### 1.2. Đa cộng tuyến và cách xử lý

Các biến combat tương quan rất mạnh; nếu đưa thẳng vào K-Means, mô hình sẽ vô tình đếm “hiệu quả combat” nhiều lần. Bảng dưới liệt kê các cặp có |r| ≥ 0,70 (ma trận đầy đủ ở `outputs/tables/feature_correlation.csv`):

| Biến A | Biến B | r |
|---|---|---|
| Kills / round | ACS | 0.97 |
| ACS | ADR | 0.95 |
| Kills / round | Multi-kill rounds / round | 0.94 |
| Kills / round | ADR | 0.92 |
| ACS | Multi-kill rounds / round | 0.92 |
| Kills / round | K/D | 0.89 |
| ADR | Multi-kill rounds / round | 0.87 |
| K/D | ACS | 0.83 |
| K/D | ADR | 0.81 |
| K/D | Multi-kill rounds / round | 0.81 |

Vì vậy mô hình chính **giảm chiều bằng PCA** trước K-Means: giữ các thành phần giải thích ≥80% phương sai, thu được **3 thành phần** và **82.1%** phương sai. Chân dung cụm vẫn được mô tả bằng 11 biến gốc để giữ khả năng diễn giải.

Ba thành phần có ý nghĩa tương đối rõ: PC1 là trục sát thương/hạ gục (kills, ACS, ADR, multi-kill, K/D), PC2 là trục chết và mở giao tranh (deaths, first deaths, assists), PC3 gần như chỉ còn HS%. Hệ số tải đầy đủ ở `outputs/tables/pca_loadings.csv`.

| Phương pháp | Số chiều | Silhouette | ARI so với mô hình chính |
|---|---|---|---|
| PCA (giữ ≥80%; 82.1% phương sai) | 3 | 0.28 | 1.00 |
| 11 biến gốc | 11 | 0.21 | 0.97 |
| 7 biến rút gọn | 7 | 0.19 | 0.47 |

Cách đọc bảng độ nhạy:

- K-Means trên 11 biến gốc cho kết quả gần với PCA (ARI = 0,968), nên PCA không tạo ra một cấu trúc hoàn toàn mới; nó chủ yếu giảm trọng số lặp của nhóm biến combat.
- Bộ 7 biến rút gọn thay đổi cụm nhiều hơn (ARI = 0,473). Điều này cho thấy **kết quả phụ thuộc vào lựa chọn biến**; không nên trình bày ba cụm như một chân lý duy nhất.
- Silhouette của các phương pháp được tính trong không gian riêng của từng phương pháp, nên chỉ nên so sánh tương đối.

### 1.3. Chọn số cụm

| k | inertia | silhouette | calinski_harabasz | davies_bouldin |
|---|---|---|---|---|
| 2 | 13724 | 0.36 | 1846 | 1.07 |
| 3 | 10664 | 0.28 | 1560 | 1.19 |
| 4 | 8905 | 0.27 | 1415 | 1.13 |
| 5 | 7725 | 0.26 | 1322 | 1.15 |
| 6 | 7032 | 0.24 | 1213 | 1.15 |
| 7 | 6433 | 0.23 | 1145 | 1.19 |
| 8 | 5972 | 0.23 | 1085 | 1.17 |

Silhouette trong bảng được tính trên không gian PCA 3 thành phần.

- Silhouette cao nhất ở **k = 2** (0.358), nhưng đây là phương án chỉ chia người chơi thành hai nhóm rất rộng.
- Trong khoảng 3–5 cụm, **k = 3** có silhouette cao nhất (**0.278**). Đây là lựa chọn có chủ đích để có ba chân dung diễn giải được, không phải k tối ưu theo silhouette.
- Độ ổn định bootstrap 80% (30 lần): ARI trung bình **0.954**, thấp nhất **0.866**. Cụm ổn định khi lấy mẫu lại, nhưng phép thử này không kiểm tra độ nhạy với thuật toán hay tập biến.
- So sánh với Hierarchical Ward (cùng k): ARI = **0.354**. Hai thuật toán **không hoàn toàn đồng nhất**, nên cấu trúc cụm chỉ nên được xem là một mô tả khám phá.

### 1.4. Chân dung cụm

| Cụm | Tên gợi ý | n | Kills/R | Deaths/R | Assists/R | K/D | ACS | ADR | FK/R | FD/R | Multi/R | SD ACS | Win rate | Duelist share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C0 | Mở giao tranh · Sát thương cao | 760 | 0.79 | 0.73 | 0.21 | 1.09 | 228.30 | 144.90 | 0.15 | 0.13 | 0.20 | 64.10 | 48.6% | 69.0% |
| C1 | Chết nhiều · Hiệu quả thấp | 849 | 0.60 | 0.74 | 0.26 | 0.82 | 175.70 | 115.10 | 0.07 | 0.10 | 0.14 | 49.80 | 37.6% | 13.6% |
| C2 | Ít chết · Hiệu quả cao | 990 | 0.70 | 0.68 | 0.28 | 1.03 | 200.90 | 131.20 | 0.08 | 0.08 | 0.17 | 55.30 | 52.6% | 12.4% |

Diễn giải dựa trên z-score:

- **C0 — Mở giao tranh · Sát thương cao** (760 người): First kills/round, ACS, Kills/round và multi-kill cao nhất; assists thấp. Đây là nhóm tạo áp lực mở giao tranh, nhưng cũng chết ở mức trên trung bình. Khoảng **69.0%** số ván của nhóm dùng Agent Duelist — đây là đặc điểm mô tả, không phải nhãn vai trò.
- **C1 — Chết nhiều · Hiệu quả thấp** (849 người): Kills/round, ACS, ADR và K/D thấp nhất; Deaths/round và First deaths/round cao. Win rate chỉ **37.6%**, thấp hơn hai nhóm còn lại. Có thể đây là nhóm người chơi bị kéo xuống bởi đội yếu hoặc mẫu trận thua, không thể quy kết chỉ do phong cách cá nhân.
- **C2 — Ít chết · Hiệu quả cao** (990 người): Assists/round, K/D và HS% cao; Deaths/round, First deaths/round thấp. ACS chỉ ở mức trung bình, cho thấy nhóm này tạo giá trị bằng độ ổn định và hỗ trợ hơn là số kill thô. Win rate **52.6%**.

**Cảnh báo diễn giải:** cụm C0 có tỷ lệ Duelist rất cao, còn hai cụm kia chủ yếu là các vai trò khác. Vì vậy “phong cách” trong dữ liệu này chịu ảnh hưởng mạnh bởi Agent được chọn. Không nên viết “C0 là Duelist” hay “C2 là IGL” khi chưa có dữ liệu vai trò/chiến thuật.

### 1.5. Hình

- `reports/figures/02_cluster_selection.png`
- `reports/figures/02_cluster_pca.png`
- `reports/figures/02_cluster_profiles.png`
- `reports/figures/02_cluster_boxplots.png`

## 2. Bài toán 2 — Luật kết hợp Agent theo bản đồ

### 2.1. Cách chạy

- Mỗi dòng là một **đội trong một ván**, gồm đúng 5 Agent không có thứ tự.
- FP-Growth, tối đa 3 Agent trong một itemset; ngưỡng support tối thiểu là `max(12 đội, 2%)` cho mỗi map.
- Luật giữ lại nếu confidence ≥ 0,40 và lift ≥ 1,05. Bảng báo cáo chỉ lấy luật có ≥30 đội hình, confidence ≥0,5 và vế trái tối đa 2 Agent.
- Với mỗi luật, win rate khi có vế trái được so sánh với các đội còn lại của cùng map bằng Fisher exact; q-value là p-value đã hiệu chỉnh BH trên toàn bộ luật.

### 2.2. Luật nổi bật theo bản đồ

| Map | Luật | n đội hình | Support | Confidence | Lift | Win rate khi có vế trái | q (BH) |
|---|---|---|---|---|---|---|---|
| Ascent | kayo → astra, jett | 248 | 0.04 | 0.71 | 2.66 | 0.53 | 0.643 |
| Ascent | kayo, killjoy → astra | 205 | 0.03 | 0.86 | 2.64 | 0.52 | 0.863 |
| Ascent | jett, kayo → astra | 248 | 0.04 | 0.81 | 2.48 | 0.53 | 0.682 |
| Ascent | killjoy, skye → astra | 544 | 0.08 | 0.80 | 2.44 | 0.51 | 0.839 |
| Bind | brimstone, viper → skye | 374 | 0.06 | 0.79 | 2.88 | 0.50 | 0.977 |
| Bind | brimstone, skye → viper | 374 | 0.06 | 0.75 | 2.77 | 0.51 | 0.891 |
| Bind | jett, viper → astra | 356 | 0.06 | 0.70 | 2.60 | 0.51 | 0.842 |
| Bind | jett, skye → astra | 420 | 0.07 | 0.66 | 2.43 | 0.51 | 0.842 |
| Breeze | kayo → cypher, sova | 52 | 0.04 | 0.63 | 1.29 | 0.42 | 0.500 |
| Breeze | kayo, sova → cypher | 52 | 0.04 | 0.68 | 1.19 | 0.43 | 0.625 |
| Breeze | chamber → sova, viper | 56 | 0.05 | 1.00 | 1.19 | 0.52 | 0.977 |
| Breeze | chamber → sova | 56 | 0.05 | 1.00 | 1.18 | 0.52 | 0.977 |
| Fracture | raze → breach, cypher | 36 | 0.18 | 0.62 | 1.52 | 0.47 | 0.846 |
| Fracture | breach, raze → cypher | 36 | 0.18 | 0.63 | 1.41 | 0.47 | 0.901 |
| Fracture | raze → cypher | 36 | 0.18 | 0.62 | 1.38 | 0.47 | 0.846 |
| Fracture | raze → astra, breach | 37 | 0.19 | 0.64 | 1.36 | 0.47 | 0.846 |
| Haven | astra, sage → skye | 148 | 0.02 | 0.61 | 2.71 | 0.56 | 0.352 |
| Haven | killjoy, sage → skye | 199 | 0.03 | 0.58 | 2.58 | 0.59 | 0.036 |
| Haven | skye, sova → astra | 658 | 0.11 | 0.77 | 2.34 | 0.48 | 0.682 |
| Haven | sage, skye → killjoy | 199 | 0.03 | 0.78 | 2.34 | 0.61 | 0.011 |
| Icebox | omen → killjoy | 372 | 0.11 | 0.54 | 1.10 | 0.48 | 0.526 |
| Icebox | reyna, sage → viper | 1011 | 0.29 | 0.89 | 1.08 | 0.46 | 0.082 |
| Icebox | jett, omen → killjoy | 293 | 0.08 | 0.53 | 1.08 | 0.47 | 0.444 |
| Icebox | reyna → sova, viper | 1181 | 0.34 | 0.82 | 1.07 | 0.47 | 0.090 |
| Split | astra, viper → skye | 303 | 0.07 | 0.61 | 3.38 | 0.51 | 0.846 |
| Split | astra, skye → viper | 303 | 0.07 | 0.58 | 3.19 | 0.49 | 0.796 |
| Split | jett, viper → skye | 198 | 0.05 | 0.54 | 3.01 | 0.52 | 0.796 |
| Split | skye, viper → astra | 303 | 0.07 | 0.80 | 2.55 | 0.55 | 0.327 |

Đọc bảng: `Support` là tỷ lệ đội hình chứa toàn bộ Agent trong luật; `Confidence` là xác suất có vế phải khi đã có vế trái; `Lift` > 1 nghĩa là hai vế xuất hiện cùng nhau nhiều hơn so với kỳ vọng độc lập; `q (BH)` là p-value Fisher đã hiệu chỉnh. Các map nhỏ (Breeze, Fracture) có n nhỏ, không nên so sánh trực tiếp độ lớn lift với Ascent/Haven.

Sau hiệu chỉnh BH, **17/580 luật** có q < 0,05. Tuy nhiên các luật có vế trái trùng nhau rất nhiều, nên số 17 không phải 17 phát hiện độc lập; đây vẫn là phân tích khám phá.

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

| Map | Đội hình | n | Win rate | CI 95% | q (BH) |
|---|---|---|---|---|---|
| Icebox | jett + reyna + sage + sova + viper | 896 | 46.5% | 43.3%–49.8% | 0.510 |
| Icebox | jett + killjoy + sage + sova + viper | 883 | 55.9% | 52.7%–59.2% | 0.024 |
| Haven | cypher + jett + omen + phoenix + sova | 617 | 48.9% | 45.0%–52.9% | 1.000 |
| Bind | cypher + jett + omen + raze + sova | 544 | 52.0% | 47.8%–56.2% | 1.000 |
| Ascent | astra + jett + killjoy + skye + sova | 462 | 54.3% | 49.8%–58.8% | 0.772 |
| Split | breach + cypher + jett + omen + raze | 428 | 48.6% | 43.9%–53.3% | 1.000 |
| Haven | breach + cypher + jett + omen + sova | 424 | 46.0% | 41.3%–50.7% | 0.829 |
| Breeze | cypher + jett + skye + sova + viper | 416 | 53.6% | 48.8%–58.3% | 0.798 |
| Haven | cypher + jett + omen + reyna + sova | 411 | 49.9% | 45.1%–54.7% | 1.000 |
| Ascent | jett + killjoy + omen + reyna + sova | 393 | 45.8% | 40.9%–50.7% | 0.829 |
| Ascent | cypher + jett + omen + reyna + sova | 368 | 49.5% | 44.4%–54.5% | 1.000 |
| Ascent | breach + cypher + jett + omen + sova | 365 | 43.6% | 38.6%–48.7% | 0.445 |

Ví dụ đáng chú ý trên Icebox: hai đội hình phổ biến nhất chỉ khác nhau ở vị trí Reyna/Killjoy:

- Jett–Killjoy–Sage–Sova–Viper: **55.9% (n = 883)**, q = 0.024 so với phần còn lại của Icebox.
- Jett–Reyna–Sage–Sova–Viper: **46.5% (n = 896)**, q = 0.510.

Chênh lệch quan sát khoảng 9,4 điểm phần trăm, và chỉ đội hình Killjoy còn khác biệt sau hiệu chỉnh BH. Đây vẫn là quan hệ quan sát: đội mạnh có thể tự chọn đội hình tốt hơn, và một đội hình có thể được chọn nhiều hơn khi đội đang thắng.

### 3.2. Kiểm định thống kê và hiệu chỉnh đa so sánh

Với 473 đội hình đủ n ≥ 8, có **26** đội hình có p < 0,05 khi so với phần còn lại của map, nhưng chỉ **3** còn q < 0,05 sau BH. Bảng dưới liệt kê 8 đội hình có q thấp nhất; ba dòng đầu là ba trường hợp còn vượt qua ngưỡng FDR:

| Map | Đội hình | n | Win rate | CI 95% | q (BH) |
|---|---|---|---|---|---|
| Icebox | jett + killjoy + sage + sova + viper | 883 | 55.9% | 52.7%–59.2% | 0.024 |
| Ascent | jett + killjoy + omen + sage + sova | 285 | 60.7% | 54.9%–66.2% | 0.045 |
| Ascent | cypher + jett + omen + sage + sova | 240 | 61.7% | 55.4%–67.6% | 0.045 |
| Haven | cypher + omen + raze + sage + sova | 54 | 74.1% | 61.1%–83.9% | 0.060 |
| Ascent | breach + cypher + omen + sage + sova | 39 | 76.9% | 61.7%–87.4% | 0.097 |
| Split | cypher + jett + omen + raze + sage | 226 | 60.2% | 53.7%–66.3% | 0.159 |
| Haven | astra + killjoy + raze + sage + skye | 64 | 68.8% | 56.6%–78.8% | 0.229 |
| Haven | astra + jett + killjoy + phoenix + sova | 127 | 62.2% | 53.5%–70.2% | 0.334 |

Đây là danh sách **khám phá**, không phải kết luận nhân quả. Việc so sánh với phần còn lại của map (thay vì với 50%) kiểm soát baseline của từng map tốt hơn, nhưng chưa kiểm soát chất lượng đội, patch và việc đội hình được chọn có chủ đích. Cần kiểm định lại trên tập hold-out hoặc mô hình có kiểm soát đội, map, patch.

## 4. Trả lời câu hỏi nghiên cứu

1. **Có những nhóm người chơi nào?** Ba nhóm: mở giao tranh/sát thương cao, chết nhiều/hiệu quả thấp, ít chết/hiệu quả cao. Độ ổn định bootstrap cao (ARI 0.954), nhưng silhouette chỉ ở mức trung bình (0.278) và Ward chỉ đồng thuận một phần (ARI 0.354).
2. **Agent nào thường đi cùng nhau theo map?** Có cấu trúc rõ: Ascent (Kayo–Astra–Jett/Killjoy), Bind (Brimstone–Viper–Skye), Haven (Cypher–Omen–Sova), Icebox (Viper–Sage–Sova), Split (Astra–Viper–Skye), Breeze (Cypher–Sova–Viper), Fracture (Breach–Cypher–Raze).
3. **Tổ hợp phổ biến có thắng nhiều hơn?** Nhìn chung không có bằng chứng mạnh: phần lớn luật có win rate 46–55%, và chỉ 3/473 đội hình còn khác biệt sau BH. Một số đội hình ít phổ biến hơn có win rate cao, nhưng n nhỏ và có thể do chọn đội.
4. **Khác nhau theo map/patch?** Có. Tỷ lệ chọn Agent thay đổi theo map và theo patch lớn; một số tổ hợp chỉ tồn tại trong một giai đoạn meta.

## 5. Giới hạn

- Dữ liệu chỉ đến **2022-01-08**; meta hiện tại đã khác.
- KAST thiếu **97,9%**, không dùng trong mô hình.
- Không có dữ liệu vũ khí, tọa độ giao tranh, kỹ năng Agent, kill log.
- Chỉ **14.005/15.888 ván** có đủ 2 đội × 5 người × 5 Agent; các ván thiếu bị loại, có thể tạo thiên lệch chọn mẫu. Ngưỡng round 13–40 loại thêm 4 ván có tổng 42 round; ảnh hưởng không đáng kể nhưng vẫn là một quyết định làm sạch.
- **126 người chơi** bị loại vì độ phủ ADR/HS dưới 80%. Thiếu dữ liệu có thể không ngẫu nhiên (ví dụ theo giai đoạn hoặc theo nguồn trận), nên mẫu phân cụm không đại diện cho toàn bộ người chơi.
- Nhãn thắng/thua chỉ có cho **97.8%** đội hình.
- Breeze/Fracture có ít trận; luật của hai map này kém ổn định.
- Luật kết hợp chỉ đo đồng xuất hiện, không đo nhân quả.
- Phân cụm bị ảnh hưởng bởi Agent role; chưa tách được “phong cách” khỏi “vai trò”. Kết quả cũng thay đổi khi dùng tập biến rút gọn (ARI 0,473 so với mô hình chính), nên ba cụm không phải cấu trúc duy nhất.
- Đã dùng Fisher exact và BH cho 580 luật và 473 đội hình, nhưng đây vẫn là phân tích khám phá; chưa có hold-out theo thời gian và chưa kiểm soát chất lượng đội.

## 6. Hướng tiếp theo

1. Kiểm định lại các đội hình có win rate cao trên tập hold-out theo thời gian (train trước 2021-07, test sau).
2. Thêm mô hình hồi quy logistic/hierarchical cho thắng/thua với biến kiểm soát map, patch, đội.
3. Phân cụm riêng trong từng nhóm vai trò Agent để tách phong cách khỏi role.
4. Khai phá chuỗi round/mua sắm bằng PrefixSpan nếu còn thời gian.
5. Bổ sung dashboard so sánh luật giữa các map và patch.
