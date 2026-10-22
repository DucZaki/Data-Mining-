# Kế hoạch 10 ngày

Mục tiêu: hoàn thành hai bài toán khai phá chính, có báo cáo và notebook tái lập được. PrefixSpan là phần mở rộng.

## Câu hỏi nghiên cứu

1. Có những nhóm người chơi nào dựa trên khả năng hạ gục, hỗ trợ, mở giao tranh và độ ổn định?
2. Agent nào thường xuất hiện cùng nhau trên từng bản đồ?
3. Những tổ hợp Agent phổ biến có hiệu suất thắng khác nhau không?
4. Kết quả khác nhau thế nào giữa các bản đồ và phiên bản game?

## Lịch

| Ngày | Việc chính | Trạng thái |
|---|---|---|
| 1 | Khảo sát dữ liệu, chọn câu hỏi | ✅ `scripts/00_audit_data.py` |
| 2 | Làm sạch bảng người chơi và Agent | ✅ `src/valorant_mining/cleaning.py` |
| 3 | Tạo `player_features` và `team_compositions` | ✅ `scripts/01_build_datasets.py` |
| 4 | Phân tích mô tả, chọn biến | ✅ `reports/02_du_lieu_khai_pha.md` |
| 5 | Chạy K-Means, chọn k | ✅ `scripts/02_cluster_players.py` |
| 6 | Diễn giải, trực quan hóa cụm | ✅ `reports/03_ket_qua_so_bo.md` |
| 7 | Chạy FP-Growth/Apriori | ✅ `scripts/03_agent_rules.py` |
| 8 | So sánh luật theo bản đồ | ✅ bảng `agent_rules_by_map.csv` |
| 9 | Đánh giá, kiểm tra chất lượng, viết hạn chế | 🟡 cần bổ sung hold-out/kiểm định |
| 10 | Hoàn thiện báo cáo, notebook, slide | 🟡 notebook có, slide chưa |

## Đơn vị phân tích

| Phân tích | Một dòng là |
|---|---|
| Phân cụm người chơi | một PlayerID, tổng hợp qua các ván |
| Luật kết hợp Agent | một đội trong một ván, tập 5 Agent |
| Mẫu tuần tự (mở rộng) | một đội trong một hiệp, chuỗi round |

## Việc cần làm trước khi nộp

- [ ] Chạy lại toàn bộ pipeline từ dữ liệu gốc và lưu log.
- [ ] Kiểm tra bảng kết quả với giảng viên hướng dẫn.
- [ ] Bổ sung hold-out theo thời gian cho các đội hình win rate cao.
- [ ] Thêm phần kiểm định thống kê (multiple comparisons) nếu kết luận về thắng/thua.
- [ ] Chuyển báo cáo markdown sang PDF/Word theo yêu cầu môn học.
- [ ] Làm slide 10–15 phút.
- [ ] (Mở rộng) PrefixSpan cho chuỗi mua sắm/round.

## Giới hạn phải ghi trong báo cáo

- Dữ liệu đến 2022-01-08.
- KAST thiếu 97,9%, không dùng.
- Thiếu vũ khí, tọa độ, kỹ năng Agent, kill log.
- Một số ván thiếu Agent/đội/round.
- Luật kết hợp không phải nhân quả.
- Phân cụm bị ảnh hưởng bởi Agent role.
