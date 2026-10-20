"""MiniFPS Woodland：单文件林间猎鸟靶场，Python 3.12 + Ursina。"""
import math
import random
import sys
from copy import deepcopy
from dataclasses import dataclass
from time import perf_counter
from ursina import (
    AmbientLight, Button, DirectionalLight, Entity, Sky, Text, Ursina, Vec3,
    application, camera, color, destroy, held_keys, invoke, mouse, raycast, scene, time, window,
)
from ursina.collider import BoxCollider
from ursina.models.procedural.cylinder import Cylinder
from ursina.models.procedural.cone import Cone
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader

VERSION = '0.3.0'
TARGET_COUNT = 8
ROUND_SECONDS = 120
SHOT_COOLDOWN = .30


@dataclass
class GameRound:
    """与渲染分离的计分规则，传入单调时钟，便于精确验证超时和重开。"""
    state: str = 'ready'
    shots: int = 0
    hits: int = 0
    streak: int = 0
    best_streak: int = 0
    combo_points: int = 0
    started_at: float = 0
    finished_elapsed: float = 0
    last_shot: float = -float('inf')

    def start(self, now):
        self.state = 'playing'
        self.shots = self.hits = self.streak = self.best_streak = self.combo_points = 0
        self.started_at = now
        self.finished_elapsed = 0
        self.last_shot = -float('inf')

    def elapsed(self, now):
        if self.state == 'ready':
            return 0
        if self.state != 'playing':
            return self.finished_elapsed
        return min(ROUND_SECONDS, max(0, now - self.started_at))

    def tick(self, now):
        if self.state == 'playing' and now - self.started_at >= ROUND_SECONDS:
            self.finished_elapsed = ROUND_SECONDS
            self.state = 'timeout'

    def can_fire(self, now):
        self.tick(now)
        return self.state == 'playing' and now - self.last_shot >= SHOT_COOLDOWN - 1e-9

    def fire(self, hit, now):
        if not self.can_fire(now):
            return None  # 冷却期点击、结算后点击不计空枪，也不改变分数。
        self.last_shot = now
        self.shots += 1
        if hit:
            self.hits += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            combo = min(self.streak - 1, 4) * 25
            self.combo_points += combo
            if self.hits == TARGET_COUNT:
                self.finished_elapsed = self.elapsed(now)
                self.state = 'cleared'
            return 100 + combo
        self.streak = 0
        return -30

    @property
    def accuracy(self):
        return self.hits / self.shots if self.shots else 0

    @property
    def score(self):
        return self.hits * 100 + self.combo_points - (self.shots - self.hits) * 30

    @property
    def bonuses(self):
        if self.state != 'cleared':
            return 0, 0, 0
        # 用时只占总分的小部分；超过 90 秒仍可清场，但没有速度奖励。
        speed = int(300 * max(0, 1 - self.finished_elapsed / 90))
        accuracy = int(200 * self.accuracy + .5)
        perfect = 150 if self.shots == TARGET_COUNT else 0
        return speed, accuracy, perfect

    @property
    def total(self):
        return max(0, self.score + sum(self.bonuses))


def main():
    smoke_test = '--smoke-test' in sys.argv
    app = Ursina(title=f'MiniFPS | Woodland v{VERSION}', borderless=False, fullscreen=False,
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
    player.ignore = True
    mouse.locked = False
    mouse.visible = True

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
    perches = []
    for x, y, z in slots:
        x += rng.uniform(-.5, .5)
        perches.append((x, y, z))
        make_bird((x, y, z), rng.uniform(-35, 35))
        # 木桩与横枝让静态鸟有自然的栖息位置。
        part(model='cylinder', position=(x, (y - .43) / 2, z),
             scale=(.18, y - .43, .18), shade=tint(99, 77, 51), solid=True)
        part(position=(x, y - .46, z), scale=(1.3, .11, .16), shade=tint(99, 77, 51))

    # HUD 保留实时分数、准确率、剩余时间和连击，结算页解释每项得分。
    hud = Entity(parent=camera.ui)
    Entity(parent=hud, model='quad', position=(-.55, .38),
           scale=(.64, .21), color=color.rgba32(20, 30, 25, 195))
    Text(f'WOODLAND / v{VERSION}', parent=hud, position=(-.85, .46), scale=.85,
         color=tint(220, 210, 171))
    counter = Text(parent=hud, position=(-.85, .42), scale=1)
    status = Text(parent=hud, position=(-.85, .38), scale=.85)
    feedback = Text(parent=hud, position=(-.85, .33), scale=.85, color=tint(220, 210, 171))
    reticle = Entity(parent=hud)
    for pos, size in [((-.009, 0), (.009, .0015)), ((.009, 0), (.009, .0015)),
                      ((0, -.009), (.0015, .009)), ((0, .009), (.0015, .009))]:
        Entity(parent=reticle, model='quad', position=pos, scale=size,
               color=color.rgba32(245, 242, 219, 215))
    Text('WASD  MOVE     MOUSE  AIM     LMB  FIRE     ESC  EXIT', parent=hud,
         position=(-.85, -.46), scale=.8, color=tint(242, 239, 220))

    # 同一个菜单用于开局和结算，按钮之外也支持 Enter / R 键。
    menu = Entity(parent=camera.ui)
    Entity(parent=menu, model='quad', scale=(4, 2), z=.2,
           color=color.rgba32(8, 15, 13, 170))
    Entity(parent=menu, model='quad', scale=(1.10, .87), z=.1,
           color=tint(27, 40, 34))
    menu_title = Text(parent=menu, text='WOODLAND', origin=(0, 0),
                      position=(0, .33), z=-.1, scale=2, color=tint(233, 219, 169))
    menu_subtitle = Text(parent=menu, origin=(0, 0), position=(0, .25), z=-.1, scale=1.1)
    details = Text(parent=menu, position=(-.46, .17), z=-.1, scale=.95, line_height=1.4)
    primary = Button(parent=menu, text='START / ENTER', position=(-.21, -.31),
                     z=-.1, scale=(.36, .065), color=tint(88, 114, 78))
    Button(parent=menu, text='EXIT / ESC', position=(.21, -.31),
           z=-.1, scale=(.36, .065), color=tint(78, 87, 77), on_click=application.quit)
    Text(parent=menu, text='8 BIRDS  /  120 SECONDS  /  AIM BEFORE FIRING',
         origin=(0, 0), position=(0, -.39), z=-.1, scale=.75, color=tint(189, 193, 168))
    game = GameRound()
    recoil = 0
    sway_time = 0

    def refresh_hud(now):
        remaining = max(0, ROUND_SECONDS - game.elapsed(now))
        counter.text = f'SCORE {game.score:04d}     BIRDS {game.hits:02d} / 08'
        status.text = (f'TIME {remaining:05.1f}s    ACC {game.accuracy:.0%}'
                       f'    STREAK {game.streak}    SHOTS {game.shots}')

    def show_menu():
        menu.enabled = True
        hud.enabled = False
        player.ignore = True
        reticle.enabled = False
        gun.enabled = False
        mouse.locked = False
        mouse.visible = True
        if game.state == 'ready':
            menu_title.text = 'WOODLAND'
            menu_subtitle.text = 'PRECISION HUNT / 8 TARGETS'
            details.text = ('Hit a bird: +100 points\n'
                            'Consecutive hits: +25 / +50 / +75 / +100 max\n'
                            'Miss: -30 points and reset streak\n\n'
                            'Clear bonuses: speed up to +300, accuracy up to +200\n'
                            'Perfect 8 shots / 8 hits: +150 extra\n'
                            '120 seconds. Timer starts when you press START.\n'
                            'WASD move, mouse aim, left click fire.')
            primary.text = 'START / ENTER'
        else:
            speed, accuracy, perfect = game.bonuses
            menu_title.text = 'GAME OVER'
            outcome = 'ALL BIRDS HIT' if game.state == 'cleared' else 'TIME UP'
            menu_subtitle.text = f'{outcome}  /  TOTAL {game.total} PTS'
            misses = game.shots - game.hits
            details.text = (f'Time {game.finished_elapsed:.1f}s   |   Birds {game.hits}/8'
                            f'   |   Accuracy {game.accuracy:.1%}\n'
                            f'Hit points:                      +{game.hits * 100}\n'
                            f'Combo bonus (best streak {game.best_streak}):    +{game.combo_points}\n'
                            f'Miss penalty ({misses} misses):              -{misses * 30}\n'
                            f'Clear speed bonus:               +{speed}\n'
                            f'Clear accuracy bonus:            +{accuracy}\n'
                            f'Perfect round bonus:             +{perfect}\n'
                            'R / ENTER or the button starts a fresh round.')
            primary.text = 'PLAY AGAIN / R'

    def start_round():
        nonlocal recoil, sway_time
        # 只重建鸟；树林、枪、木桩和 UI 复用，避免重开后实体不断累积。
        for bird in list(birds):
            destroy(bird)
        birds.clear()
        for position in perches:
            make_bird(position, rng.uniform(-35, 35))
        player.position = (0, 0, -10)
        player.rotation = (0, 0, 0)
        player.camera_pivot.rotation = (0, 0, 0)
        player.air_time = 0
        for key in ('w', 'a', 's', 'd'):
            held_keys[key] = 0
        recoil = sway_time = 0
        game.start(perf_counter())
        menu.enabled = False
        hud.enabled = True
        player.ignore = False
        reticle.enabled = gun.enabled = True
        mouse.locked = not smoke_test
        mouse.visible = smoke_test
        feedback.text = 'HIT +100   /   MISS -30   /   BUILD A STREAK'
        feedback.color = tint(220, 210, 171)
        refresh_hud(perf_counter())

    primary.on_click = lambda: start_round() if game.state != 'playing' else None

    def shoot(now=None):
        nonlocal recoil
        now = perf_counter() if now is None else now
        if not game.can_fire(now):
            if game.state == 'timeout':
                show_menu()
            return
        hit = raycast(camera.world_position, camera.forward, distance=65,
                      ignore=[player], traverse_target=scene)
        target = hit.entity if hit.hit and hit.entity in birds else None
        delta = game.fire(target is not None, now)
        recoil = .07
        if target is not None:
            birds.remove(target)
            destroy(target)
            feedback.text = f'HIT +{delta}   /   STREAK {game.streak}'
            feedback.color = tint(189, 224, 146)
        else:
            feedback.text = 'MISS -30   /   STREAK RESET'
            feedback.color = tint(241, 159, 131)
        refresh_hud(now)
        if game.state == 'cleared':
            show_menu()

    def handle_input(key):
        if key == 'escape':
            mouse.locked = False
            mouse.visible = True
            application.quit()
        elif key in ('enter', 'r') and game.state != 'playing':
            start_round()
        elif key == 'left mouse down' and mouse.locked:
            shoot()

    def update_view():
        nonlocal recoil, sway_time
        if game.state != 'playing':
            return
        now = perf_counter()
        game.tick(now)
        refresh_hud(now)
        if game.state == 'timeout':
            show_menu()
            return
        sway_time += min(time.dt, .05)
        recoil = max(0, recoil - time.dt * .4)
        gun.z = .82 - recoil
        gun.rotation_x = -recoil * 65
        gun.y = -.25 + math.sin(sway_time * 1.8) * .002

    controls = Entity()
    controls.input = handle_input
    controls.update = update_view
    refresh_hud(perf_counter())
    show_menu()

    if smoke_test:
        def screenshot(path):
            from pathlib import Path
            from panda3d.core import Filename
            app.graphicsEngine.renderFrame()
            app.graphicsEngine.renderFrame()
            app.screenshot(namePrefix=Filename.from_os_specific(str(Path(path).resolve())),
                           defaultFilename=False)

        def verify():
            try:
                assert game.state == 'ready' and menu.enabled and player.ignore
                if '--menu-screenshot' in sys.argv:
                    screenshot(sys.argv[sys.argv.index('--menu-screenshot') + 1])
                mouse.hovered_entity = primary
                app.input('left mouse down')
                app.input('left mouse up')
                mouse.hovered_entity = None
                assert game.state == 'playing' and len(birds) == TARGET_COUNT
                assert game.shots == 0  # 点击开始按钮不能被当作一次射击。
                assert raycast(Vec3(0, 2, -10), Vec3(0, 0, -1),
                               distance=10, ignore=[player]).hit
                if '--screenshot' in sys.argv:
                    screenshot(sys.argv[sys.argv.index('--screenshot') + 1])
                now = game.started_at
                # 把真实鸟移到准星前方，测试实际射线、连击、清场与结果页。
                for index, bird in enumerate(list(birds)):
                    bird.world_position = camera.world_position + camera.forward * 3
                    shoot(now + index)
                    assert bird not in birds
                assert game.state == 'cleared' and game.hits == 8 and not birds
                assert menu.enabled and player.ignore and not mouse.locked
                score = game.total
                shoot(now + 20)
                assert game.total == score and game.shots == 8
                if '--result-screenshot' in sys.argv:
                    screenshot(sys.argv[sys.argv.index('--result-screenshot') + 1])
                # 连续重开不能残留旧目标、旧分数或冻结的计时器。
                for _ in range(3):
                    handle_input('r')
                    assert len(birds) == 8 and game.score == 0 and game.shots == 0
                    assert game.state == 'playing' and not menu.enabled and not player.ignore
                    # 再次结束本局，才能从结算页使用 R 开启下一局。
                    game.tick(game.started_at + ROUND_SECONDS)
                    show_menu()
                game.tick(game.started_at + ROUND_SECONDS)
                show_menu()
                assert game.state == 'timeout' and menu.enabled and game.total == 0
                print('SMOKE TEST PASSED: scoring, clear, restart, timeout', flush=True)
            except Exception:
                import traceback
                traceback.print_exc()
                sys.exit(1)
            application.quit()
        invoke(verify, delay=1)
    app.run()


if __name__ == '__main__':
    main()
