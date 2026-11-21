# Khai phá dữ liệu thi đấu Valorant

Tra cứu Agent và đội hình theo map, phân nhóm tuyển thủ, dự đoán thắng từ lựa chọn Agent.

## Tập dữ liệu

Dữ liệu chính được lưu tại `data/raw/valorant.sqlite`, bao gồm các trận thi đấu Valorant trong giai đoạn 2020–2022.

- `Matches`: thông tin trận đấu, thời gian, giải đấu và thể thức.
- `Games`: bản đồ thi đấu, đội tham gia và điểm số.
- `Game_Scoreboard`: Agent và chỉ số thi đấu của từng tuyển thủ trên mỗi bản đồ.
- `Game_Rounds`: lịch sử từng round, kết quả và thông tin kinh tế khi có dữ liệu.

Các chỉ số gồm ACS, ADR, kills, deaths, assists, KAST, HS%, first kills và first deaths. Một số trường có dữ liệu thiếu, cần xử lý trước khi phân tích.

Sau làm sạch, dữ liệu có 14.005 ván, 28.010 lượt đội hình và 2.599 tuyển thủ đủ điều kiện phân cụm.

Hồ sơ radar tuyển thủ sử dụng bộ dữ liệu riêng từ [VCT Reference](https://vct-reference.com/dataset), gồm ACS, ADR, K/D, hỗ trợ/round, first kills/round và KAST. Metadata của nguồn này được lưu tại `data/processed/vct_player_profiles_source.json` khi tạo dữ liệu.

## Thông tin tra cứu

- Tần suất lựa chọn và tỉ lệ thắng của Agent theo bản đồ.
- Đội hình phổ biến và các nhóm Agent thường được sử dụng cùng nhau.
- Hồ sơ chỉ số và phân nhóm tuyển thủ theo đặc điểm thi đấu.
- Kết quả dự đoán thắng dựa trên lựa chọn Agent.

Thống kê đội hình phản ánh dữ liệu lịch sử 2020–2022. Tỉ lệ thắng quan sát được không bảo đảm hiệu quả trong các phiên bản hiện tại.

## Phương pháp

- Chọn 7 đặc trưng ADR, deaths/round, assists/round, first kills/round, first deaths/round, độ lệch chuẩn ACS và HS.
- Chặn ngoại lệ phân vị 1%–99%, chuẩn hóa Z-score.
- K-Means chọn k từ 2–8 theo silhouette, đối chứng phân cụm phân cấp Average linkage cùng k.
- Apriori và FP-Growth khai phá cùng dữ liệu, support, confidence, lift để so sánh.
- Logistic Regression, Random Forest và AdaBoost dự đoán thắng trên cùng tập test thời gian sau.
- Bootstrap theo MatchID, Wilson, Fisher exact và hiệu chỉnh BH dùng để đánh giá độ bất định.

## Xem giao diện

Từ thư mục dự án, chạy:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Mở [dashboard](http://127.0.0.1:8765/dashboard/) để xem các thống kê đã được tạo sẵn.

## Cấu trúc

- src/valorant_mining/ chứa làm sạch, đặc trưng, phân cụm, luật, trực quan hóa.
- dashboard/ chứa giao diện và trang chẩn đoán.
- tests/ kiểm tra tính đúng đắn của dữ liệu và thực nghiệm.
