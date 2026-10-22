#!/usr/bin/env python
"""Step 4: generate the preliminary results report."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from valorant_mining.report import save_results_report


if __name__ == "__main__":
    save_results_report()
