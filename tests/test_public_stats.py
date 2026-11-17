"""Checks that map explorer denominators and time filters stay honest."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from valorant_mining.public_stats import build_public_data, wilson_interval


class PublicStatsTests(unittest.TestCase):
    def test_pick_and_win_denominators_are_distinct(self):
        frame = pd.DataFrame([
            {"GameID": 1, "Date": "2020-10-01", "Map": "Ascent", "EventName": "Event A",
             "agents_str": "jett|omen|sage|sova|cypher", "won": 1},
            {"GameID": 1, "Date": "2020-10-01", "Map": "Ascent", "EventName": "Event A",
             "agents_str": "raze|omen|sage|sova|cypher", "won": 0},
            {"GameID": 2, "Date": "2021-10-01", "Map": "Ascent", "EventName": "Event B",
             "agents_str": "jett|omen|sage|sova|cypher", "won": None},
        ])
        all_data = build_public_data(frame)["maps"]["Ascent"]["all"]
        jett = next(a for a in all_data["agents"] if a["name"] == "jett")
        self.assertEqual((all_data["games"], all_data["teams"], all_data["labeled_teams"]), (2, 3, 2))
        self.assertAlmostEqual(jett["pick_rate"], 2 / 3)
        self.assertEqual((jett["labeled"], jett["wins"], jett["win_rate"]), (1, 1, 1))
        self.assertEqual(build_public_data(frame)["maps"]["Ascent"]["2020"]["teams"], 2)
        self.assertEqual(build_public_data(frame)["maps"]["Fracture"]["2020"]["teams"], 0)

    def test_wilson_interval_contains_observed_rate(self):
        low, high = wilson_interval(54, 100)
        self.assertLess(low, .54)
        self.assertGreater(high, .54)
        self.assertEqual(wilson_interval(0, 0), (0, 0))


if __name__ == "__main__":
    unittest.main()
