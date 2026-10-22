# Kiểm tra chất lượng đầu ra

| Kiểm tra | Kết quả | Nguồn |
|---|---|---|
| Mỗi ván có đúng 2 đội hình | PASS | team_compositions |
| Không trùng khóa (GameID, team) | PASS | team_compositions |
| Mỗi đội có đúng 5 Agent | PASS | team_compositions |
| Mỗi đội hình có 5 Agent khác nhau | PASS | team_compositions |
| Chỉ còn bản đồ thi đấu | PASS | team_compositions |
| Số round trong khoảng 13–40 | PASS | team_compositions |
| Nhãn thắng/thua chỉ là 0/1/NaN | PASS | team_compositions |
| Người chơi đủ ≥10 ván | PASS | player_features |
| Người chơi đủ ≥100 round | PASS | player_features |
| Không thiếu biến mô hình | PASS | player_features |
| Không trùng PlayerID | PASS | player_features |
| Support trong (0, 1] | PASS | rules |
| Confidence trong (0, 1] | PASS | rules |
| Lift ≥ 1 | PASS | rules |
| Support count ≤ số đội hình | PASS | rules |
| Đội hình chi tiết có đúng 5 Agent | PASS | exact_compositions |
| Win rate trong [0, 1] | PASS | exact_compositions |

**Tổng:** 17 kiểm tra, 0 lỗi.

Các kiểm tra này chỉ xác nhận tính nhất quán của dữ liệu đầu ra; không thay thế kiểm định thống kê cho các kết luận về thắng/thua.