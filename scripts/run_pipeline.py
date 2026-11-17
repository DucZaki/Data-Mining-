#!/usr/bin/env python
"""Run the full experiment pipeline on Windows, macOS, or Linux."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    ("Audit dữ liệu", [sys.executable, "scripts/00_audit_data.py"]),
    ("Tạo tập phân tích", [sys.executable, "scripts/01_build_datasets.py"]),
    ("Phân cụm", [sys.executable, "scripts/02_cluster_players.py"]),
    ("Luật kết hợp", [sys.executable, "scripts/03_agent_rules.py"]),
    ("So sánh mô hình", [sys.executable, "scripts/07_compare_predictors.py"]),
    ("Trang chẩn đoán", [sys.executable, "scripts/08_build_diagnostic_page.py"]),
    ("Hồ sơ tuyển thủ VCT", [sys.executable, "scripts/10_build_vct_player_profiles.py"]),
    ("Trang tra cứu map và Agent", [sys.executable, "scripts/09_build_public_dashboard.py"]),
    ("Unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("Kiểm tra đầu ra", [sys.executable, "scripts/05_validate.py"]),
]


def main() -> int:
    if not (ROOT / "data/raw/valorant.sqlite").is_file():
        print("Thiếu data/raw/valorant.sqlite", file=sys.stderr)
        return 1
    started = time.perf_counter()
    for index, (name, command) in enumerate(STAGES, 1):
        print(f"\n[{index}/{len(STAGES)}] {name}", flush=True)
        step = time.perf_counter()
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            print(f"Dừng ở bước {name}: mã lỗi {result.returncode}", file=sys.stderr)
            return result.returncode
        print(f"Hoàn tất {name} sau {time.perf_counter() - step:.1f} giây", flush=True)
    print(f"\nPipeline PASS sau {time.perf_counter() - started:.1f} giây")
    print(f"Trang tra cứu: {ROOT / 'dashboard/index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
