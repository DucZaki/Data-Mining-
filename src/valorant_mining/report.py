"""Generate a current experiment summary directly from output tables."""
from __future__ import annotations

import pandas as pd

from .config import OUTPUT_TABLES, REPORT_DIR, CLUSTER_FEATURES


def build_results_report() -> str:
    summary = pd.read_csv(OUTPUT_TABLES / "clustering_summary.csv")
    clusters = pd.read_csv(OUTPUT_TABLES / "cluster_profiles_raw.csv")
    models = pd.read_csv(OUTPUT_TABLES / "predictor_comparison.csv")
    association = pd.read_csv(OUTPUT_TABLES / "association_comparison.csv")
    lines = [
        "# Kết quả thực nghiệm theo phương pháp trong chương trình học",
        "",
        "## Quy trình",
        "",
        "1. Kiểm tra SQLite, loại ván sai và tạo đội hình đủ 5 Agent.",
        "2. Tổng hợp chỉ số tuyển thủ theo round, kiểm tra độ phủ.",
        "3. Chặn ngoại lệ tại phân vị 1% và 99%, chuẩn hóa Z-score.",
        "4. Phân cụm K-Means trên các biến " + ", ".join(CLUSTER_FEATURES) + ".",
        "5. Chọn k theo silhouette từ 2 đến 8, so sánh Average linkage cùng k.",
        "6. So sánh Apriori và FP-Growth cùng support, confidence, lift.",
        "7. So sánh Logistic Regression, Random Forest và AdaBoost trên tập test theo thời gian.",
        "",
        "## Phân cụm",
        "",
        summary.to_markdown(index=False),
        "",
        clusters.to_markdown(index=False),
        "",
        "## Luật kết hợp",
        "",
        association.to_markdown(index=False),
        "",
        "Thời gian phụ thuộc máy và lần chạy. Hai thuật toán phải tìm cùng tập phổ biến.",
        "",
        "## Dự đoán thắng",
        "",
        models.to_markdown(index=False),
        "",
        "Train dùng ngày trước 22/09/2021, test từ 22/09/2021 đến 08/01/2022.",
        "Các mô hình chỉ dùng map, patch và đội hình trước trận. Bootstrap lấy lại mẫu theo MatchID.",
        "Δ log loss dương là tốt hơn mốc. CI chạm 0 chưa đủ bằng chứng cải thiện.",
        "",
        "## Hạn chế",
        "",
        "Thống kê đội hình thuộc giai đoạn 2020–2022. Sức mạnh đội và đối thủ chưa được kiểm soát.",
        "Average linkage có thể tạo nhóm rất nhỏ. Cần đọc cả kích thước cụm và silhouette.",
        "Radar tuyển thủ VCT sử dụng nguồn riêng và phục vụ mô tả.",
    ]
    return "\n".join(lines) + "\n"


def save_results_report() -> None:
    path = REPORT_DIR / "03_ket_qua_so_bo.md"
    path.write_text(build_results_report(), encoding="utf-8")
    print(path)
