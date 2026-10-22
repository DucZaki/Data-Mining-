# Dữ liệu

- `raw/valorant.sqlite`: dữ liệu gốc (khoảng 76 MB).
- `processed/`: dữ liệu sinh ra bởi `scripts/01_build_datasets.py`, không commit.

Đặt file gốc vào `data/raw/valorant.sqlite` trước khi chạy pipeline.

Các bảng gốc:

| Bảng | Ý nghĩa |
|---|---|
| `Matches` | trận, ngày, patch, giải, thể thức |
| `Games` | từng map trong trận, điểm, thông tin mua sắm |
| `Game_Scoreboard` | một dòng / người chơi / map, gồm Agent và chỉ số |
| `Game_Rounds` | lịch sử round dạng chuỗi (Python literal) |
