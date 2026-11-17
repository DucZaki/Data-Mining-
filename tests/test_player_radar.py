"""Regression checks for VCT profile aggregation and KAST scaling."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from valorant_mining.player_radar import build_profiles


class PlayerRadarTests(unittest.TestCase):
    def test_round_weighted_metrics_do_not_overflow_tinyint(self):
        rows = []
        for i in range(20):
            rows.append({"player_id": 1, "player_name": "Example", "season": 2026,
                         "map_name": "Ascent", "game_id": str(i), "rounds": 20,
                         "acs_all": 200, "adr_all": 130,
                         "kast_all": pd.Series([75], dtype="int8").iloc[0],
                         "kills_all": 20, "deaths_all": 10,
                         "assists_all": 5, "fk_all": 2})
        out = build_profiles(pd.DataFrame(rows))
        self.assertEqual(len(out), 2)  # Ascent and all-map scopes.
        profile = out[out["map"] == "Ascent"].iloc[0]
        self.assertEqual(profile["games"], 20)
        self.assertAlmostEqual(profile["acs"], 200)
        self.assertAlmostEqual(profile["adr"], 130)
        self.assertAlmostEqual(profile["kast"], .75)
        self.assertAlmostEqual(profile["kd"], 2)
        self.assertAlmostEqual(profile["assists_pr"], .25)
        self.assertAlmostEqual(profile["first_kills_pr"], .1)

    def test_thin_profiles_are_excluded(self):
        row = {"player_id": 1, "player_name": "Thin", "season": 2026,
               "map_name": "Bind", "game_id": "one", "rounds": 20,
               "acs_all": 200, "adr_all": 130, "kast_all": 75,
               "kills_all": 20, "deaths_all": 10, "assists_all": 5, "fk_all": 2}
        self.assertTrue(build_profiles(pd.DataFrame([row])).empty)


if __name__ == "__main__":
    unittest.main()
