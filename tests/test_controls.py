"""覆盖导致窗口模式无法正常转动枪口的回归。"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from woodland.controls import LookPolicy


class LookTests(unittest.TestCase):
    def setUp(self):
        self.policy = LookPolicy()

    def step(self, dx=.1, dy=.05, **kwargs):
        options = dict(playing=True, inside=True, captured=False, zoom=False)
        options.update(kwargs)
        return self.policy.delta(dx, dy, **options)

    def test_windowed_aim_without_right_button(self):
        self.step(0, 0)
        self.assertEqual(self.step(), (3.5, -1.75))
        self.assertEqual(self.step(0, 0), (0, 0))

    def test_outside_and_reentry_do_not_jump(self):
        self.step(); self.step()
        self.assertEqual(self.step(inside=False), (0, 0))
        self.assertEqual(self.step(10, 10), (0, 0))
        self.assertEqual(self.step(), (3.5, -1.75))

    def test_pause_and_resume(self):
        self.step()
        self.assertEqual(self.step(playing=False), (0, 0))
        self.assertEqual(self.step(), (0, 0))
        self.assertEqual(self.step(), (3.5, -1.75))

    def test_fullscreen_and_zoom_capture(self):
        self.step(captured=True, inside=False)
        self.assertEqual(self.step(captured=True, inside=False), (3.5, -1.75))
        self.assertEqual(self.step(captured=True, inside=False, zoom=True), (2, -1))
        self.assertEqual(self.step(), (0, 0))  # 释放捕获跳过重定位帧。
        self.assertEqual(self.step(), (3.5, -1.75))


if __name__ == '__main__':
    unittest.main()
