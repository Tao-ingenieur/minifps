"""鼠标瞄准策略；独立于渲染引擎，可验证模式切换和离窗行为。"""
from dataclasses import dataclass


@dataclass
class LookPolicy:
    previous_mode: object = None

    def delta(self, dx, dy, *, playing, inside, captured, zoom):
        # 首次启用、重新进入窗口、捕获/释放时跳过一帧，避免光标重定位使视角猛跳。
        active = playing and (inside or captured)
        mode = (active, captured)
        changed = mode != self.previous_mode
        self.previous_mode = mode
        if not active or changed:
            return 0, 0
        sensitivity = 20 if zoom else 35
        return dx * sensitivity, -dy * sensitivity
