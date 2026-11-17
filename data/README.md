# Dữ liệu

- `raw/valorant.sqlite`: dữ liệu gốc, **đã commit** (khoảng 76 MB).
- `processed/`: dữ liệu sinh ra bởi `scripts/01_build_datasets.py`, không commit.

File gốc đã có sẵn tại `data/raw/valorant.sqlite`. Nếu thay bằng bản dữ liệu khác, đặt cùng tên rồi chạy lại `make all`.

## Nguồn VCT cho hồ sơ tuyển thủ

`python scripts/10_build_vct_player_profiles.py` tải `data/external/vct.duckdb` từ [VCT Reference](https://vct-reference.com/dataset) nếu chưa có và sinh `data/processed/vct_player_profiles.csv`. Đây là bộ dữ liệu tier 1 riêng (2021–2026), dùng cho radar ACS, ADR, K/D, hỗ trợ/round, first kills/round và KAST. File metadata `vct_player_profiles_source.json` ghi URL, SHA-256, phạm vi ngày và cách tính. Không ghép ngầm bộ này với SQLite 2020–2022; các phần trên giao diện đều ghi nguồn riêng. Bản DuckDB không được commit vào Git, nhưng có trong gói mã bàn giao; chạy lệnh tải trên để tái tạo.

Các bảng gốc:

| Bảng | Ý nghĩa |
|---|---|
| `Matches` | trận, ngày, patch, giải, thể thức |
| `Games` | từng map trong trận, điểm, thông tin mua sắm |
| `Game_Scoreboard` | một dòng / người chơi / map, gồm Agent và chỉ số |
| `Game_Rounds` | lịch sử round dạng chuỗi (Python literal) |
