"""MiniFPS Woodland：单文件林间猎鸟靶场，Python 3.12 + Ursina。"""
import math
import random
import sys
from copy import deepcopy
from ursina import (
    AmbientLight, DirectionalLight, Entity, Sky, Text, Ursina, Vec3,
    application, camera, color, destroy, invoke, mouse, raycast, scene, time, window,
)
from ursina.collider import BoxCollider
from ursina.models.procedural.cylinder import Cylinder
from ursina.models.procedural.cone import Cone
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader


def main():
    smoke_test = '--smoke-test' in sys.argv
    app = Ursina(title='MiniFPS | Woodland', borderless=False, fullscreen=False,
                 size=(1280, 720), development_mode=False)
    window.color = color.rgb32(162, 189, 196)
    window.exit_button.visible = False
    window.fps_counter.enabled = False
    rng = random.Random(17 if smoke_test else None)
    # 圆柱和圆锥使用程序网格，避免依赖并不存在的同名模型文件。
    meshes = {'cylinder': Cylinder(resolution=16, start=-.5),
              'cone': Cone(resolution=12)}
    cone = meshes['cone']
    normals = []
    for index in range(0, len(cone.vertices), 3):
        a, b, c = (Vec3(v) for v in cone.vertices[index:index + 3])
        normal = (b - a).cross(c - a).normalized()
        normals.extend([normal] * 3)
    cone.normals = normals
    cone.generate()

    def tint(r, g, b):
        return color.rgb32(r, g, b)

    def part(parent=scene, model='cube', position=(0, 0, 0),
             scale=(1, 1, 1), shade=None, rotation=(0, 0, 0), solid=False):
        model = deepcopy(meshes[model]) if model in meshes else model
        return Entity(parent=parent, model=model, position=position, scale=scale,
                      color=shade if shade is not None else color.white,
                      rotation=rotation, collider='box' if solid else None,
                      shader=lit_with_shadows_shader)

    Sky()
    AmbientLight(color=tint(185, 192, 183))
    sun = DirectionalLight(shadows=False, color=tint(210, 193, 159))
    sun.look_at(Vec3(1, -2, -1))
    scene.fog_color = tint(162, 189, 196)
    scene.fog_density = (25, 70)
    part(position=(0, -.5, 12), scale=(65, 1, 70),
         shade=tint(104, 120, 79), solid=True)
    # 小径与散落石块为纯色几何体；天空使用引擎自带资源。
    part(position=(0, .006, 0), scale=(5, .01, 30), shade=tint(155, 144, 108))
    for _ in range(38):
        x, z = rng.uniform(-27, 27), rng.uniform(-14, 40)
        if abs(x) < 4:
            continue
        part(model='sphere', position=(x, .14, z),
             scale=(rng.uniform(.4, 1.3), .35, .7), shade=tint(126, 132, 113))

    # 两侧和远处的树林保留中央射击视野；树干有碰撞，树冠仅用于装饰。
    for side in (-1, 1):
        for index in range(15):
            x = side * rng.uniform(12, 27)
            z = -12 + index * 3.8
            height = rng.uniform(6, 10)
            part(model='cylinder', position=(x, height / 2, z),
                 scale=(.65, height, .65), shade=tint(83, 66, 48), solid=True)
            for tier in range(3):
                part(model='cone', position=(x, height * .58 + tier * 1.4, z),
                     scale=(5 - tier, 3.6, 5 - tier),
                     shade=tint(49 + tier * 5, 81 + tier * 7, 57 + tier * 4))
    for x in (-15, -9, 0, 9, 15):
        part(model='sphere', position=(x, 1.1, 36), scale=(13, 7, 10),
             shade=tint(100, 125, 105))

    # 栅栏标示可活动区域，隐藏碰撞墙防止走出场地。
    for z in (-15, 30):
        for x in range(-12, 13, 3):
            part(position=(x, .65, z), scale=(.16, 1.3, .16), shade=tint(98, 78, 53))
        for y in (.45, .95):
            part(position=(0, y, z), scale=(24, .12, .1), shade=tint(127, 102, 67))
    for pos, size in [((-16, 3, 7), (1, 6, 46)), ((16, 3, 7), (1, 6, 46)),
                      ((0, 3, -15.5), (33, 6, 1)), ((0, 3, 30.5), (33, 6, 1))]:
        wall = Entity(model='cube', position=pos, scale=size, collider='box')
        wall.visible = False

    player = FirstPersonController(position=(0, .1, -10), speed=5,
                                   mouse_sensitivity=Vec3(35, 35, 0))
    player.input = lambda key: None
    player.cursor.enabled = False
    camera.fov = 76
    mouse.locked = not smoke_test
    mouse.visible = smoke_test

    # 多部件猎枪：木质枪托、金属机匣、长枪管、瞄准镜、扳机护圈及持枪手。
    # 全部模型是摄像机子物体且没有碰撞，不干扰射线检测。
    gun = Entity(parent=camera, position=(.25, -.25, .82),
                 rotation=(0, -7, -2), scale=.52)
    wood, dark, steel = tint(118, 72, 39), tint(38, 44, 47), tint(87, 98, 102)
    part(gun, position=(0, -.035, -.32), scale=(.16, .23, .75),
         shade=wood, rotation=(-8, 0, 0))
    part(gun, position=(0, -.09, -.68), scale=(.18, .30, .05), shade=dark)
    part(gun, position=(0, .03, .08), scale=(.145, .15, .47), shade=steel)
    part(gun, position=(0, -.04, .42), scale=(.17, .16, .39), shade=wood)
    part(gun, model='cylinder', position=(0, .11, .91), scale=(.065, 1.18, .065),
         shade=dark, rotation=(90, 0, 0))
    part(gun, model='cylinder', position=(0, .11, 1.51), scale=(.085, .045, .085),
         shade=steel, rotation=(90, 0, 0))
    part(gun, model='circle', position=(0, .11, 1.535), scale=.055,
         shade=color.black, rotation=(0, 180, 0))
    for z in (-.04, .27):
        part(gun, position=(0, .19, z), scale=(.10, .15, .06), shade=dark)
    part(gun, model='cylinder', position=(0, .29, .11), scale=(.12, .60, .12),
         shade=dark, rotation=(90, 0, 0))
    for z in (-.21, .42):
        part(gun, model='cylinder', position=(0, .29, z), scale=(.19, .12, .19),
             shade=dark, rotation=(90, 0, 0))
    part(gun, model='circle', position=(0, .29, -.275), scale=.145,
         shade=tint(45, 117, 130))
    # 护圈用三段细条，避免将扳机区域画成一整块。
    for pos, size in [((0, -.22, .02), (.045, .025, .22)),
                      ((0, -.16, -.08), (.045, .13, .025)),
                      ((0, -.16, .12), (.045, .13, .025))]:
        part(gun, position=pos, scale=size, shade=dark)
    part(gun, position=(0, -.14, 0), scale=(.025, .08, .025), shade=steel,
         rotation=(20, 0, 0))
    part(gun, model='sphere', position=(.15, .06, -.02), scale=.07, shade=steel)
    part(gun, position=(.10, .06, -.02), scale=(.16, .035, .035), shade=steel)
    for pos, size, rotation in [((.07, -.15, -.27), (.18, .19, .28), (15, 0, -15)),
                                ((-.05, -.14, .43), (.20, .15, .27), (0, 0, 15))]:
        part(gun, model='sphere', position=pos, scale=size,
             shade=tint(78, 83, 58), rotation=rotation)
    part(gun, position=(.10, -.31, -.35), scale=(.21, .36, .22),
         shade=tint(65, 77, 59), rotation=(-25, 0, -12))

    # 鸟根节点承担命中碰撞，身体、头、喙、双翼、尾羽都是其子节点。
    birds = []
    def make_bird(position, heading=0):
        bird = Entity(position=position, rotation_y=heading)
        bird.collider = BoxCollider(bird, center=Vec3(0, .05, 0),
                                    size=Vec3(1.35, .85, 1))
        brown, cream = tint(137, 101, 67), tint(222, 201, 153)
        part(bird, model='sphere', scale=(.56, .49, .78), shade=brown)
        part(bird, model='sphere', position=(0, -.06, -.21),
             scale=(.40, .35, .36), shade=cream)
        part(bird, model='sphere', position=(0, .25, -.32), scale=.38, shade=brown)
        part(bird, model='cone', position=(0, .23, -.58),
             scale=(.15, .23, .15), shade=tint(217, 165, 67), rotation=(-90, 0, 0))
        for side in (-1, 1):
            part(bird, model='sphere', position=(side * .155, .30, -.43),
                 scale=.065, shade=tint(15, 20, 18))
            part(bird, model='sphere', position=(side * .175, .312, -.445),
                 scale=.018, shade=color.white)
            part(bird, model='sphere', position=(side * .34, .05, .04),
                 scale=(.55, .13, .49), shade=tint(90, 69, 49),
                 rotation=(0, side * 20, side * -12))
            part(bird, position=(side * .12, -.32, .08), scale=(.035, .20, .035),
                 shade=tint(185, 137, 66))
            part(bird, position=(side * .12, -.41, -.015), scale=(.13, .035, .20),
                 shade=tint(185, 137, 66))
        for x in (-.13, 0, .13):
            part(bird, model='sphere', position=(x, .02, .49),
                 scale=(.14, .09, .55), shade=tint(74, 60, 46), rotation=(15, x * 90, 0))
        birds.append(bird)
        return bird

    slots = [(-6, 2, 3), (-3, 2.6, 8), (2, 2.2, 4), (6, 3, 11),
             (-7, 3.5, 16), (0, 3.2, 18), (7, 2.5, 22), (-3, 2.1, 24)]
    for x, y, z in slots:
        x += rng.uniform(-.5, .5)
        make_bird((x, y, z), rng.uniform(-35, 35))
        # 木桩与横枝让静态鸟有自然的栖息位置。
        part(model='cylinder', position=(x, (y - .43) / 2, z),
             scale=(.18, y - .43, .18), shade=tint(99, 77, 51), solid=True)
        part(position=(x, y - .46, z), scale=(1.3, .11, .16), shade=tint(99, 77, 51))

    # 克制的界面：标题、命中数、细准星与操作提示。
    Entity(parent=camera.ui, model='quad', position=(-.64, .40),
           scale=(.46, .14), color=color.rgba32(20, 30, 25, 175))
    Text('WOODLAND / FIELD 01', position=(-.85, .46), scale=.9,
         color=tint(220, 210, 171))
    counter = Text('BIRDS  00 / 08', position=(-.85, .41), scale=1.15)
    for pos, size in [((-.009, 0), (.009, .0015)), ((.009, 0), (.009, .0015)),
                      ((0, -.009), (.0015, .009)), ((0, .009), (.0015, .009))]:
        Entity(parent=camera.ui, model='quad', position=pos, scale=size,
               color=color.rgba32(245, 242, 219, 215))
    Text('WASD  MOVE     MOUSE  AIM     LMB  FIRE     ESC  EXIT',
         position=(-.85, -.46), scale=.8, color=tint(242, 239, 220))
    shots = 0
    hits = 0
    recoil = 0
    elapsed = 0

    def shoot():
        nonlocal shots, hits, recoil
        shots += 1
        recoil = .07
        hit = raycast(camera.world_position, camera.forward, distance=65,
                      ignore=[player], traverse_target=scene)
        if hit.hit and hit.entity in birds:
            birds.remove(hit.entity)
            destroy(hit.entity)
            hits += 1
        counter.text = f'BIRDS  {hits:02d} / 08    SHOTS  {shots:02d}'
        if not birds:
            counter.text = 'FIELD CLEAR / ESC TO EXIT'

    def handle_input(key):
        if key == 'escape':
            mouse.locked = False
            mouse.visible = True
            application.quit()
        elif key == 'left mouse down' and mouse.locked:
            shoot()

    def update_view():
        nonlocal recoil, elapsed
        elapsed += min(time.dt, .05)
        recoil = max(0, recoil - time.dt * .4)
        gun.z = .82 - recoil
        gun.rotation_x = -recoil * 65
        gun.y = -.25 + math.sin(elapsed * 1.8) * .002

    controls = Entity()
    controls.input = handle_input
    controls.update = update_view

    if smoke_test:
        def verify():
            try:
                assert len(birds) == 8
                assert raycast(Vec3(0, 2, -10), Vec3(0, 0, -1),
                               distance=10, ignore=[player]).hit
                if '--screenshot' in sys.argv:
                    from pathlib import Path
                    from panda3d.core import Filename
                    app.graphicsEngine.renderFrame()
                    app.graphicsEngine.renderFrame()
                    output = Path(sys.argv[sys.argv.index('--screenshot') + 1]).resolve()
                    app.screenshot(namePrefix=Filename.from_os_specific(str(output)),
                                   defaultFilename=False)
                probe = make_bird(camera.world_position + camera.forward * 3)
                shoot()
                assert probe not in birds and len(birds) == 8
                assert hits == 1 and shots == 1
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
