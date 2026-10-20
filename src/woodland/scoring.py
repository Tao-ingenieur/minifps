"""对局状态、计分、暂停计时与对局数据校验。"""
import math
import uuid
from dataclasses import dataclass
from .config import ROUND_SECONDS, TARGET_COUNT, SHOT_COOLDOWN

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
