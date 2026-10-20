"""玩家最高分、历史、成就与导入纪录合并。"""
import uuid
from copy import deepcopy
from .config import TARGET_COUNT
from datetime import datetime, timezone
from .scoring import SaveError, number

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
