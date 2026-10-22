# Dữ liệu

- `raw/valorant.sqlite`: dữ liệu gốc, **đã commit** (khoảng 76 MB).
- `processed/`: dữ liệu sinh ra bởi `scripts/01_build_datasets.py`, không commit.

File gốc đã có sẵn tại `data/raw/valorant.sqlite`. Nếu thay bằng bản dữ liệu khác, đặt cùng tên rồi chạy lại `make all`.

Các bảng gốc:

| Bảng | Ý nghĩa |
|---|---|
| `Matches` | trận, ngày, patch, giải, thể thức |
| `Games` | từng map trong trận, điểm, thông tin mua sắm |
| `Game_Scoreboard` | một dòng / người chơi / map, gồm Agent và chỉ số |
| `Game_Rounds` | lịch sử round dạng chuỗi (Python literal) |
