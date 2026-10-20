"""用标准库验证计分规则，无需创建游戏窗口。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from minifps import GameRound, ROUND_SECONDS


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.game = GameRound()
        self.game.start(1000)

    def test_hit_combo_cap_and_miss_reset(self):
        g = self.game
        self.assertEqual([g.fire(True, 1000 + i) for i in range(6)],
                         [100, 125, 150, 175, 200, 200])
        self.assertEqual(g.fire(False, 1006), -30)
        self.assertEqual(g.streak, 0)
        self.assertEqual(g.fire(True, 1007), 100)
        self.assertEqual(g.best_streak, 6)
        self.assertEqual(g.score, 1020)

    def test_misses_can_be_negative_but_final_total_has_zero_floor(self):
        g = self.game
        g.fire(False, 1000)
        self.assertEqual(g.score, -30)
        g.tick(1000 + ROUND_SECONDS)
        self.assertEqual(g.total, 0)
        self.assertEqual(g.bonuses, (0, 0, 0))

    def test_perfect_clear_bonus_and_frozen_result(self):
        g = self.game
        for i in range(8):
            g.fire(True, 1000 + i * 5)
        self.assertEqual(g.state, 'cleared')
        self.assertEqual(g.score, 1350)
        self.assertEqual(g.bonuses, (183, 200, 150))
        self.assertEqual(g.total, 1883)
        self.assertEqual(g.elapsed(9999), 35)
        self.assertIsNone(g.fire(True, 9999))
        self.assertEqual(g.shots, 8)
        self.assertEqual(g.total, 1883)

    def test_inaccurate_clear_has_lower_accuracy_bonus_and_no_perfect(self):
        g = self.game
        for i in range(8):
            g.fire(False, 1000 + i * 2)
            g.fire(True, 1001 + i * 2)
        self.assertEqual(g.accuracy, .5)
        self.assertEqual(g.score, 560)
        self.assertEqual(g.bonuses, (250, 100, 0))
        self.assertEqual(g.total, 910)

    def test_speed_bonus_stops_at_90_seconds_but_clear_is_allowed(self):
        g = self.game
        for i in range(7):
            g.fire(True, 1000 + i)
        g.fire(True, 1090)
        self.assertEqual(g.state, 'cleared')
        self.assertEqual(g.bonuses, (0, 200, 150))

    def test_exact_deadline_rejects_last_hit_and_clear_bonuses(self):
        g = self.game
        for i in range(7):
            g.fire(True, 1000 + i)
        self.assertIsNone(g.fire(True, 1120))
        self.assertEqual(g.state, 'timeout')
        self.assertEqual(g.hits, 7)
        self.assertEqual(g.elapsed(9999), 120)
        self.assertEqual(g.bonuses, (0, 0, 0))

    def test_cooldown_ignores_clicks_without_penalty(self):
        g = self.game
        g.fire(True, 1000)
        self.assertIsNone(g.fire(False, 1000.1))
        self.assertEqual((g.shots, g.hits, g.streak, g.score), (1, 1, 1, 100))
        self.assertEqual(g.fire(False, 1000.3), -30)

    def test_ready_and_restarting_reset_every_scoring_field(self):
        g = GameRound()
        self.assertIsNone(g.fire(True, 10))
        self.assertEqual(g.elapsed(10), 0)
        g.start(20)
        g.fire(True, 20)
        g.fire(False, 21)
        g.tick(140)
        g.start(500)
        self.assertEqual(g.state, 'playing')
        self.assertEqual((g.shots, g.hits, g.streak, g.best_streak, g.combo_points),
                         (0, 0, 0, 0, 0))
        self.assertEqual(g.elapsed(501), 1)
        self.assertEqual(g.score, 0)
        self.assertEqual(g.bonuses, (0, 0, 0))
        self.assertEqual(g.fire(True, 500), 100)


if __name__ == '__main__':
    unittest.main()
