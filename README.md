# MiniFPS Woodland v0.3.0

一个极简 Windows 第一人称林间猎鸟靶场，使用 Python + Ursina。可辨认的多部件 3D 猎枪包含木质枪托、金属枪管、瞄准镜和持枪手；鸟有头、喙、眼睛、双翼、脚与尾羽，栖息在林间木桩上。每次启动 8 只鸟的位置与朝向略有变化。

WASD 移动，鼠标瞄准，左键射击。启动后先显示规则菜单，点击 START 或按 Enter 开始一局 120 秒挑战。击中全部 8 只鸟或用时结束后显示 Game Over、逐项得分和总分，可按 R / Enter 或点击 PLAY AGAIN 重新开始。ESC 释放鼠标并退出。

当前版本 **v0.3.0**。每个版本的具体改动见 [更新日志](CHANGELOG.md)，可下载历史源码或查看 [GitHub Releases](https://github.com/Tao-ingenieur/minifps/releases)。前两版已根据原始提交补记历史记录。

![游戏实机画面](docs/preview.png)
![清场结算](docs/results.png)

## 积分规则

积分侧重命中与准确率，速度只作为清场加分，不乘算整局成绩。

| 项目 | 规则 |
| --- | --- |
| 命中小鸟 | +100 分 |
| 连续命中 | 第 2、3、4 次分别额外 +25、+50、+75；第 5 次起每次额外 +100 |
| 空枪 | -30 分并清空当前连击；打到地面、木桩、树或边界也算空枪 |
| 清场速度奖励 | `floor(300 × max(0, 1 - 用时秒数 / 90))`，最多 +300；90 秒之后为 0 |
| 清场准确率奖励 | `200 × 命中数 / 有效射击数`，四舍五入到整数，最多 +200 |
| 全中额外奖励 | 8 发命中 8 只鸟，额外 +150 |
| 超时 | 120 秒结束本局，保留命中/连击分和空枪扣分，不发任何清场奖励 |
| 最终总分 | `max(0, 命中分 + 连击分 - 空枪扣分 + 清场奖励)` |

实时分数允许为负，避免先乱开枪再命中逃避惩罚；最终结算最低 0 分。准确率在未开枪时显示 0%。射击间隔 0.30 秒，冷却期点击不算发数或空枪；结算后无法继续射击刷分。计时使用单调时钟，游戏加载时间不计入比赛，开始后不会因为低帧率而变慢。

例如：40 秒内用 8 发全部命中，得分为 `800 命中 + 550 连击 + 166 用时 + 200 准确率 + 150 全中 = 1866 分`。

清场显示 **GAME OVER / ALL BIRDS HIT**，超时显示 **GAME OVER / TIME UP**。结算后释放鼠标、停止移动并冻结得分和用时。重新开始会重置全部计分状态、8 只鸟、玩家位置和视角；树林与木桩复用。

## 目录

```text
simplei-fps/
├── minifps/                  # 仅此目录上传 GitHub
│   ├── src/minifps.py        # 完整单文件游戏，无需外部贴图
│   ├── requirements.txt
│   ├── requirements-build.txt
│   ├── build.ps1
│   └── README.md
└── minifps-local/            # 不上传 GitHub
    ├── .venv/               # 本机依赖环境
    ├── build/               # PyInstaller 中间产物
    ├── dist/MiniFPS.exe     # 可以直接分发的单文件程序
    └── MiniFPS.spec
```

## 安装与运行

开发电脑使用 Windows 10/11 x64，安装 Python 3.12 x64（python.org 官方安装器）；游戏玩家运行 exe 不需要安装 Python。

在 `minifps` 目录打开 PowerShell。以下命令无需激活虚拟环境：

```powershell
py -3.12 -m venv ..\minifps-local\.venv
& ..\minifps-local\.venv\Scripts\python.exe -m pip install --upgrade pip
& ..\minifps-local\.venv\Scripts\python.exe -m pip install -r requirements.txt
& ..\minifps-local\.venv\Scripts\python.exe src\minifps.py
```

在规则菜单点击 START 或按 Enter 后，鼠标锁定到窗口，W/S 前后移动，A/D 左右平移，鼠标转动视角，单击左键射击。准星下的第一个碰撞物决定命中；猎枪模型不参与碰撞。射中小鸟后小鸟消失，清场或超时后显示结算页，可按 R / Enter 或点击按钮开启新一局。ESC 直接退出并释放鼠标。

## 完整单文件代码

复制下面代码到 `minifps.py`，安装 Ursina 后可独立运行，不依赖本仓库其他文件。

```python
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
```

## 打包独立 Windows exe

1. 在 Windows x64 上按前述步骤创建环境并确认源码游戏可以运行。
2. 在 `minifps` 目录安装打包依赖：

   ```powershell
   & ..\minifps-local\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
   ```

3. 执行构建脚本。ExecutionPolicy 只对这次 PowerShell 子进程生效：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
   ```

4. 产物为 `..\minifps-local\dist\MiniFPS.exe`。脚本使用 `--onefile --windowed` 并收集 Ursina / Panda3D 的模型、字体、动态库等内置资源；不需要手动复制素材。首次构建可能需要几分钟，单文件启动时需要短暂解压。
5. 双击 exe，检查移动、鼠标瞄准、射击消靶、墙壁碰撞和 ESC 退出。将 exe 复制到未安装 Python 的 Windows 电脑再测试；运行需要正常的显卡驱动。
6. 仅分发 `MiniFPS.exe` 即可；不必分发虚拟环境或源码。第三方引擎随包许可证位于打包资源中，可在对外分发时同时附带 `THIRD_PARTY_NOTICES.md`。

如双击无窗口或闪退，构建控制台版并从 PowerShell 启动，查看错误：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -Console
& ..\minifps-local\dist\MiniFPS.exe
```

控制台版与正式版输出文件名相同，后一次构建覆盖前一次。重新执行不带 `-Console` 的构建得到正式版。

可选自动自检（真实窗口短暂出现，检查按钮开局、场地边界、真实鸟形目标命中、清场结算、连续重开和超时，然后退出）：

```powershell
& ..\minifps-local\.venv\Scripts\python.exe src\minifps.py --smoke-test
# 控制台版 exe 也支持：
& ..\minifps-local\dist\MiniFPS.exe --smoke-test
```

## GitHub

Git 仓库根目录为 `minifps`，同级 `minifps-local` 不在版本控制范围内。`.gitignore` 也排除 exe、缓存、虚拟环境和构建产物。公开仓库只包含源码、依赖清单及说明。

参考：[Ursina API](https://www.ursinaengine.org/api_reference.html)、[PyInstaller 官方使用说明](https://www.pyinstaller.org/en/stable/usage.html)。



## 验证与后续发布

计分规则测试不创建游戏窗口：

```powershell
& ..\minifps-local\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

后续每次发布需要更新版本号、更新日志、README、版本标签与 GitHub Release；详细步骤见 [CONTRIBUTING.md](CONTRIBUTING.md)。exe 和构建环境继续只保留在本地目录。
