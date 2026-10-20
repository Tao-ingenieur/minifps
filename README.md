# MiniFPS Woodland v0.4.0

一个极简 Windows 第一人称林间猎鸟靶场，使用 Python + Ursina。可辨认的多部件 3D 猎枪包含木质枪托、金属枪管、瞄准镜和持枪手；鸟有头、喙、眼睛、双翼、脚与尾羽，栖息在林间木桩上。每局有 8 只静态鸟，朝向随机；场景与栖息位置固定，确保跨次启动读档时布局一致。

WASD 移动，鼠标瞄准，左键射击。启动后先显示规则菜单，点击 START 或按 Enter 开始一局 120 秒挑战。击中全部 8 只鸟或用时结束后显示 Game Over、逐项得分和总分，可按 R / Enter 或点击 PLAY AGAIN 重新开始。ESC 保存后释放鼠标并退出。

当前版本 **v0.4.0**。每个版本的具体改动见 [更新日志](CHANGELOG.md)，可下载历史源码或查看 [GitHub Releases](https://github.com/Tao-ingenieur/minifps/releases)。前两版已根据原始提交补记历史记录。

![游戏实机画面](docs/preview.png)
![暂停与存档菜单](docs/pause.png)
![清场结算](docs/results.png)

## 存盘、继续与玩家成绩

默认存档保存在 `%LOCALAPPDATA%\MiniFPS`，即 Windows 当前用户的本地应用数据目录，不依赖 exe 所在位置。新版本覆盖 exe 后，档案与最高分仍会保留。游戏是本地单人档案，无需注册或联网。

| 操作 | 按键 / 菜单 |
| --- | --- |
| 暂停 / 继续 | P；暂停菜单也可按 Enter 继续 |
| 快速存盘 | F5 / QUICK SAVE，保存后停在暂停页 |
| 快速读档 | F9 / QUICK LOAD；有当前进度时先确认 |
| 导出便携存档 | F6 / EXPORT JSON，选择保存位置 |
| 导入便携存档 | F7 / IMPORT JSON，选择之前导出的 JSON |
| 重开本局 | R / NEW ROUND；局中先确认，不清除最高分 |
| 看历史与成就 | 暂停或结算菜单的 HISTORY |
| 放大瞄准 | 按住鼠标右键，松开恢复；放大时降低鼠标灵敏度 |
| 保存并退出 | ESC / SAVE & EXIT；关闭窗口也触发保存 |

存档包含剩余目标、玩家位置与视角、当前分数所需的命中/发数与连击、已用时间和射击冷却。读档后停在暂停页，继续前不消耗时间。暂停、离线及文件选择器打开期间都不计时；切出窗口也会自动暂停。

游戏会在每次有效射击后、每 10 秒、暂停、结算和正常退出时保存到 `autosave.json`。下次启动可用 CONTINUE 恢复。F5 保存的是独立的 `quicksave.json` 检查点，之后的新局与自动保存不会覆盖它。F6 导出的是可复制到其他电脑的独立 JSON 文件，F7 导入后合并本机档案。

**当前分**是本局实时分数，可为负；**最高分**是已完成清场或超时局的最高结算分；**上一局分数**是最近完成局的结算分。新局清零当前分，最高分和历史成绩继续保留。导入旧备份不会降低本机最高分、最快清场或成就。最近 20 局记录包括得分、用时、命中率和清场/超时状态；同一局重复导入不会重复累计局数，重新挑战旧检查点取得更好结果可以提高最高分。

额外成就包括：首次清场、8 发全中、30 秒内清场、结算达到 1800 分。成就记录在本地档案中，结算页显示本次新解锁项目。

存档采用 JSON 校验与原子写入，并保留上一版 `.bak` 备份；自动/快速存档损坏时尝试恢复备份。原损坏文件在被替换前保留 `.corrupt-*` 副本。写入失败会显示提示，保存失败退出时需要再次确认；无效导入不会覆盖当前局。存档仅用于本地离线游戏，不作为线上竞技成绩认证。

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

实时分数允许为负，避免先乱开枪再命中逃避惩罚；最终结算最低 0 分。准确率在未开枪时显示 0%。射击间隔 0.30 秒，冷却期点击不算发数或空枪；结算后无法继续射击刷分。计时使用单调时钟，游戏加载时间不计入比赛，游玩时不会因为低帧率而变慢，暂停和离线时间不计入。

例如：40 秒内用 8 发全部命中，得分为 `800 命中 + 550 连击 + 166 用时 + 200 准确率 + 150 全中 = 1866 分`。

清场显示 **GAME OVER / ALL BIRDS HIT**，超时显示 **GAME OVER / TIME UP**。结算后释放鼠标、停止移动并冻结得分和用时。重新开始会重置当前局计分、8 只鸟、玩家位置和视角；树林与木桩复用，玩家档案中的最高分和历史不变。

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

在规则菜单点击 START 或按 Enter 后，鼠标锁定到窗口，W/S 前后移动，A/D 左右平移，鼠标转动视角，单击左键射击。准星下的第一个碰撞物决定命中；猎枪模型不参与碰撞。射中小鸟后小鸟消失，清场或超时后显示结算页，可按 R / Enter 或点击按钮开启新一局。P 暂停，ESC 保存并退出、释放鼠标。

## 完整单文件代码

复制下面代码到 `minifps.py`，安装 Ursina 后可独立运行，不依赖本仓库其他文件。

```python
"""MiniFPS Woodland：单文件林间猎鸟靶场，Python 3.12 + Ursina。"""
import math
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
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

VERSION = '0.4.0'
SAVE_FORMAT = 1
RULESET = 'woodland-scoring-1'
SLOTS = [(-6, 2, 3), (-3, 2.6, 8), (2, 2.2, 4), (6, 3, 11),
         (-7, 3.5, 16), (0, 3.2, 18), (7, 2.5, 22), (-3, 2.1, 24)]
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
    round_id: str = ''
    paused_cooldown: float = 0

    def start(self, now):
        self.state = 'playing'
        self.shots = self.hits = self.streak = self.best_streak = self.combo_points = 0
        self.started_at = now
        self.finished_elapsed = 0
        self.last_shot = -float('inf')
        self.round_id = str(uuid.uuid4())
        self.paused_cooldown = 0

    def elapsed(self, now):
        if self.state == 'ready':
            return 0
        if self.state != 'playing':
            return self.finished_elapsed
        return min(ROUND_SECONDS, max(0, now - self.started_at))

    def pause(self, now):
        self.tick(now)
        if self.state == 'playing':
            self.finished_elapsed = self.elapsed(now)
            self.paused_cooldown = min(SHOT_COOLDOWN, max(0, SHOT_COOLDOWN - (now - self.last_shot)))
            self.state = 'paused'

    def resume(self, now):
        if self.state == 'paused':
            self.started_at = now - self.finished_elapsed
            self.last_shot = now - SHOT_COOLDOWN + self.paused_cooldown
            self.state = 'playing'

    def snapshot(self, now):
        if self.state not in ('playing', 'paused'):
            return None
        cooldown = (self.paused_cooldown if self.state == 'paused' else
                    min(SHOT_COOLDOWN, max(0, SHOT_COOLDOWN - (now - self.last_shot))))
        return {'id': self.round_id, 'shots': self.shots, 'hits': self.hits,
                'streak': self.streak, 'best_streak': self.best_streak,
                'combo_points': self.combo_points, 'elapsed': self.elapsed(now),
                'cooldown': cooldown}

    @classmethod
    def restore(cls, data, now):
        data = validate_round(data)
        game = cls()
        game.state = 'paused'  # 读档先暂停，玩家确认继续后才开始计时。
        game.round_id = data['id']
        for key in ('shots', 'hits', 'streak', 'best_streak', 'combo_points'):
            setattr(game, key, data[key])
        game.finished_elapsed = data['elapsed']
        game.started_at = now - game.finished_elapsed
        game.paused_cooldown = data['cooldown']
        return game

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



class SaveError(ValueError):
    """向玩家显示可读错误，不执行来自存档的任何代码。"""


def number(value, label, low, high, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SaveError(f'Invalid {label}.')
    if not math.isfinite(value) or not low <= value <= high:
        raise SaveError(f'{label} is out of range.')
    if integer and not isinstance(value, int):
        raise SaveError(f'{label} must be an integer.')
    return value


def validate_round(data):
    if not isinstance(data, dict):
        raise SaveError('Missing round data.')
    try:
        identifier = str(uuid.UUID(data['id']))
        shots = number(data['shots'], 'shots', 0, 400, True)
        hits = number(data['hits'], 'hits', 0, 7, True)
        streak = number(data['streak'], 'streak', 0, hits, True)
        best = number(data['best_streak'], 'best streak', streak, hits, True)
        combo = number(data['combo_points'], 'combo', 0, 550, True)
        elapsed = number(data['elapsed'], 'elapsed', 0, ROUND_SECONDS)
        cooldown = number(data['cooldown'], 'cooldown', 0, SHOT_COOLDOWN)
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise SaveError('Invalid round data: ' + str(error)) from error
    combo_sum = lambda count: sum(min(i, 4) * 25 for i in range(count))
    if (hits > shots or elapsed >= ROUND_SECONDS or combo % 25 or
            not combo_sum(best) <= combo <= combo_sum(hits) or
            (hits > 0 and best == 0) or (shots == hits and streak != hits)):
        raise SaveError('Inconsistent score or timer in save.')
    return {'id': identifier, 'shots': shots, 'hits': hits, 'streak': streak,
            'best_streak': best, 'combo_points': combo, 'elapsed': elapsed,
            'cooldown': cooldown}


ACHIEVEMENTS = {'first_clear': 'First clear', 'perfect': 'Perfect 8/8',
                'quick': 'Clear in 30s', 'expert': 'Score 1800+'}


def new_profile():
    return {'best_score': 0, 'last_score': 0, 'games_played': 0,
            'fastest_clear': None, 'achievements': [], 'history': [], 'completed_ids': []}


def validate_profile(data):
    if not isinstance(data, dict):
        raise SaveError('Missing player profile.')
    try:
        profile = new_profile()
        for key in ('best_score', 'last_score'):
            profile[key] = number(data[key], key, 0, 2000, True)
        profile['games_played'] = number(data['games_played'], 'games played', 0, 10000000, True)
        fastest = data['fastest_clear']
        profile['fastest_clear'] = None if fastest is None else number(fastest, 'fastest clear', 0, 120)
        if not isinstance(data['achievements'], list) or len(data['achievements']) > 4:
            raise SaveError('Invalid achievements.')
        profile['achievements'] = sorted(set(data['achievements']))
        if not set(profile['achievements']).issubset(ACHIEVEMENTS):
            raise SaveError('Unknown achievement.')
        ids = data['completed_ids']
        if not isinstance(ids, list) or len(ids) > 500:
            raise SaveError('Invalid completed rounds.')
        profile['completed_ids'] = list(dict.fromkeys(str(uuid.UUID(v)) for v in ids))
        history = data['history']
        if not isinstance(history, list) or len(history) > 20:
            raise SaveError('Too many history entries.')
        for item in history:
            identifier = str(uuid.UUID(item['id']))
            if item['state'] not in ('cleared', 'timeout'):
                raise SaveError('Invalid result state.')
            score = number(item['score'], 'result score', 0, 2000, True)
            hits = number(item['hits'], 'result hits', 0, 8, True)
            shots = number(item['shots'], 'result shots', hits, 400, True)
            elapsed = number(item['elapsed'], 'result elapsed', 0, 120)
            at = item['at']
            if not isinstance(at, str) or len(at) > 40:
                raise SaveError('Invalid result date.')
            datetime.fromisoformat(at)
            if (item['state'] == 'cleared') != (hits == 8):
                raise SaveError('Inconsistent completed result.')
            profile['history'].append({'id': identifier, 'state': item['state'],
                'score': score, 'hits': hits, 'shots': shots, 'elapsed': elapsed, 'at': at})
        if profile['best_score'] < max([profile['last_score']] + [r['score'] for r in profile['history']]):
            raise SaveError('High score is lower than recorded scores.')
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise SaveError('Invalid player profile: ' + str(error)) from error
    return profile


def record_result(profile, game):
    if game.state not in ('cleared', 'timeout'):
        return []
    duplicate = game.round_id in profile['completed_ids']
    unlocked_before = set(profile['achievements'])
    profile['last_score'] = game.total
    profile['best_score'] = max(profile['best_score'], game.total)
    if not duplicate:
        profile['games_played'] += 1
        profile['completed_ids'] = (profile['completed_ids'] + [game.round_id])[-500:]
    record = {
        'id': game.round_id, 'state': game.state, 'score': game.total,
        'hits': game.hits, 'shots': game.shots, 'elapsed': game.finished_elapsed,
        'at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    existing = next((r for r in profile['history'] if r['id'] == game.round_id), None)
    if not existing or any(existing[k] != record[k] for k in ('state', 'score', 'hits', 'shots', 'elapsed')):
        profile['history'] = ([r for r in profile['history'] if r['id'] != game.round_id] + [record])[-20:]
    unlocked = set(profile['achievements'])
    if game.state == 'cleared':
        unlocked.add('first_clear')
        if game.shots == TARGET_COUNT:
            unlocked.add('perfect')
        if game.finished_elapsed <= 30:
            unlocked.add('quick')
        if game.total >= 1800:
            unlocked.add('expert')
        old = profile['fastest_clear']
        profile['fastest_clear'] = game.finished_elapsed if old is None else min(old, game.finished_elapsed)
    profile['achievements'] = sorted(unlocked)
    return sorted(unlocked - unlocked_before)


def merge_profiles(local, imported):
    """导入旧备份也不会降低本机最高分，重复导入不会叠加同一局成绩。"""
    result = deepcopy(imported)
    result['best_score'] = max(local['best_score'], imported['best_score'])
    result['achievements'] = sorted(set(local['achievements']) | set(imported['achievements']))
    times = [v for v in (local['fastest_clear'], imported['fastest_clear']) if v is not None]
    result['fastest_clear'] = min(times) if times else None
    records = {item['id']: item for item in local['history'] + imported['history']}
    result['history'] = sorted(records.values(), key=lambda r: r['at'])[-20:]
    ids = list(dict.fromkeys(local['completed_ids'] + imported['completed_ids']))
    result['completed_ids'] = ids[-500:]
    result['games_played'] = max(local['games_played'], imported['games_played'], len(ids))
    return result


def validate_save(data):
    if (not isinstance(data, dict) or type(data.get('format_version')) is not int or
            data.get('format_version') != SAVE_FORMAT or
            data.get('ruleset') != RULESET):
        raise SaveError('Unsupported save format or scoring rules.')
    profile = validate_profile(data.get('profile'))
    session = data.get('session')
    if session is not None:
        try:
            round_data = validate_round(session['round'])
            perches = session['perches']
            if not isinstance(perches, list) or len(perches) != 8:
                raise SaveError('Expected 8 target perches.')
            checked_perches = []
            for value, original in zip(perches, SLOTS):
                if not isinstance(value, list) or len(value) != 3:
                    raise SaveError('Invalid perch.')
                x = number(value[0], 'perch x', original[0] - .6, original[0] + .6)
                if value[1:] != list(original[1:]):
                    raise SaveError('Invalid perch height or depth.')
                checked_perches.append([x, original[1], original[2]])
            remaining = session['birds']
            if not isinstance(remaining, list) or len(remaining) != 8 - round_data['hits']:
                raise SaveError('Target count does not match hits.')
            checked_birds, used = [], set()
            for bird in remaining:
                slot = number(bird['slot'], 'bird slot', 0, 7, True)
                if slot in used:
                    raise SaveError('Duplicate target in save.')
                used.add(slot)
                heading = number(bird['heading'], 'bird heading', -180, 180)
                checked_birds.append({'slot': slot, 'heading': heading})
            position = session['position']
            view = session['view']
            if not isinstance(position, list) or len(position) != 3 or not isinstance(view, list) or len(view) != 2:
                raise SaveError('Invalid player position or view.')
            position = [number(v, 'player position', low, high) for v, low, high in
                        zip(position, (-15.5, 0, -15), (15.5, 6, 30))]
            view = [number(view[0], 'yaw', 0, 360), number(view[1], 'pitch', -90, 90)]
            session = {'round': round_data, 'perches': checked_perches,
                       'birds': checked_birds, 'position': position, 'view': view}
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise SaveError('Invalid saved session: ' + str(error)) from error
    return {'format_version': SAVE_FORMAT, 'game_version': VERSION, 'ruleset': RULESET,
            'profile': profile, 'session': session}


class SaveStore:
    """UTF-8 JSON、大小/类型校验、同目录临时文件原子替换、上一版备份。"""
    def __init__(self, directory):
        self.directory = Path(directory)
        self.autosave = self.directory / 'autosave.json'
        self.quick = self.directory / 'quicksave.json'

    @staticmethod
    def read(path):
        try:
            path = Path(path)
            if path.stat().st_size > 1024 * 1024:
                raise SaveError('Save file exceeds 1 MB.')
            return validate_save(json.loads(path.read_text(encoding='utf-8-sig')))
        except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
            raise SaveError('Cannot read save: ' + str(error)) from error

    @classmethod
    def load_with_backup(cls, path):
        path = Path(path)
        if not path.exists() and not path.with_suffix(path.suffix + '.bak').exists():
            return None, ''
        try:
            return cls.read(path), ''
        except SaveError as error:
            try:
                return cls.read(path.with_suffix(path.suffix + '.bak')), 'Recovered previous backup.'
            except SaveError:
                return None, str(error)

    @classmethod
    def write(cls, path, data):
        data = validate_save(data)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            if path.exists():
                try:
                    cls.read(path)
                    backup = path.with_suffix(path.suffix + '.bak')
                except SaveError:
                    backup = path.with_name(path.stem + '.corrupt-' + uuid.uuid4().hex[:8] + path.suffix)
                shutil.copy2(path, backup)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.tmp',
                                             prefix=path.name + '.', dir=path.parent, delete=False) as file:
                temporary = Path(file.name)
                json.dump(data, file, ensure_ascii=False, allow_nan=False, indent=2)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()


def choose_save_file(save=False):
    """Windows 原生文件对话框；无需额外 GUI 依赖，也不会更改工作目录。"""
    if os.name != 'nt':
        raise SaveError('File dialogs require Windows. F5/F9 still use the local save folder.')
    import ctypes
    from ctypes import wintypes
    class OpenFileName(ctypes.Structure):
        _fields_ = [('lStructSize', wintypes.DWORD), ('hwndOwner', wintypes.HWND),
            ('hInstance', wintypes.HINSTANCE), ('lpstrFilter', wintypes.LPCWSTR),
            ('lpstrCustomFilter', wintypes.LPWSTR), ('nMaxCustFilter', wintypes.DWORD),
            ('nFilterIndex', wintypes.DWORD), ('lpstrFile', wintypes.LPWSTR),
            ('nMaxFile', wintypes.DWORD), ('lpstrFileTitle', wintypes.LPWSTR),
            ('nMaxFileTitle', wintypes.DWORD), ('lpstrInitialDir', wintypes.LPCWSTR),
            ('lpstrTitle', wintypes.LPCWSTR), ('Flags', wintypes.DWORD),
            ('nFileOffset', wintypes.WORD), ('nFileExtension', wintypes.WORD),
            ('lpstrDefExt', wintypes.LPCWSTR), ('lCustData', ctypes.c_ssize_t),
            ('lpfnHook', ctypes.c_void_p), ('lpTemplateName', wintypes.LPCWSTR),
            ('pvReserved', ctypes.c_void_p), ('dwReserved', wintypes.DWORD),
            ('FlagsEx', wintypes.DWORD)]
    buffer = ctypes.create_unicode_buffer(32768)
    if save:
        buffer.value = 'MiniFPS-save.json'
    info = OpenFileName()
    info.lStructSize = ctypes.sizeof(info)
    ctypes.windll.user32.GetForegroundWindow.restype = wintypes.HWND
    info.hwndOwner = ctypes.windll.user32.GetForegroundWindow()
    info.lpstrFilter = 'MiniFPS JSON saves\0*.json\0\0'
    info.lpstrFile = ctypes.cast(buffer, wintypes.LPWSTR)
    info.nMaxFile = len(buffer)
    info.lpstrTitle = 'Export MiniFPS save' if save else 'Import MiniFPS save'
    info.lpstrDefExt = 'json'
    info.Flags = 0x00080000 | 0x00000800 | 0x00000008 | (0x00000002 if save else 0x00001000)
    function = ctypes.windll.comdlg32.GetSaveFileNameW if save else ctypes.windll.comdlg32.GetOpenFileNameW
    function.argtypes = [ctypes.POINTER(OpenFileName)]
    function.restype = wintypes.BOOL
    if function(ctypes.byref(info)):
        return Path(buffer.value)
    if ctypes.windll.comdlg32.CommDlgExtendedError():
        raise SaveError('Windows could not open the file dialog.')
    return None


def main():
    smoke_test = '--smoke-test' in sys.argv
    app = Ursina(title=f'MiniFPS | Woodland v{VERSION}', borderless=False, fullscreen=False,
                 size=(1280, 720), development_mode=False)
    window.color = color.rgb32(162, 189, 196)
    window.exit_button.visible = False
    window.fps_counter.enabled = False
    # 场景固定，保证重新启动或导入存档时树木碰撞位置一致。
    rng = random.Random(17)
    round_rng = random.Random(17 if smoke_test else None)
    if '--data-dir' in sys.argv:
        data_dir = Path(sys.argv[sys.argv.index('--data-dir') + 1])
        if smoke_test:
            data_dir = data_dir / ('smoke-' + uuid.uuid4().hex)
    elif smoke_test:
        data_dir = Path(tempfile.gettempdir()) / ('minifps-smoke-' + uuid.uuid4().hex)
    else:
        data_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local/share')) / 'MiniFPS'
    store = SaveStore(data_dir)
    loaded, initial_notice = store.load_with_backup(store.autosave)
    profile = loaded['profile'] if loaded else new_profile()
    saved_session = loaded['session'] if loaded else None
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
    def make_bird(position, heading=0, slot=None):
        bird = Entity(position=position, rotation_y=heading)
        bird.slot = len(birds) if slot is None else slot
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

    perches, perch_models = [], []
    for index, (x, y, z) in enumerate(SLOTS):
        x += rng.uniform(-.5, .5)
        perches.append((x, y, z))
        make_bird((x, y, z), rng.uniform(-35, 35), index)
        perch = Entity(position=(x, 0, z))
        perch_models.append(perch)
        part(perch, model='cylinder', position=(0, (y - .43) / 2, 0),
             scale=(.18, y - .43, .18), shade=tint(99, 77, 51), solid=True)
        part(perch, position=(0, y - .46, 0), scale=(1.3, .11, .16), shade=tint(99, 77, 51))

    hud = Entity(parent=camera.ui)
    Entity(parent=hud, model='quad', position=(-.51, .35), scale=(.72, .26),
           color=color.rgba32(20, 30, 25, 195))
    Text(f'WOODLAND / v{VERSION}', parent=hud, position=(-.85, .46), scale=.85,
         color=tint(220, 210, 171))
    counter = Text(parent=hud, position=(-.85, .42), scale=1)
    status = Text(parent=hud, position=(-.85, .38), scale=.85)
    feedback = Text(parent=hud, position=(-.85, .33), scale=.85, color=tint(220, 210, 171))
    personal = Text(parent=hud, position=(-.85, .28), scale=.75, color=tint(220, 210, 171))
    reticle = Entity(parent=hud)
    for pos, size in [((-.009, 0), (.009, .0015)), ((.009, 0), (.009, .0015)),
                      ((0, -.009), (.0015, .009)), ((0, .009), (.0015, .009))]:
        Entity(parent=reticle, model='quad', position=pos, scale=size,
               color=color.rgba32(245, 242, 219, 215))
    Text('WASD MOVE  /  LMB FIRE  /  RMB ZOOM  /  P PAUSE  /  F5 SAVE  /  F9 LOAD',
         parent=hud, position=(-.85, -.46), scale=.72, color=tint(242, 239, 220))
    toast = Text(parent=camera.ui, origin=(0, 0), position=(.3, .45), z=-.4,
                 scale=.8, color=tint(242, 225, 170), enabled=False)

    menu = Entity(parent=camera.ui)
    Entity(parent=menu, model='quad', scale=(4, 2), z=.2,
           color=color.rgba32(8, 15, 13, 175))
    Entity(parent=menu, model='quad', scale=(1.36, .96), z=.1, color=tint(27, 40, 34))
    menu_title = Text(parent=menu, origin=(0, 0), position=(0, .395), z=-.1,
                      scale=1.8, color=tint(233, 219, 169))
    menu_subtitle = Text(parent=menu, origin=(0, 0), position=(0, .325), z=-.1, scale=.95)
    details = Text(parent=menu, position=(-.58, .25), z=-.1, scale=.85, line_height=1.25)
    menu_notice = Text(parent=menu, position=(-.61, -.435), z=-.2, scale=.67,
                       color=tint(234, 207, 144))
    def button(text, x, y, shade=None):
        return Button(parent=menu, text=text, position=(x, y), z=-.1,
                      scale=(.35, .055), color=shade or tint(66, 83, 69))
    primary = button('START / ENTER', -.40, -.20, tint(88, 114, 78))
    restart_button = button('NEW ROUND / R', 0, -.20)
    history_button = button('HISTORY', .40, -.20)
    save_button = button('QUICK SAVE / F5', -.40, -.275)
    load_button = button('QUICK LOAD / F9', 0, -.275)
    export_button = button('EXPORT JSON / F6', .40, -.275)
    import_button = button('IMPORT JSON / F7', -.40, -.35)
    exit_button = button('SAVE & EXIT / ESC', 0, -.35)
    back_button = button('BACK / P', .40, -.35)
    buttons = [primary, restart_button, history_button, save_button, load_button,
               export_button, import_button, exit_button, back_button]
    game = GameRound()
    recoil = sway_time = 0
    notice = initial_notice
    notice_until = 0
    next_autosave = 0
    menu_mode = 'normal'
    pending_action = None
    unlocked = []

    def notify(text):
        nonlocal notice, notice_until
        notice = text.replace('\n', ' ')[:115]
        menu_notice.text = notice
        toast.text = notice
        notice_until = perf_counter() + 5

    def refresh_hud(now):
        remaining = max(0, ROUND_SECONDS - game.elapsed(now))
        counter.text = f'SCORE {game.score:04d}     BIRDS {game.hits:02d} / 08'
        status.text = (f'TIME {remaining:05.1f}s    ACC {game.accuracy:.0%}'
                       f'    STREAK {game.streak}    SHOTS {game.shots}')
        personal.text = f'BEST {profile["best_score"]}    LAST {profile["last_score"]}    P: PAUSE'

    def payload(now=None):
        now = perf_counter() if now is None else now
        game.tick(now)
        record_result(profile, game)
        session = None
        if game.state in ('playing', 'paused'):
            session = {'round': game.snapshot(now), 'perches': [list(v) for v in perches],
                       'birds': [{'slot': b.slot, 'heading': b.rotation_y} for b in birds],
                       'position': [player.x, max(0, player.y), player.z],
                       'view': [player.rotation_y % 360, player.camera_pivot.rotation_x]}
        elif game.state == 'ready':
            session = saved_session  # 启动菜单退出时保留尚未恢复的旧进度。
        return {'format_version': SAVE_FORMAT, 'game_version': VERSION, 'ruleset': RULESET,
                'profile': deepcopy(profile), 'session': session}

    def checkpoint(path=None, announce=False, now=None):
        nonlocal next_autosave
        try:
            store.write(path or store.autosave, payload(now))
            next_autosave = perf_counter() + 10
            if announce:
                notify('Saved. Progress, score and profile are safe.')
            return True
        except (OSError, SaveError) as error:
            next_autosave = perf_counter() + 10
            notify('SAVE FAILED: ' + str(error))
            return False
        finally:
            # 自动保存可能恰好跨过截止时间，此时也必须进入结算而非停留在 HUD。
            if game.state == 'timeout' and not menu.enabled:
                show_menu()

    def show_menu(mode='normal'):
        nonlocal menu_mode
        menu_mode = mode
        menu.enabled = True
        hud.enabled = False
        player.ignore = True
        reticle.enabled = gun.enabled = False
        camera.fov = 76
        player.mouse_sensitivity = Vec3(35, 35, 0)
        mouse.locked = False
        mouse.visible = True
        toast.enabled = False
        for item in buttons:
            item.enabled = True
        back_button.enabled = mode != 'normal'
        primary.text = 'RESUME / ENTER' if game.state == 'paused' else 'PLAY AGAIN / ENTER'
        primary.on_click = primary_action
        back_button.on_click = lambda: show_menu()
        menu_notice.text = notice
        if mode == 'history':
            primary.text = 'BACK TO MENU'
            menu_title.text = 'PLAYER RECORDS'
            menu_subtitle.text = f'BEST {profile["best_score"]}  /  LAST {profile["last_score"]}  /  ROUNDS {profile["games_played"]}'
            rows = ['RECENT RESULTS (newest first)']
            for item in reversed(profile['history'][-5:]):
                label = 'CLEAR' if item['state'] == 'cleared' else 'TIME UP'
                accuracy = item['hits'] / item['shots'] if item['shots'] else 0
                rows.append(f'{item["at"][:10]}  {label}  {item["score"]} pts  '
                            f'{item["elapsed"]:.1f}s  {accuracy:.0%}')
            if not profile['history']:
                rows.append('No completed rounds yet. Finish a round to set a record.')
            fastest = profile['fastest_clear']
            rows.append('\nFASTEST CLEAR: ' + (f'{fastest:.1f}s' if fastest is not None else '--'))
            rows.append('BADGES: ' + ', '.join(ACHIEVEMENTS[a] for a in profile['achievements']))
            details.text = '\n'.join(rows)
        elif game.state == 'ready':
            menu_title.text = 'WOODLAND'
            current = GameRound.restore(saved_session['round'], perf_counter()).score if saved_session else 0
            menu_subtitle.text = f'BEST {profile["best_score"]}  /  LAST {profile["last_score"]}  /  SAVED SCORE {current}'
            primary.text = 'CONTINUE / ENTER' if saved_session else 'START / ENTER'
            details.text = ('8 birds / 120 seconds. Hit +100, miss -30.\n'
                            'Build a streak: +25 / +50 / +75 / +100 extra.\n'
                            'Clear bonuses: speed +300 max, accuracy +200 max.\n'
                            '8 shots / 8 hits: +150 perfect bonus.\n\n'
                            'P pauses; F5 saves; F9 loads. RMB zooms to aim.\n'
                            'Progress autosaves after shots and every 10 seconds.\n'
                            'Export / Import JSON transfers progress to another PC.')
        elif game.state == 'paused':
            menu_title.text = 'PAUSED'
            menu_subtitle.text = f'CURRENT {game.score}  /  BEST {profile["best_score"]}  /  LAST {profile["last_score"]}'
            details.text = (f'Birds {game.hits}/8    Shots {game.shots}    Accuracy {game.accuracy:.1%}\n'
                            f'Time left {ROUND_SECONDS - game.finished_elapsed:.1f}s    Streak {game.streak}\n\n'
                            'Timer is stopped. Resume with P or ENTER.\n'
                            'F5: quick save     F9: quick load\n'
                            'F6: export a JSON file     F7: import a JSON file\n'
                            'NEW ROUND asks before discarding this attempt.\n'
                            'Best score and completed records survive restarts.')
        else:
            speed, accuracy, perfect = game.bonuses
            menu_title.text = 'GAME OVER'
            outcome = 'ALL BIRDS HIT' if game.state == 'cleared' else 'TIME UP'
            menu_subtitle.text = f'{outcome} / {game.total} PTS / BEST {profile["best_score"]}'
            details.text = (f'Time {game.finished_elapsed:.1f}s   Birds {game.hits}/8   Accuracy {game.accuracy:.1%}\n'
                            f'Hit points +{game.hits * 100}    Combo +{game.combo_points}\n'
                            f'Miss penalty -{(game.shots - game.hits) * 30}\n'
                            f'Clear speed +{speed}    Clear accuracy +{accuracy}\n'
                            f'Perfect round +{perfect}    Best streak {game.best_streak}\n\n'
                            'UNLOCKED: ' + (', '.join(ACHIEVEMENTS[a] for a in unlocked) or '--') + '\n'
                            'Result saved. View HISTORY or play another round.')

    def finish_round():
        nonlocal unlocked
        unlocked = record_result(profile, game)
        checkpoint()
        show_menu()

    def set_active():
        nonlocal next_autosave, menu_mode, pending_action
        menu_mode = 'normal'
        pending_action = None
        menu.enabled = False
        hud.enabled = True
        player.ignore = False
        reticle.enabled = gun.enabled = True
        mouse.locked = not smoke_test
        mouse.visible = smoke_test
        next_autosave = perf_counter() + 10
        refresh_hud(perf_counter())

    def start_round():
        nonlocal recoil, sway_time, saved_session, unlocked
        for bird in list(birds):
            destroy(bird)
        birds.clear()
        for index, position in enumerate(perches):
            make_bird(position, round_rng.uniform(-35, 35), index)
        player.position = (0, 0, -10)
        player.rotation = player.camera_pivot.rotation = (0, 0, 0)
        player.air_time = 0
        for key in ('w', 'a', 's', 'd'):
            held_keys[key] = 0
        recoil = sway_time = 0
        saved_session = None
        unlocked = []
        game.start(perf_counter())
        feedback.text = 'HIT +100 / MISS -30 / BUILD A STREAK'
        feedback.color = tint(220, 210, 171)
        set_active()
        checkpoint()

    def pause_round():
        if game.state == 'playing':
            game.pause(perf_counter())
            if game.state == 'timeout':
                finish_round()
                return
            checkpoint()
        show_menu()

    def resume_round():
        if game.state == 'paused':
            game.resume(perf_counter())
            for key in ('w', 'a', 's', 'd'):
                held_keys[key] = 0
            set_active()

    def restore_session(session):
        nonlocal game, saved_session, recoil
        session = validate_save({'format_version': SAVE_FORMAT, 'ruleset': RULESET,
                                 'profile': profile, 'session': session})['session']
        for bird in list(birds):
            destroy(bird)
        birds.clear()
        perches[:] = [tuple(v) for v in session['perches']]
        for model, (x, y, z) in zip(perch_models, perches):
            model.position = (x, 0, z)
        for item in session['birds']:
            make_bird(perches[item['slot']], item['heading'], item['slot'])
        game = GameRound.restore(session['round'], perf_counter())
        player.position = session['position']
        player.rotation = (0, session['view'][0], 0)
        player.camera_pivot.rotation = (session['view'][1], 0, 0)
        player.air_time = 0
        recoil = 0
        saved_session = None
        refresh_hud(perf_counter())
        checkpoint()
        show_menu()

    def primary_action():
        if menu_mode != 'normal':
            show_menu()
            return
        if game.state == 'paused':
            resume_round()
        elif game.state == 'ready' and saved_session:
            restore_session(saved_session)
            notify('Save restored. Press P or ENTER to resume.')
        elif game.state != 'playing':
            start_round()

    def confirm(title, text, action):
        nonlocal pending_action, menu_mode
        pause_round()
        pending_action = action
        menu_mode = 'confirm'
        menu_title.text = title
        menu_subtitle.text = 'YOUR BEST SCORE AND RECORDS WILL BE KEPT'
        details.text = text + '\n\nPress ENTER to confirm, P to cancel.'
        for item in buttons:
            item.enabled = item in (primary, back_button)
        primary.text = 'CONFIRM / ENTER'
        primary.on_click = accept_confirmation
        back_button.text = 'CANCEL / P'
        back_button.on_click = cancel_confirmation

    def accept_confirmation():
        nonlocal pending_action, menu_mode
        action, pending_action = pending_action, None
        menu_mode = 'normal'
        if action:
            action()
        back_button.text = 'BACK / P'

    def cancel_confirmation():
        nonlocal pending_action
        pending_action = None
        back_button.text = 'BACK / P'
        show_menu()

    def request_restart():
        if game.state in ('playing', 'paused') or (game.state == 'ready' and saved_session):
            confirm('NEW ROUND?', 'Discard this attempt and start with 8 birds and 0 points?\n'
                    'This replaces the automatic checkpoint. Your F5 save stays intact.', start_round)
        else:
            start_round()

    def save_quick():
        pause_round()
        checkpoint(store.quick, announce=True)

    def apply_import(data):
        nonlocal profile, game, saved_session
        profile = merge_profiles(profile, data['profile'])
        if data['session']:
            restore_session(data['session'])
        else:
            game = GameRound()
            saved_session = None
            checkpoint()
            show_menu()
        notify('Imported. Best score and records merged; no duplicate results.')

    def load_file(path):
        pause_round()
        try:
            if Path(path) == store.quick:
                data, recovery = store.load_with_backup(path)
                if data is None:
                    raise SaveError(recovery or 'No quick save yet. Use F5 first.')
                if recovery:
                    notify(recovery)
            else:
                data = store.read(path)
        except SaveError as error:
            notify('LOAD FAILED: ' + str(error))
            return
        if game.state == 'paused' or saved_session:
            confirm('LOAD SAVE?', 'Replace the current attempt with the selected save?\n'
                    'Local high scores and achievements will be merged, not lowered.',
                    lambda: apply_import(data))
        else:
            apply_import(data)

    def import_file():
        pause_round()
        try:
            path = choose_save_file()
            if path:
                load_file(path)
        except (OSError, SaveError) as error:
            notify('IMPORT FAILED: ' + str(error))

    def export_file():
        pause_round()
        try:
            path = choose_save_file(save=True)
            if path:
                checkpoint(path, announce=True)
        except (OSError, SaveError) as error:
            notify('EXPORT FAILED: ' + str(error))

    def exit_game(force=False):
        pause_round()
        if not checkpoint() and not force:
            confirm('SAVE FAILED', 'Exit anyway? Progress since the last successful save may be lost.',
                    lambda: exit_game(force=True))
            return
        mouse.locked = False
        mouse.visible = True
        application.quit()

    restart_button.on_click = request_restart
    history_button.on_click = lambda: (pause_round(), show_menu('history'))
    save_button.on_click = save_quick
    load_button.on_click = lambda: load_file(store.quick)
    export_button.on_click = export_file
    import_button.on_click = import_file
    exit_button.on_click = exit_game

    def shoot(now=None):
        nonlocal recoil
        now = perf_counter() if now is None else now
        if not game.can_fire(now):
            if game.state == 'timeout':
                finish_round()
            return
        hit = raycast(camera.world_position, camera.forward, distance=65,
                      ignore=[player], traverse_target=scene)
        target = hit.entity if hit.hit and hit.entity in birds else None
        delta = game.fire(target is not None, now)
        recoil = .07
        if target is not None:
            birds.remove(target)
            destroy(target)
            feedback.text = f'HIT +{delta} / STREAK {game.streak}'
            feedback.color = tint(189, 224, 146)
        else:
            feedback.text = 'MISS -30 / STREAK RESET'
            feedback.color = tint(241, 159, 131)
        refresh_hud(now)
        if game.state == 'cleared':
            finish_round()
        else:
            checkpoint(now=now)

    def handle_input(key):
        if menu_mode == 'confirm':
            if key == 'enter':
                accept_confirmation()
            elif key in ('p', 'escape'):
                cancel_confirmation()
            return
        if key == 'escape':
            exit_game()
        elif key == 'p':
            if menu_mode == 'history':
                show_menu()
            elif game.state == 'playing':
                pause_round()
            elif game.state == 'paused':
                resume_round()
        elif key == 'r':
            request_restart()
        elif key == 'enter' and game.state != 'playing':
            primary_action()
        elif key == 'f5':
            save_quick()
        elif key == 'f9':
            load_file(store.quick)
        elif key == 'f6':
            export_file()
        elif key == 'f7':
            import_file()
        elif key == 'left mouse down' and mouse.locked:
            shoot()
        elif key == 'right mouse down' and game.state == 'playing':
            camera.fov = 50
            player.mouse_sensitivity = Vec3(20, 20, 0)
        elif key == 'right mouse up':
            camera.fov = 76
            player.mouse_sensitivity = Vec3(35, 35, 0)

    def update_view():
        nonlocal recoil, sway_time
        toast.enabled = game.state == 'playing' and perf_counter() < notice_until
        if game.state != 'playing':
            return
        now = perf_counter()
        game.tick(now)
        refresh_hud(now)
        if game.state == 'timeout':
            finish_round()
            return
        if not smoke_test and not app.win.getProperties().getForeground():
            pause_round()
            notify('Window inactive. Game paused; timer stopped.')
            return
        if now >= next_autosave:
            checkpoint()
        sway_time += min(time.dt, .05)
        recoil = max(0, recoil - time.dt * .4)
        gun.z = .82 - recoil
        gun.rotation_x = -recoil * 65
        gun.y = -.25 + math.sin(sway_time * 1.8) * .002

    controls = Entity()
    controls.input = handle_input
    controls.update = update_view
    # 点击窗口关闭按钮同样存盘；防止直接关窗丢失最后进度。
    app.exitFunc = lambda: checkpoint()
    refresh_hud(perf_counter())
    show_menu()

    if smoke_test:
        def screenshot(path):
            from panda3d.core import Filename
            app.graphicsEngine.renderFrame()
            app.graphicsEngine.renderFrame()
            app.screenshot(namePrefix=Filename.from_os_specific(str(Path(path).resolve())),
                           defaultFilename=False)

        def verify():
            nonlocal profile, game, saved_session
            try:
                # 自检目录独立，绝不读取或改写玩家的真实存档。
                assert game.state == 'ready' and menu.enabled and player.ignore
                if '--menu-screenshot' in sys.argv:
                    screenshot(sys.argv[sys.argv.index('--menu-screenshot') + 1])
                mouse.hovered_entity = primary
                app.input('left mouse down')
                app.input('left mouse up')
                mouse.hovered_entity = None
                assert game.state == 'playing' and len(birds) == 8
                assert game.shots == 0
                bird = birds[0]
                bird.world_position = camera.world_position + camera.forward * 3
                shoot(game.started_at)
                assert game.hits == 1 and len(birds) == 7
                player.position = (1, 0, -8)
                player.rotation_y = 12
                player.camera_pivot.rotation_x = 5
                save_quick()
                snapshot = store.read(store.quick)
                assert snapshot['session']['round']['hits'] == 1
                assert len(snapshot['session']['birds']) == 7
                saved_score = game.score
                request_restart()
                assert menu_mode == 'confirm' and game.state == 'paused'
                cancel_confirmation()
                assert game.score == saved_score
                request_restart()
                accept_confirmation()
                assert game.score == 0 and len(birds) == 8
                assert menu_mode == 'normal'
                handle_input('p')
                assert game.state == 'paused'
                handle_input('p')
                assert game.state == 'playing'
                load_file(store.quick)
                assert menu_mode == 'confirm'
                accept_confirmation()
                assert game.state == 'paused' and game.score == saved_score
                assert len(birds) == 7 and abs(player.x - 1) < .01 and player.rotation_y == 12
                export_path = store.directory / 'export-test.json'
                checkpoint(export_path)
                assert store.read(export_path)['session']['round'] == game.snapshot(perf_counter())
                if '--pause-screenshot' in sys.argv:
                    screenshot(sys.argv[sys.argv.index('--pause-screenshot') + 1])
                resume_round()
                if '--screenshot' in sys.argv:
                    screenshot(sys.argv[sys.argv.index('--screenshot') + 1])
                now = game.started_at + game.elapsed(perf_counter()) + 1
                for index, bird in enumerate(list(birds)):
                    bird.world_position = camera.world_position + camera.forward * 3
                    shoot(now + index)
                    assert bird not in birds
                assert game.state == 'cleared' and game.hits == 8 and not birds
                assert profile['best_score'] == game.total and profile['games_played'] == 1
                assert menu.enabled and player.ignore and not mouse.locked
                checkpoint()
                assert profile['games_played'] == 1
                if '--result-screenshot' in sys.argv:
                    screenshot(sys.argv[sys.argv.index('--result-screenshot') + 1])
                apply_import(snapshot)
                assert profile['best_score'] > 0 and game.score == saved_score
                assert len(profile['history']) == 1
                start_round()
                assert game.score == 0 and profile['best_score'] > 0 and len(birds) == 8
                app.exitFunc()
                assert store.read(store.autosave)['session'] is not None
                checkpoint(now=game.started_at + ROUND_SECONDS)
                assert game.state == 'timeout' and menu.enabled and player.ignore
                finish_round()
                assert game.state == 'timeout' and profile['games_played'] == 2
                # 从磁盘重新读取，模拟关闭程序后再次启动。
                persisted, error = store.load_with_backup(store.autosave)
                assert persisted['profile']['best_score'] == profile['best_score'] and not error
                assert persisted['profile']['last_score'] == 0 and persisted['session'] is None
                print('SMOKE TEST PASSED: save, load, import, best score, restart, results', flush=True)
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

可选自动自检（真实窗口短暂出现，在隔离测试目录检查存盘、重开确认、真实目标命中、位置/视角读档、导入合并、最高分与结算，然后退出，不接触真实玩家存档）：

```powershell
& ..\minifps-local\.venv\Scripts\python.exe src\minifps.py --smoke-test
# 控制台版 exe 也支持：
& ..\minifps-local\dist\MiniFPS.exe --smoke-test
```

## GitHub

Git 仓库根目录为 `minifps`，同级 `minifps-local` 不在版本控制范围内。`.gitignore` 也排除 exe、缓存、虚拟环境和构建产物。公开仓库只包含源码、依赖清单及说明。

参考：[Ursina API](https://www.ursinaengine.org/api_reference.html)、[PyInstaller 官方使用说明](https://www.pyinstaller.org/en/stable/usage.html)。



## 验证与后续发布

29 项计分、暂停、档案合并及存档可靠性测试不创建游戏窗口：

```powershell
& ..\minifps-local\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

后续每次发布需要更新版本号、更新日志、README、版本标签与 GitHub Release；详细步骤见 [CONTRIBUTING.md](CONTRIBUTING.md)。exe 和构建环境继续只保留在本地目录。
