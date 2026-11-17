"""Regression tests for the paired-game prediction experiment."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import pandas as pd


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "07_compare_predictors.py"
spec = importlib.util.spec_from_file_location("compare_predictors", SCRIPT)
prediction = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prediction)


def example_compositions() -> pd.DataFrame:
    common = dict(Date="2021-01-01 13:00:00", Patch="Patch 2.0", Map="Ascent")
    rows = [
        dict(GameID="g1", MatchID="m1", team="ZZZ", side="Team1",
             agents_str="viper|sage|sova|omen|raze", won=0, **common),
        dict(GameID="g1", MatchID="m1", team="AAA", side="Team2",
             agents_str="jett|skye|cypher|breach|astra", won=1, **common),
        dict(GameID="g2", MatchID="m2", team="BBB", side="Team1",
             agents_str="jett|skye|cypher|breach|astra", won=1,
             Date="2021-01-02 09:00:00", Patch="Patch 2.0", Map="Bind"),
        dict(GameID="g2", MatchID="m2", team="CCC", side="Team2",
             agents_str="viper|sage|sova|omen|raze", won=0,
             Date="2021-01-02 09:00:00", Patch="Patch 2.0", Map="Bind"),
    ]
    return pd.DataFrame(rows)


class PredictionDataTests(unittest.TestCase):
    def test_team_choice_uses_team_code_not_postgame_side(self):
        games = prediction.make_game_table(example_compositions().sample(frac=1, random_state=3))
        self.assertEqual(games["won"].tolist(), [1, 1])
        self.assertEqual(games["agent_jett"].tolist(), [1, 1])
        self.assertEqual(games["agent_viper"].tolist(), [-1, -1])
        self.assertEqual(games["date"].dt.hour.tolist(), [0, 0])

    def test_opposing_labels_must_disagree(self):
        bad = example_compositions()
        bad.loc[(bad.GameID == "g1") & (bad.team == "ZZZ"), "won"] = 1
        with self.assertRaisesRegex(ValueError, "opposing win labels"):
            prediction.make_game_table(bad)

    def test_split_uses_whole_dates_and_disjoint_matches(self):
        games = prediction.make_game_table(example_compositions())
        train, test = prediction.temporal_split(games, 0.5)
        self.assertEqual(train.GameID.tolist(), ["g1"])
        self.assertEqual(test.GameID.tolist(), ["g2"])
        self.assertLess(train.date.max(), test.date.min())
        bad = games.copy()
        bad.loc[bad.GameID == "g2", "MatchID"] = "m1"
        with self.assertRaisesRegex(ValueError, "MatchID"):
            prediction.temporal_split(bad, 0.5)

    def test_bootstrap_resamples_matches_reproducibly(self):
        pred = pd.DataFrame({"MatchID": ["m1", "m1", "m2", "m2"],
                             "won": [0, 1, 0, 1],
                             "Train prevalence": [0.5] * 4,
                             "Good model": [0.1, 0.9, 0.2, 0.8]})
        a = prediction.block_bootstrap_log_loss(pred, ["Good model"], n_boot=200, seed=7)
        b = prediction.block_bootstrap_log_loss(pred, ["Good model"], n_boot=200, seed=7)
        pd.testing.assert_frame_equal(a, b)
        self.assertGreater(a.loc[0, "delta_ci_low"], 0)
        self.assertEqual(a.loc[0, "bootstrap_groups"], 2)

    def test_diagnostics_preserve_test_counts(self):
        pred = pd.DataFrame({"GameID": ["a", "b", "c", "d"],
                             "MatchID": ["m1", "m1", "m2", "m2"],
                             "date": pd.to_datetime(["2021-01-01", "2021-01-01", "2021-02-01", "2021-02-01"]),
                             "Map": ["Ascent", "Ascent", "Bind", "Bind"],
                             "won": [0, 1, 0, 1], "Train prevalence": [0.5] * 4,
                             "Good model": [0.1, 0.9, 0.2, 0.8]})
        by_map, by_month, cal = prediction.diagnostic_tables(pred, ["Train prevalence", "Good model"])
        self.assertEqual(by_map.loc[by_map.model == "Good model", "n_games"].sum(), 4)
        self.assertEqual(by_month.loc[by_month.model == "Good model", "n_games"].sum(), 4)
        self.assertEqual(cal.loc[cal.model == "Good model", "n_games"].sum(), 4)


if __name__ == "__main__":
    unittest.main()
