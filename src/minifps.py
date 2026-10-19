"""MiniFPS：单文件 Ursina 靶场，WASD / 鼠标 / 左键 / ESC。"""
import random
import sys
from ursina import (
    AmbientLight, DirectionalLight, Entity, Sky, Text, Ursina, Vec3,
    application, camera, color, destroy, invoke, mouse, raycast, scene, window,
)
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader


def main():
    smoke_test = '--smoke-test' in sys.argv
    app = Ursina(title='MiniFPS', borderless=False, fullscreen=False,
                 size=(1280, 720), development_mode=False)
    window.color = color.rgb32(135, 180, 220)
    window.exit_button.visible = False
    window.fps_counter.enabled = False

    # 房间内部 24 × 24，高 6。带厚度的碰撞箱防止穿过墙壁和地板。
    def block(position, scale, tint):
        return Entity(model='cube', position=position, scale=scale,
                      color=tint, collider='box', shader=lit_with_shadows_shader)

    block((0, -.5, 0), (25, 1, 25), color.rgb32(90, 100, 110))
    block((0, 6.5, 0), (25, 1, 25), color.rgb32(155, 165, 175))
    block((-12.5, 3, 0), (1, 6, 25), color.rgb32(165, 180, 195))
    block((12.5, 3, 0), (1, 6, 25), color.rgb32(165, 180, 195))
    block((0, 3, -12.5), (25, 6, 1), color.rgb32(145, 160, 180))
    block((0, 3, 12.5), (25, 6, 1), color.rgb32(145, 160, 180))

    # 纯色天空与基础光照；室内主要看到四面墙及天花板。
    Sky(texture=None, color=color.rgb32(135, 180, 220))
    AmbientLight(color=color.rgba32(180, 180, 180, 255))
    sun = DirectionalLight(shadows=False, color=color.rgba32(150, 150, 150, 255))
    sun.look_at(Vec3(1, -2, 1))

    # 在相互隔开的网格中抽样，靶子不重叠，也不占用出生点。
    targets = []
    slots = [(x, z) for x in (-9, -6, -3, 0, 3, 6, 9)
             for z in (-3, 0, 3, 6, 9)]
    for x, z in random.sample(slots, 8):
        targets.append(block((x, .75, z), (1.5, 1.5, 1.5),
                             color.rgb32(230, 100, 65)))

    player = FirstPersonController(position=(0, .1, -9), speed=5,
                                   mouse_sensitivity=Vec3(40, 40, 0))
    player.jump_height = 0  # 仅保留基础移动。
    player.input = lambda key: None  # 禁用默认控制器的空格跳跃。
    player.cursor.enabled = False
    camera.fov = 85
    mouse.locked = not smoke_test
    mouse.visible = smoke_test

    # 枪体没有碰撞箱，不参与命中检测。
    Entity(parent=camera, model='cube', color=color.rgb32(50, 60, 70),
           position=(.35, -.26, .65), scale=(.16, .18, .55))
    Text('+', parent=camera.ui, origin=(0, 0), scale=1.5)
    counter = Text(text=f'Targets: {len(targets)} / 8',
                   position=(-.85, .46), scale=1.3)
    Text('WASD: Move | Mouse: Aim | LMB: Shoot | ESC: Exit',
         position=(-.85, -.46), scale=.9)

    def shoot():
        # 即时命中子弹：检测镜头正前方最近的碰撞物，墙壁阻挡射击。
        hit = raycast(camera.world_position, camera.forward, distance=60,
                      ignore=[player], traverse_target=scene)
        if hit.hit and hit.entity in targets:
            targets.remove(hit.entity)
            destroy(hit.entity)
            counter.text = f'Targets: {len(targets)} / 8'
            if not targets:
                counter.text = 'All targets cleared! ESC to exit'

    def handle_input(key):
        if key == 'escape':
            mouse.locked = False
            mouse.visible = True
            application.quit()
        elif key == 'left mouse down' and mouse.locked:
            shoot()

    # Entity.input 接收 Ursina 的输入事件。
    controls = Entity()
    controls.input = handle_input

    # 自检不锁定鼠标，运行真实渲染与碰撞检测后自动退出。
    if smoke_test:
        def verify():
            try:
                assert len(targets) == 8
                assert raycast(Vec3(0, 2, -9), Vec3(0, 0, -1),
                               distance=10, ignore=[player]).hit
                probe = block(camera.world_position + camera.forward * 3,
                              (1, 1, 1), color.red)
                targets.append(probe)
                shoot()
                assert probe not in targets and len(targets) == 8
                print('SMOKE TEST PASSED', flush=True)
            except Exception:
                import traceback
                traceback.print_exc()
                sys.exit(1)
            application.quit()
        invoke(verify, delay=1)

    app.run()


if __name__ == '__main__':
    main()

