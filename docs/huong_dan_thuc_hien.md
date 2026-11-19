# Cách thực hiện đồ án theo chương trình học

1. Xác định ba mục tiêu. Phân nhóm tuyển thủ, tìm Agent đồng xuất hiện theo map và dự đoán thắng từ đội hình.
2. Kiểm tra kích thước, thuộc tính, giá trị thiếu, ngoại lệ và khóa dữ liệu bằng scripts/00_audit_data.py.
3. Tạo dữ liệu sạch bằng scripts/01_build_datasets.py. Tổng hợp chỉ số theo round và lọc người chơi đủ số ván, số round, độ phủ.
4. Chọn 7 đặc trưng gồm ADR, deaths/round, assists/round, first kills/round, first deaths/round, độ lệch chuẩn ACS và HS. Tránh đưa đồng thời nhiều biến sát thương tương quan cao.
5. Chặn giá trị ở phân vị 1%–99% rồi chuẩn hóa Z-score. Khoảng cách Euclidean khi đó sử dụng các biến có thang đo tương đương.
6. Chạy K-Means với k từ 2 đến 8. Chọn silhouette cao nhất, mô tả kích thước và đặc trưng từng cụm. So sánh Average linkage cùng k. Average linkage hợp nhất hai cụm có khoảng cách trung bình giữa các cặp điểm nhỏ nhất.
7. Xem mỗi đội hình là một giao dịch gồm năm Agent. Chạy Apriori và FP-Growth cùng support tối thiểu max(12/n, 0,02), độ dài tập tối đa 3, confidence ≥0,4 và lift ≥1,05. Kiểm tra tập phổ biến giống nhau, so sánh thời gian.
8. Tạo một dòng dự đoán cho mỗi ván. Đội đích chọn theo thứ tự chữ cái của mã đội. Chỉ dùng map, patch và chênh lệch lựa chọn Agent hai đội.
9. Chia train/test theo ngày. Huấn luyện Logistic Regression, Random Forest và AdaBoost trên cùng train. Random Forest dùng 300 cây, max_depth=8, min_samples_leaf=30. AdaBoost dùng 200 cây gốc một mức, learning_rate=0,05. Tham số định trước, không chọn theo test.
10. Đọc accuracy, AUC, log loss và Brier. So mốc tần suất train, bootstrap 2.000 lần theo MatchID để có khoảng tin cậy của mức cải thiện.
11. Tạo dashboard và chạy unit tests, kiểm tra đầu ra. Radar tuyển thủ là trực quan hóa các chỉ số thật.
12. Kết luận từ CSV vừa sinh. Phân tích dữ liệu cũ, khác biệt vai trò và thiếu sức mạnh đội/đối thủ. Average linkage có thể tạo nhóm nhỏ nên cần xét kích thước cụm.

## Các lệnh

```powershell
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
python scripts/04_make_report.py
python -m http.server 8765 --bind 127.0.0.1
```

## Đầu ra cần dùng khi thuyết trình

- outputs/tables/cluster_evaluation.csv để giải thích chọn k.
- outputs/tables/clustering_summary.csv và cluster_profiles_raw.csv để mô tả cụm.
- outputs/tables/association_comparison.csv để so sánh Apriori và FP-Growth.
- outputs/tables/predictor_comparison.csv để so sánh ba mô hình với mốc.
- reports/figures/02_cluster_features.png hiển thị ADR và deaths/round theo Z-score.
- reports/03_ket_qua_so_bo.md là bản tổng hợp sinh từ dữ liệu.

Các phương pháp chính đều thuộc danh sách đã học. Chúng là thuật toán kinh điển. Yêu cầu “hai phương pháp mới nhất” của giảng viên cần được xác nhận riêng khi chốt nội dung.
