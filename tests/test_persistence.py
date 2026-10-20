"""存档、暂停、备份、导入合并与玩家成绩的回归测试。"""
import json
import sys
import unittest
import uuid
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from minifps import (GameRound, SaveError, SaveStore, SLOTS, SAVE_FORMAT, RULESET,
                    VERSION, new_profile, record_result, merge_profiles, validate_save)


def fixture():
    game = GameRound()
    game.start(1000)
    game.fire(True, 1001)
    game.pause(1002)
    return {'format_version': SAVE_FORMAT, 'game_version': VERSION, 'ruleset': RULESET,
        'profile': new_profile(), 'session': {'round': game.snapshot(1002),
        'perches': [list(v) for v in SLOTS],
        'birds': [{'slot': i, 'heading': 0} for i in range(1, 8)],
        'position': [1, 0, -8], 'view': [12, 5]}}


def completed(elapsed=35):
    game = GameRound()
    game.start(1000)
    for i in range(7):
        game.fire(True, 1000 + i)
    game.fire(True, 1000 + elapsed)
    return game


class PauseTests(unittest.TestCase):
    def test_pause_excludes_offline_time_and_preserves_cooldown(self):
        game = GameRound()
        game.start(1000)
        game.fire(True, 1002)
        game.pause(1002.1)
        self.assertEqual(game.state, 'paused')
        self.assertAlmostEqual(game.elapsed(99999), 2.1)
        self.assertIsNone(game.fire(True, 99999))
        game.resume(2000)
        self.assertAlmostEqual(game.elapsed(2001), 3.1)
        self.assertIsNone(game.fire(False, 2000.1))
        self.assertEqual(game.fire(True, 2000.2), 125)

    def test_pause_at_deadline_remains_timeout(self):
        game = GameRound()
        game.start(0)
        game.pause(120)
        game.resume(1000)
        self.assertEqual(game.state, 'timeout')
        self.assertEqual(game.elapsed(1000), 120)

    def test_restore_preserves_score_combo_timer_and_identity(self):
        data = fixture()['session']['round']
        game = GameRound.restore(data, 90000)
        self.assertEqual(game.state, 'paused')
        self.assertEqual((game.score, game.hits, game.streak, game.shots), (100, 1, 1, 1))
        self.assertEqual(game.round_id, data['id'])
        self.assertEqual(game.elapsed(99999), 2)
        game.resume(100000)
        self.assertEqual(game.elapsed(100001), 3)


class ValidationTests(unittest.TestCase):
    def test_complete_snapshot_roundtrip(self):
        data = fixture()
        clean = validate_save(json.loads(json.dumps(data)))
        self.assertEqual(clean['session'], data['session'])
        self.assertEqual(clean['profile'], data['profile'])

    def test_unknown_format_or_rules_rejected(self):
        for field, value in [('format_version', 99), ('format_version', True), ('ruleset', 'future')]:
            data = fixture()
            data[field] = value
            with self.assertRaises(SaveError):
                validate_save(data)

    def test_invalid_numbers_and_inconsistent_counters_rejected(self):
        cases = [('shots', -1), ('shots', True), ('hits', 9), ('streak', 2),
                 ('combo_points', 999), ('elapsed', 120), ('elapsed', float('nan')),
                 ('cooldown', .31), ('id', 'not-a-round-id')]
        for key, value in cases:
            data = fixture()
            data['session']['round'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                validate_save(data)

    def test_duplicate_or_missing_birds_rejected(self):
        data = fixture()
        data['session']['birds'][1]['slot'] = 1
        with self.assertRaises(SaveError):
            validate_save(data)
        data = fixture()
        data['session']['birds'].pop()
        with self.assertRaises(SaveError):
            validate_save(data)

    def test_invalid_player_and_world_positions_rejected(self):
        for field, value in [('position', [5000, 0, 0]), ('view', [0, float('inf')])]:
            data = fixture()
            data['session'][field] = value
            with self.assertRaises(SaveError):
                validate_save(data)
        data = fixture()
        data['session']['perches'][0][0] = 100
        with self.assertRaises(SaveError):
            validate_save(data)

    def test_invalid_profile_does_not_pass_import(self):
        for field, value in [('best_score', 900000), ('games_played', -1),
                             ('achievements', ['unknown']), ('history', [{}])]:
            data = fixture()
            data['profile'][field] = value
            with self.subTest(field=field), self.assertRaises(SaveError):
                validate_save(data)


class ProfileTests(unittest.TestCase):
    def test_result_records_high_last_history_and_badges_once(self):
        profile = new_profile()
        game = completed(20)
        unlocked = record_result(profile, game)
        self.assertEqual(profile['best_score'], game.total)
        self.assertEqual(profile['last_score'], game.total)
        self.assertEqual(profile['games_played'], 1)
        self.assertEqual(len(profile['history']), 1)
        self.assertEqual(set(unlocked), {'first_clear', 'perfect', 'quick', 'expert'})
        self.assertEqual(record_result(profile, game), [])
        self.assertEqual(profile['games_played'], 1)

    def test_replaying_same_saved_round_can_improve_best_without_duplicate_count(self):
        profile = new_profile()
        game = completed(70)
        record_result(profile, game)
        previous = profile['best_score']
        game.finished_elapsed = 20
        record_result(profile, game)
        self.assertGreater(profile['best_score'], previous)
        self.assertEqual(profile['games_played'], 1)
        self.assertEqual(len(profile['history']), 1)
        self.assertEqual(profile['history'][0]['score'], game.total)

    def test_lower_new_result_updates_last_but_keeps_best(self):
        profile = new_profile()
        record_result(profile, completed(20))
        best = profile['best_score']
        game = GameRound()
        game.start(1000)
        game.fire(False, 1000)
        game.tick(1120)
        record_result(profile, game)
        self.assertEqual(profile['last_score'], 0)
        self.assertEqual(profile['best_score'], best)
        self.assertEqual(profile['games_played'], 2)

    def test_import_old_backup_never_lowers_records_or_duplicates_history(self):
        old = new_profile()
        record_result(old, completed(70))
        local = deepcopy(old)
        record_result(local, completed(20))
        merged = merge_profiles(local, old)
        self.assertEqual(merged['best_score'], local['best_score'])
        self.assertEqual(merged['fastest_clear'], 20)
        self.assertEqual(len(merged['history']), 2)
        again = merge_profiles(merged, old)
        self.assertEqual(again, merged)

    def test_history_is_bounded(self):
        profile = new_profile()
        for _ in range(25):
            record_result(profile, completed())
        self.assertEqual(profile['games_played'], 25)
        self.assertEqual(len(profile['history']), 20)


class StorageTests(unittest.TestCase):
    def setUp(self):
        # 所有测试文件只写入仓库外的本地测试目录，保留失败证据。
        root = Path(__file__).resolve().parents[2] / 'minifps-local' / 'test-data'
        self.directory = root / uuid.uuid4().hex
        self.directory.mkdir(parents=True)
        self.path = self.directory / 'save.json'

    def test_atomic_write_read_and_previous_backup(self):
        first = fixture()
        SaveStore.write(self.path, first)
        second = fixture()
        second['profile']['best_score'] = 1500
        SaveStore.write(self.path, second)
        self.assertEqual(SaveStore.read(self.path)['profile']['best_score'], 1500)
        self.assertEqual(SaveStore.read(str(self.path) + '.bak')['profile']['best_score'], 0)
        self.assertEqual(list(self.directory.glob('*.tmp')), [])

    def test_failed_replace_keeps_previous_save_and_cleans_temp_file(self):
        SaveStore.write(self.path, fixture())
        previous = self.path.read_bytes()
        with patch('minifps.os.replace', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                SaveStore.write(self.path, fixture())
        self.assertEqual(self.path.read_bytes(), previous)
        self.assertEqual(list(self.directory.glob('*.tmp')), [])

    def test_corrupted_file_recovers_backup_and_preserves_corrupt_copy(self):
        SaveStore.write(self.path, fixture())
        SaveStore.write(self.path, fixture())
        self.path.write_text('{interrupted', encoding='utf-8')
        recovered, notice = SaveStore.load_with_backup(self.path)
        self.assertIsNotNone(recovered)
        self.assertIn('Recovered', notice)
        SaveStore.write(self.path, recovered)
        self.assertEqual(len(list(self.directory.glob('save.corrupt-*.json'))), 1)
        self.assertIsNotNone(SaveStore.read(str(self.path) + '.bak'))

    def test_missing_main_can_recover_backup(self):
        SaveStore.write(str(self.path) + '.bak', fixture())
        recovered, notice = SaveStore.load_with_backup(self.path)
        self.assertIsNotNone(recovered)
        self.assertIn('Recovered', notice)

    def test_missing_or_irrecoverable_data_has_no_silent_success(self):
        self.assertEqual(SaveStore.load_with_backup(self.path), (None, ''))
        self.path.write_text('broken', encoding='utf-8')
        recovered, notice = SaveStore.load_with_backup(self.path)
        self.assertIsNone(recovered)
        self.assertTrue(notice)
        self.assertEqual(self.path.read_text(), 'broken')

    def test_oversized_or_malformed_input_is_rejected(self):
        self.path.write_text(' ' * (1024 * 1024 + 1), encoding='utf-8')
        with self.assertRaises(SaveError):
            SaveStore.read(self.path)
        self.path.write_text('{"format_version": NaN}', encoding='utf-8')
        with self.assertRaises(SaveError):
            SaveStore.read(self.path)

    def test_invalid_import_does_not_overwrite_existing_save(self):
        SaveStore.write(self.path, fixture())
        before = self.path.read_bytes()
        bad = fixture()
        bad['session']['birds'] = []
        with self.assertRaises(SaveError):
            SaveStore.write(self.path, bad)
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
