"""WASD 与鼠标视角。自由鼠标、捕获和缩放不再与是否允许瞄准混为一谈。"""
from ursina import Vec3, camera, mouse
from ursina.prefabs.first_person_controller import FirstPersonController
from .controls import LookPolicy


class PlayerController(FirstPersonController):
    def __init__(self, smoke_test=False, **kwargs):
        super().__init__(**kwargs)
        self.smoke_test = smoke_test
        self.look_policy = LookPolicy()
        self.playing = self.captured = self.zoom = False
        self.look_sensitivity = 35
        self.cursor.enabled = False
        self.ignore = True
        self.mouse_sensitivity = Vec3(0, 0, 0)
        mouse.locked = False
        mouse.visible = True
        camera.fov = 76

    def input(self, key):
        # 不启用引擎默认的跳跃；其余按键由游戏统一分发。
        pass

    def configure_pointer(self, playing, fullscreen, zoom):
        captured = playing and (fullscreen or zoom)
        if (playing, captured) != (self.playing, self.captured):
            # 暂停期间实体不执行 update，必须在配置切换时主动清理旧采样状态。
            self.look_policy.previous_mode = None
        self.playing, self.zoom = playing, zoom
        self.captured = captured
        self.look_sensitivity = 20 if zoom else 35
        locked = self.captured and not self.smoke_test
        if mouse.locked != locked:
            mouse.locked = locked
        if mouse.visible != (not locked):
            mouse.visible = not locked
        camera.fov = 50 if zoom and playing else 76

    def update_look(self, delta=None, inside=None):
        # 窗口内直接移动鼠标即可瞄准；光标可以离窗，离窗时不消费陈旧位移。
        delta = mouse.velocity if delta is None else delta
        inside = not mouse.is_outside if inside is None else inside
        yaw, pitch = self.look_policy.delta(delta[0], delta[1], playing=self.playing,
                                           inside=inside, captured=self.captured, zoom=self.zoom)
        self.rotation_y += yaw
        self.camera_pivot.rotation_x = max(-89, min(89, self.camera_pivot.rotation_x + pitch))

    def read_pointer(self):
        return mouse.velocity, not mouse.is_outside

    def update(self):
        delta, inside = self.read_pointer()
        self.update_look(delta, inside)
        # 保留引擎的 WASD、重力和碰撞；鼠标仅由上面消费一次。
        self.mouse_sensitivity = Vec3(0, 0, 0)
        super().update()
