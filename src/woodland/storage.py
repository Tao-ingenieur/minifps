"""JSON 存档校验、原子写入、备份恢复；不依赖图形引擎。"""
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from .config import VERSION, SAVE_FORMAT, RULESET, SLOTS, TARGET_COUNT
from .scoring import SaveError, number, validate_round
from .profiles import validate_profile

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
