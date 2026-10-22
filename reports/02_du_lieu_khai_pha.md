# Dữ liệu khai phá đã xây dựng

## 1. Nhật ký làm sạch

| Chỉ số | Giá trị |
|---|---|
| scoreboard_rows_raw | 157939 |
| dropped_missing_player_id | 87 |
| dropped_bad_agent_or_team | 6265 |
| dropped_duplicate_player_game | 4 |
| scoreboard_rows_clean | 151583 |
| games_raw | 15888 |
| games_with_round_history | 14854 |
| round_history_inconsistent | 7 |
| games_with_valid_rosters | 14016 |
| games_after_round_and_map_filter | 14005 |
| games_with_winner_mapping | 13691 |
| teams_in_compositions | 28010 |
| compositions_with_win_label | 27382 |
| players_remaining | 7481 |
| maps_kept | ['Ascent', 'Bind', 'Breeze', 'Fracture', 'Haven', 'Icebox', 'Split'] |

## 2. Người chơi sau ngưỡng tối thiểu

| Bước | Số người chơi |
|---|---|
| Người chơi trong bảng điểm sạch | 7476 |
| Đủ ≥10 ván | 2724 |
| Đủ ≥100 round | 2724 |
| Đủ biến mô hình | 2724 |

## 3. Đội hình theo bản đồ

| Bản đồ | Số ván | Số đội hình | Có nhãn thắng |
|---|---|---|---|
| Ascent | 3403 | 6806 | 6652 |
| Haven | 3108 | 6216 | 6036 |
| Bind | 2948 | 5896 | 5730 |
| Split | 2112 | 4224 | 4096 |
| Icebox | 1747 | 3494 | 3494 |
| Breeze | 588 | 1176 | 1176 |
| Fracture | 99 | 198 | 198 |

## 4. Biến dùng cho phân cụm

Các biến được tổng hợp theo PlayerID, chia theo tổng số round để tránh ưu tiên các ván có overtime:

- Kills/round, Deaths/round, Assists/round, K/D
- ACS, ADR, HS%
- First kills/round, First deaths/round
- Số multi-kill (2K–5K) trên mỗi round
- Độ lệch chuẩn ACS giữa các ván (độ ổn định)

KAST bị loại vì thiếu gần như toàn bộ. Tỷ lệ chọn vai trò Agent chỉ dùng để mô tả cụm, không đưa vào mô hình.

## 5. File sinh ra

- `data/processed/clean_games.csv`
- `data/processed/clean_scoreboard.csv`
- `data/processed/team_compositions.csv`
- `data/processed/player_features.csv`
- `data/processed/player_attrition.csv`