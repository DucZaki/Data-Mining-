# Kiểm tra dữ liệu Valorant

## 1. Quy mô và phạm vi

- Khoảng thời gian: **2020-05-02 13:00:00** đến **2022-01-08 15:30:00**.
- Số bảng: Matches, Games, Game_Scoreboard, Game_Rounds.
- Số patch thô trong bảng Matches: **39** (chuỗi patch chưa được chuẩn hóa, có cả giá trị thiếu).

| table | rows |
|---|---|
| Matches | 7818 |
| Games | 15888 |
| Game_Scoreboard | 157939 |
| Game_Rounds | 15531 |

## 2. Phân bố bản đồ

| Map | games |
|---|---|
| Ascent | 3866 |
| Haven | 3487 |
| Bind | 3355 |
| Split | 2408 |
| Icebox | 1944 |
| Breeze | 661 |
| Fracture | 107 |
| TBD | 60 |

Bản đồ `TBD` không phải bản đồ thi đấu và bị loại khỏi phân tích đội hình. `Fracture` chỉ có 107 ván, nên các luật riêng cho Fracture có độ tin cậy thấp hơn các map còn lại.

## 3. Mức độ thiếu dữ liệu

| field | missing | missing_pct |
|---|---|---|
| PlayerID | 87 | 0.06 |
| Agent (rỗng/null) | 4100 | 2.60 |
| ACS | 530 | 0.34 |
| KAST_Percent | 154572 | 97.87 |
| FirstKills | 530 | 0.34 |
| Num_2Ks | 10195 | 6.46 |

**KAST không dùng làm biến trung tâm.** Chỉ 3367 dòng có KAST (2.1%), và giá trị nằm trong khoảng 0.14–1.00. Việc thay giá trị thiếu bằng 0 sẽ tạo ra một biến giả có ý nghĩa sai, nên KAST bị loại khỏi mô hình.

Số dòng mỗi ván:

| rows_per_game | games |
|---|---|
| 1 | 2 |
| 2 | 8 |
| 3 | 21 |
| 4 | 27 |
| 5 | 37 |
| 6 | 34 |
| 7 | 19 |
| 8 | 14 |
| 9 | 46 |
| 10 | 15669 |
| 12 | 1 |

Các ván không có đúng 10 dòng thường thiếu người chơi, thiếu Agent hoặc có dòng huấn luyện viên/dự bị. Những ván này không thể tạo đội hình 5 Agent đầy đủ.

## 4. Người chơi và ngưỡng tối thiểu

Tổng số PlayerID khác nhau: **8596**.

| min_games | players |
|---|---|
| 1 | 8596 |
| 5 | 4330 |
| 10 | 2976 |
| 15 | 2372 |
| 20 | 1983 |
| 30 | 1520 |
| 50 | 942 |

Ngưỡng mặc định của dự án là **≥ 10 ván** và **≥ 100 round**. Ngưỡng này giữ được 2976 người chơi trước khi áp thêm yêu cầu độ phủ ACS/ADR/HS ≥80% và đủ biến mô hình.

## 5. Lịch sử round

| games | with_round_history | coverage_pct | round_count_mismatch |
|---|---|---|---|
| 15888 | 14854 | 95.64 | 34 |

Khoảng 95.6% ván có RoundHistory. Trong số này, một số ít ván có tổng round của bảng Games không khớp với độ dài lịch sử round; các ván đó bị loại để tránh chia sai mẫu số khi tính chỉ số theo round. Trong bảng Games gốc có **4 ván** vượt 40 round (đều là 42 round) và **28 ván** dưới 13 round; ngưỡng 13–40 loại các ván này sau bước kiểm tra đội hình.

## 6. Chất lượng nhóm đội

| team_group_size | groups | groups_with_5_distinct_agents |
|---|---|---|
| 1 | 52 | 0 |
| 2 | 75 | 0 |
| 3 | 107 | 0 |
| 4 | 1093 | 0 |
| 5 | 29328 | 29324 |
| 10 | 5 | 0 |

Một nhóm có 5 người chơi vẫn có thể không đủ 5 Agent khác nhau (ví dụ trùng Agent hoặc thiếu Agent). Các nhóm như vậy bị loại khỏi tập đội hình dùng cho luật kết hợp.

## 7. Kết quả làm sạch

| bước | số dòng |
|---|---|
| Bảng điểm gốc | 157939 |
| Sau khi bỏ PlayerID/Agent/đội thiếu | 151583 |
| Ván có 2 đội × 5 người chơi hợp lệ | 14016 |
| Ván còn lại sau kiểm tra số round và bản đồ | 14005 |
| Đội hình 5 Agent dùng cho luật kết hợp | 28010 |

- Số ván còn lại: **14005**.
- Số đội hình (team-map): **28010**.
- Số đội hình có nhãn thắng/thua: **27382** (97.8%).
- Số người chơi còn trong bảng điểm sạch: **7481**.
- Số đội hình theo bản đồ:

| map | teams | games |
|---|---|---|
| Ascent | 6806 | 3403 |
| Haven | 6216 | 3108 |
| Bind | 5896 | 2948 |
| Split | 4224 | 2112 |
| Icebox | 3494 | 1747 |
| Breeze | 1176 | 588 |
| Fracture | 198 | 99 |

## 8. Hệ quả cho phân tích

1. **Đơn vị phân tích của phân cụm** là một PlayerID, tổng hợp qua các ván có đủ dữ liệu; không dùng từng dòng game.
2. **Đơn vị phân tích của luật kết hợp** là một đội trong một ván, với tập 5 Agent không có thứ tự.
3. **Không đưa KAST vào mô hình**; các biến thay thế là Kills/round, Deaths/round, ACS, ADR, FirstKills/Deaths và tần suất multi-kill.
4. **Không kết luận nhân quả** từ luật kết hợp. Một tổ hợp xuất hiện nhiều chỉ cho biết nó phổ biến, không chứng minh nó làm tăng tỷ lệ thắng.
5. Dữ liệu dừng ở **2022-01-08**, nên kết quả không đại diện cho meta hiện tại.

## 9. File sinh ra

- `data/processed/clean_games.csv`
- `data/processed/clean_scoreboard.csv`
- `data/processed/team_compositions.csv`
- `data/processed/cleaning_audit.csv`
- `reports/figures/01_audit_overview.png`
- `reports/figures/01_audit_missing.png`
