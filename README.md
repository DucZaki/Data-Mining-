# Khai phá dữ liệu thi đấu Valorant

Tra cứu Agent và đội hình theo map, phân nhóm tuyển thủ, dự đoán thắng từ lựa chọn Agent.

## Chạy chương trình

Yêu cầu Python 3.11 trở lên.

```powershell
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
python -m http.server 8765 --bind 127.0.0.1
```

Mở http://127.0.0.1:8765/dashboard/ để xem kết quả cho người xem.
Trang chẩn đoán mô hình ở /dashboard/predictor_diagnostics.html.

## Phương pháp

- Chọn 7 đặc trưng ADR, deaths/round, assists/round, first kills/round, first deaths/round, độ lệch chuẩn ACS và HS.
- Chặn ngoại lệ phân vị 1%–99%, chuẩn hóa Z-score.
- K-Means chọn k từ 2–8 theo silhouette, đối chứng phân cụm phân cấp Average linkage cùng k.
- Apriori và FP-Growth khai phá cùng dữ liệu, support, confidence, lift để so sánh.
- Logistic Regression, Random Forest và AdaBoost dự đoán thắng trên cùng tập test thời gian sau.
- Bootstrap theo MatchID, Wilson, Fisher exact và hiệu chỉnh BH dùng để đánh giá độ bất định.

## Dữ liệu và kết quả

SQLite gốc tại data/raw/valorant.sqlite. Sau làm sạch có 14.005 ván, 28.010 lượt đội hình và 2.599 người chơi đủ điều kiện phân cụm.
Hồ sơ radar dùng nguồn VCT Reference riêng, tự tải qua scripts/10_build_vct_player_profiles.py.
Metadata và SHA-256 được ghi trong data/processed/vct_player_profiles_source.json.

Các CSV kết quả ở outputs/tables/. Tạo bản tổng hợp bằng python scripts/04_make_report.py.
Hướng dẫn chi tiết ở docs/huong_dan_thuc_hien.md.
Dữ liệu gốc đội hình thuộc 2020–2022. Hiệu suất dự đoán phải đọc cùng mốc tần suất train và khoảng tin cậy.

## Cấu trúc

- src/valorant_mining/ chứa làm sạch, đặc trưng, phân cụm, luật, trực quan hóa.
- scripts/ chứa các bước pipeline và sinh dashboard.
- notebooks/ chứa notebook thực nghiệm.
- dashboard/ chứa giao diện và trang chẩn đoán.
- tests/ kiểm tra tính đúng đắn của dữ liệu và thực nghiệm.
