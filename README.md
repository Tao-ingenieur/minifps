# MiniFPS

一个极简 Windows 第一人称靶场，使用 Python + Ursina。纯色室内房间、四面墙、天花板、基础天空与光照，每次启动随机生成 8 个静态方块。WASD 移动，鼠标瞄准，左键发射即时命中子弹；击中靶子后靶子消失，墙壁会阻挡射击。ESC 释放鼠标并退出。没有音效、AI 或复杂特效。

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

游戏开始时鼠标锁定到窗口，W/S 前后移动，A/D 左右平移，鼠标转动视角，单击左键射击。准星下的第一个碰撞物决定命中；打完所有靶子后显示完成提示，重新启动生成新靶子。ESC 直接退出并释放鼠标。

## 完整单文件代码

复制下面代码到 `minifps.py`，安装 Ursina 后可独立运行，不依赖本仓库其他文件。

```python
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

可选自动自检（真实窗口短暂出现，检查墙壁射线与靶子命中，然后退出）：

```powershell
& ..\minifps-local\.venv\Scripts\python.exe src\minifps.py --smoke-test
# 控制台版 exe 也支持：
& ..\minifps-local\dist\MiniFPS.exe --smoke-test
```

## GitHub

Git 仓库根目录为 `minifps`，同级 `minifps-local` 不在版本控制范围内。`.gitignore` 也排除 exe、缓存、虚拟环境和构建产物。公开仓库只包含源码、依赖清单及说明。

参考：[Ursina API](https://www.ursinaengine.org/api_reference.html)、[PyInstaller 官方使用说明](https://www.pyinstaller.org/en/stable/usage.html)。


