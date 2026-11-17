# Hướng dẫn thực hiện đồ án và chạy mã

Tài liệu này là hướng dẫn triển khai, chưa phải báo cáo hay slide theo mẫu trường.

## 1. Xác định bài toán và nguồn

**Câu hỏi cho người xem:** Trên từng map, Agent và đội hình 5 người nào được các đội thi đấu chọn? Tỉ lệ thắng quan sát được ra sao? Hồ sơ sáu chỉ số của một tuyển thủ trong cùng mùa/map trông thế nào?

Hai nguồn có phạm vi khác nhau và được giữ riêng:

- `data/raw/valorant.sqlite`: 14.005 ván sạch, 28.010 lượt đội hình, từ 05/2020 đến 01/2022. Dùng cho map, Agent, tổ hợp và dự đoán thắng.
- [VCT Reference](https://vct-reference.com/dataset): tệp DuckDB 13 MB, gồm 10 bảng. Bảng `player_map` có 73.976 dòng tuyển thủ–map trong bản tải này, mùa 2021–2026. Dùng cho radar tuyển thủ. Trang nguồn cho phép sử dụng dữ liệu và mô tả chi tiết phạm vi, độ phủ; xem thêm [methodology](https://vct-reference.com/methodology).

Đã đối chiếu các nguồn khác: [Kaggle LAN đến 05/2022](https://www.kaggle.com/datasets/aadeshmishra/valorant-esports-player-stats-at-lan-till-may-2022) và [Kaggle Champions Istanbul 2022](https://www.kaggle.com/datasets/shihouinyoruichi/valorant-champions-2022-istanbul-stats) hẹp hơn về thời gian/giải; bộ [Hugging Face gameplay-data](https://huggingface.co/datasets/xiaoluo11/valorant-gameplay-data) là 12 mẫu ảnh/video, không phải bảng chỉ số thi đấu. Vì vậy phần radar dùng VCT Reference. Không gán số liệu mô phỏng cho tuyển thủ thật.

## 2. Khảo sát và kiểm tra dữ liệu

Chạy `python scripts/00_audit_data.py` để xem kích thước, khóa, map, phân phối và thiếu dữ liệu của SQLite. Chạy `python scripts/10_build_vct_player_profiles.py` để lấy nguồn VCT và tạo hồ sơ. Bảng scoreboard gốc có ACS và ADR ở hơn 96% dòng, nhưng `KAST_Percent` chỉ có ở khoảng **2,2%**; không điền 0 hay đoán KAST từ K/D. Metadata `data/processed/vct_player_profiles_source.json` lưu URL, SHA-256 và phạm vi ngày để truy xuất nguồn.

Kiểm tra giá trị bất thường: số round hợp lệ 13–40; tỉ lệ KAST 0–100%; K/D hữu hạn; Agent mỗi đội đủ 5 và không trùng; một GameID có đúng hai đội; kết quả thắng khớp `Games.Winner`. Các lỗi kiểu dữ liệu cũng cần kiểm tra: KAST trong DuckDB là `TINYINT`, phải đổi sang số thực **trước** khi nhân với số round để tránh tràn số nguyên.

## 3. Tiền xử lý và tạo đặc trưng

Chạy `python scripts/01_build_datasets.py` để làm sạch trận, scoreboard và đội hình. Với hồ sơ tuyển thủ VCT:

- Chỉ giữ trận hoàn tất, bỏ showmatch, chỉ dùng dòng có đủ sáu chỉ số và round hợp lệ.
- Yêu cầu độ phủ của sáu chỉ số ít nhất 80%; tối thiểu 20 map cho hồ sơ cả mùa hoặc 5 ván cho hồ sơ một map.
- ACS, ADR, KAST: trung bình **theo số round**. K/D: tổng kills / tổng deaths. Hỗ trợ và mở giao tranh: assists / round và first kills / round.
- Radar dùng **phân vị** của từng chỉ số trong nhóm tuyển thủ đủ điều kiện cùng mùa và map. Sáu chỉ số thật vẫn hiện bên cạnh; phân vị chỉ phục vụ so sánh trong nhóm, không phải điểm kỹ năng tuyệt đối.

Đầu ra: `data/processed/vct_player_profiles.csv` với `player_id`, tên, mùa, map, số ván, độ phủ, sáu chỉ số thật và sáu phân vị. Mã tạo: `src/valorant_mining/player_radar.py`, `scripts/10_build_vct_player_profiles.py`.

## 4. Phương pháp khai phá và đối chứng

Radar là **trực quan hóa mô tả**, không phải thuật toán dự đoán. Phần khai phá của đồ án sử dụng:

1. **PCA + K-Means** phân cụm 2.599 người chơi đủ dữ liệu; so silhouette, bootstrap ARI và phân cụm Ward.
2. **FP-Growth** tìm Agent đồng xuất hiện theo map; đánh giá support, confidence, lift. So sánh win rate đội hình bằng khoảng Wilson, Fisher exact và hiệu chỉnh Benjamini–Hochberg.
3. **LightGBM và CatBoost** là hai thuật toán hiện đại để so sánh với logistic regression và mốc tần suất thắng train. Chia tập theo ngày, giữ cùng một trận trong một tập, đánh giá trên tương lai bằng AUC, log loss, Brier và bootstrap theo `MatchID`.

Không gọi tương quan giữa Agent/đội hình và thắng là quan hệ nhân quả. Chất lượng đội, đối thủ, bản cập nhật và chiến thuật đều có thể gây nhiễu.

## 5. Thực nghiệm và bảng kết quả cần kiểm tra

Chạy `python scripts/run_pipeline.py` để tạo lại các bảng. Đọc `outputs/tables/clustering_summary.csv`, `agent_rules_summary.csv`, `exact_compositions.csv`, `predictor_comparison.csv`, `predictor_by_map.csv`, `vct_player_profiles.csv` (trong `data/processed`). Bản chạy hiện có:

| Hạng mục | Kết quả | Cách diễn giải |
|---|---:|---|
| Ván sạch / lượt đội hình | 14.005 / 28.010 | Hai đội trên mỗi ván |
| Luật kết hợp | 580 | Đồng xuất hiện, chưa chứng minh hiệu quả |
| K-Means, k=3 | silhouette 0,278 | Mức tách cụm vừa phải |
| LightGBM | AUC 0,540; log loss 0,6892 | Tốt hơn mốc rất ít; CI bootstrap chạm 0 |
| CatBoost | AUC 0,539; log loss 0,6905 | Tốt hơn mốc rất ít; CI bootstrap chạm 0 |
| Hồ sơ tuyển thủ VCT | 6.285 hồ sơ; 652 tuyển thủ | Sáu chỉ số đủ độ phủ theo mùa/map |

So sánh hai mô hình dự đoán dựa trên cùng 2.509 ván test, không so độ chính xác của hai tập khác nhau. Trong phần phân tích, trình bày ví dụ cụ thể theo map/Agent/tuyển thủ, kèm cỡ mẫu và khoảng tin cậy. Kiểm tra thay đổi khi lọc mùa/map và đối chiếu với giai đoạn dữ liệu.

## 6. Trực quan hóa và kiểm thử

`python scripts/09_build_public_dashboard.py` tạo `dashboard/index.html`. Mở bằng `python -m http.server 8765` rồi vào `http://127.0.0.1:8765/dashboard/`. Thử bộ lọc map, giai đoạn, mùa VCT và tên tuyển thủ. Kiểm tra radar đổi theo tuyển thủ, sáu chỉ số gốc vẫn khớp CSV, nhóm ít mẫu không được vẽ. Chạy `python -m unittest discover -s tests -v` và `python scripts/05_validate.py`.

## 7. Kết luận, hạn chế và hướng phát triển

Kết luận phải tách hai nguồn. Phần map/đội hình đến 01/2022 là lịch sử; hồ sơ tuyển thủ VCT đến 10/2026 thuộc mẫu giải tier 1, không được trộn hai phạm vi thành một tỉ lệ chung. KAST trong SQLite gốc thiếu gần hết, nên nguồn VCT được dùng cho biểu đồ riêng. Phân vị có thể đổi khi lọc mùa/map và không kiểm soát vai trò Agent hoặc chất lượng đối thủ. Mô hình thắng hiện chỉ cải thiện nhỏ so với mốc.

Hướng tiếp theo: so sánh tuyển thủ **cùng vai trò**, phân tích xu hướng theo patch, bộ dựng đội hình 5 Agent và kiểm định trên dữ liệu giải mới. Nếu cần tạo dữ liệu mô phỏng để thử giao diện, đặt file ở `data/synthetic/`, gắn `is_synthetic=true` và không trộn vào kết quả thực nghiệm hoặc kết luận.

## Lệnh chạy từ đầu

```powershell
git clone https://github.com/DucZaki/Data-Mining-.git
cd Data-Mining-
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
python -m http.server 8765
```

Pipeline tự tải VCT Reference lần đầu qua `scripts/10_build_vct_player_profiles.py`. Muốn cập nhật VCT về bản mới, xóa riêng `data/external/vct.duckdb`, chạy lại script này rồi tạo lại dashboard. Khi cập nhật nguồn, ghi ngày tải và SHA-256 trong metadata; không so trực tiếp bản mới với kết quả cũ mà thiếu thông tin phiên bản.
