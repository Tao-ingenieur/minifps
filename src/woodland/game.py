"""启动应用，协调输入、对局、存档、界面和射击流程。"""
from copy import deepcopy
import math
import os
import random
import sys
import tempfile
import uuid
from pathlib import Path
from time import perf_counter
from ursina import (Entity, Ursina, Vec3, application, camera, color, destroy,
                    held_keys, invoke, mouse, raycast, scene, time, window)
from .config import VERSION, SAVE_FORMAT, RULESET, SLOTS, TARGET_COUNT, ROUND_SECONDS, SHOT_COOLDOWN
from .scoring import GameRound, SaveError
from .profiles import ACHIEVEMENTS, new_profile, record_result, merge_profiles
from .storage import SaveStore, validate_save
from .dialogs import choose_save_file
from .world import build_world
from .weapon import build_weapon
from .targets import build_targets
from .ui import build_ui
from .player import PlayerController
from .smoke import verify_aim

def main():
    movement_test = '--movement-smoke-test' in sys.argv
    smoke_test = '--smoke-test' in sys.argv or movement_test
    app = Ursina(title=f'MiniFPS | Woodland v{VERSION}', borderless=False, fullscreen=False,
                 size=(1280, 720), development_mode=False)
    # 统一交给游戏处理 F11，避免引擎调试快捷键和自定义逻辑各切换一次。
    window.input_entity.enabled = False
    window.fullscreen = False
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
    part, tint = build_world(rng)
    player = PlayerController(position=(0, .1, -10), speed=5, smoke_test=smoke_test)
    gun = build_weapon(part, tint)
    birds, make_bird, perches, perch_models = build_targets(part, tint, rng)
    (hud, counter, status, feedback, personal, reticle, toast, menu,
     menu_title, menu_subtitle, details, menu_notice, primary, restart_button,
     history_button, save_button, load_button, export_button, import_button,
     display_button, about_button, exit_button, face_button, back_button, buttons) = build_ui(tint)
    game = GameRound()
    recoil = sway_time = 0
    notice = initial_notice
    notice_until = 0
    next_autosave = 0
    menu_mode = 'normal'
    pending_action = None
    unlocked = []
    looking = False
    layout_aspect = None

    def notify(text):
        nonlocal notice, notice_until
        notice = text.replace('\n', ' ')[:115]
        menu_notice.text = notice
        toast.text = notice
        notice_until = perf_counter() + 5

    def sync_pointer():
        player.configure_pointer(game.state == 'playing' and not menu.enabled,
                                 window.fullscreen, looking)

    def layout_ui():
        nonlocal layout_aspect
        aspect = window.aspect_ratio
        if layout_aspect == aspect:
            return
        layout_aspect = aspect
        # 按屏幕左边缘定位，16:10 全屏和较窄窗口也不会裁掉分数。
        scale = min(1, aspect / 1.6)
        hud.scale = scale
        hud.x = -aspect / 2 + .04 + .85 * scale
        hud.y = .46 * (1 - scale)
        menu.scale = min(1, max(.3, (aspect - .08) / 1.36))

    def toggle_fullscreen():
        if not window.main_monitor:
            notify('Cannot detect monitor. Windowed mode remains available.')
            return
        was_playing = game.state == 'playing'
        if was_playing:
            pause_round()
        window.fullscreen = not window.fullscreen
        window.borderless = window.fullscreen
        # Ursina 恢复切换前的窗口尺寸和位置；UI 根据实际宽高比自动重排。
        sync_pointer()
        show_menu()
        notify(('Fullscreen' if window.fullscreen else 'Windowed') +
               ' mode. ESC / ENTER resumes; move mouse to look; RMB zooms.')

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
        nonlocal menu_mode, looking
        menu_mode = mode
        layout_ui()
        looking = False
        menu.enabled = True
        hud.enabled = False
        player.ignore = True
        reticle.enabled = gun.enabled = False
        camera.fov = 76
        player.configure_pointer(False, window.fullscreen, False)
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
        display_button.text = 'WINDOWED / F11' if window.fullscreen else 'FULLSCREEN / F11'
        if mode == 'about':
            primary.text = 'BACK TO MENU'
            menu_title.text = 'ABOUT MINIFPS'
            menu_subtitle.text = f'WOODLAND / VERSION {VERSION}'
            details.text = ('A single-player woodland precision shooting game.\n'
                            'Built with Python + Ursina + Panda3D.\n'
                            f'Save format {SAVE_FORMAT}; local saves remain compatible with v0.4.0.\n\n'
                            'F11 / Alt+Enter: fullscreen or windowed.\n'
                            'Mouse moves view; RMB zooms; windowed cursor can leave.\n'
                            'ESC / P: pause; HOME: face birds. F5 save; F9 load.\n'
                            'Source: github.com/Tao-ingenieur/minifps')
        elif mode == 'history':
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
                            'ESC pauses; F11 fullscreen; F1 About / version.\n'
                            'Mouse moves view; RMB zooms; windowed cursor can leave.\n'
                            'Export / Import JSON transfers progress to another PC.')
        elif game.state == 'paused':
            menu_title.text = 'PAUSED'
            menu_subtitle.text = f'CURRENT {game.score}  /  BEST {profile["best_score"]}  /  LAST {profile["last_score"]}'
            details.text = (f'Birds {game.hits}/8    Shots {game.shots}    Accuracy {game.accuracy:.1%}\n'
                            f'Time left {ROUND_SECONDS - game.finished_elapsed:.1f}s    Streak {game.streak}\n\n'
                            'Timer stopped. ESC / P / ENTER resumes.\n'
                            'F5: quick save     F9: quick load\n'
                            'F6: export a JSON file     F7: import a JSON file\n'
                            'NEW ROUND asks before discarding this attempt.\n'
                            'F11 fullscreen / windowed; F1 About and version.')
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
        sync_pointer()
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
            # 点击 CONTINUE 已经表达继续意图，不再要求多按一次才能移动。
            resume_round()
            notify('Save continued. WASD moves; HOME faces a remaining bird.')
        elif game.state != 'playing':
            start_round()

    def confirm(title, text, action):
        nonlocal pending_action, menu_mode
        pause_round()
        pending_action = action
        menu_mode = 'confirm'
        menu_title.text = title
        menu_subtitle.text = 'YOUR BEST SCORE AND RECORDS WILL BE KEPT'
        details.text = text + '\n\nPress ENTER to confirm, ESC to cancel.'
        for item in buttons:
            item.enabled = item in (primary, back_button)
        primary.text = 'CONFIRM / ENTER'
        primary.on_click = accept_confirmation
        back_button.text = 'CANCEL / ESC'
        back_button.on_click = cancel_confirmation

    def accept_confirmation():
        nonlocal pending_action, menu_mode
        action, pending_action = pending_action, None
        menu_mode = 'normal'
        if action:
            action()
        back_button.text = 'BACK / ESC'

    def cancel_confirmation():
        nonlocal pending_action
        pending_action = None
        back_button.text = 'BACK / ESC'
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

    def face_birds():
        if game.state not in ('playing', 'paused') or not birds:
            notify('Start or continue a round first. HOME faces a remaining bird.')
            return
        target = min(birds, key=lambda bird: (bird.world_position - camera.world_position).length())
        direction = target.world_position - camera.world_position
        player.rotation_y = math.degrees(math.atan2(direction.x, direction.z))
        horizontal = math.hypot(direction.x, direction.z)
        player.camera_pivot.rotation_x = max(-70, min(70, -math.degrees(math.atan2(direction.y, horizontal))))
        mouse.velocity = Vec3(0, 0, 0)
        if game.state == 'paused':
            resume_round()
        notify('Facing a remaining bird. Hold RMB to look around.')

    restart_button.on_click = request_restart
    history_button.on_click = lambda: (pause_round(), show_menu('history'))
    save_button.on_click = save_quick
    load_button.on_click = lambda: load_file(store.quick)
    export_button.on_click = export_file
    import_button.on_click = import_file
    exit_button.on_click = lambda: confirm('EXIT GAME?',
        'Save progress and close MiniFPS? You can continue next time.', exit_game)
    display_button.on_click = toggle_fullscreen
    about_button.on_click = lambda: (pause_round(), show_menu('about'))
    face_button.on_click = face_birds

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
        nonlocal looking
        if menu_mode == 'confirm':
            if key == 'enter':
                accept_confirmation()
            elif key in ('p', 'escape'):
                cancel_confirmation()
            return
        if key in ('f11', 'alt-enter') or (key == 'enter' and
                (held_keys['alt'] or held_keys['left alt'] or held_keys['right alt'])):
            toggle_fullscreen()
        elif key == 'f1':
            pause_round()
            show_menu('about')
        elif key in ('escape', 'p'):
            if menu_mode in ('history', 'about'):
                show_menu()
            elif game.state == 'playing':
                pause_round()
            elif game.state == 'paused':
                resume_round()
            else:
                show_menu()  # ESC 在首页或结算页也不退出。
        elif key == 'r':
            request_restart()
        elif key == 'home':
            face_birds()
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
        elif key == 'left mouse down' and game.state == 'playing' and not mouse.is_outside:
            shoot()
        elif key == 'right mouse down' and game.state == 'playing' and not mouse.is_outside:
            looking = True
            sync_pointer()
        elif key == 'right mouse up':
            looking = False
            sync_pointer()

    def update_view():
        nonlocal recoil, sway_time
        layout_ui()
        toast.enabled = game.state == 'playing' and perf_counter() < notice_until
        if game.state != 'playing':
            return
        now = perf_counter()
        game.tick(now)
        refresh_hud(now)
        if game.state == 'timeout':
            finish_round()
            return
        # 自由鼠标模式下 has_mouse() 可在窗口仍有焦点时返回 False。
        # 只以真实失焦暂停；鼠标移出不能把正常的 WASD 输入停掉。
        if not smoke_test and not app.win.getProperties().getForeground():
            pause_round()
            notify('Window lost focus. Paused; cursor released.')
            return
        sync_pointer()
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
            nonlocal profile, game, saved_session, looking
            try:
                # 自检目录独立，绝不读取或改写玩家的真实存档。
                assert game.state == 'ready' and menu.enabled and player.ignore
                assert not window.fullscreen and not mouse.locked
                handle_input('escape')
                assert game.state == 'ready' and menu.enabled
                if '--menu-screenshot' in sys.argv:
                    screenshot(sys.argv[sys.argv.index('--menu-screenshot') + 1])
                mouse.hovered_entity = primary
                app.input('left mouse down')
                app.input('left mouse up')
                mouse.hovered_entity = None
                assert game.state == 'playing' and len(birds) == 8
                assert game.shots == 0
                assert not mouse.locked and mouse.visible
                handle_input('escape')
                assert game.state == 'paused' and menu.enabled and not mouse.locked
                frozen = game.elapsed(perf_counter() + 60)
                assert frozen == game.finished_elapsed
                handle_input('escape')
                assert game.state == 'playing' and not menu.enabled and not mouse.locked
                handle_input('f1')
                assert menu_mode == 'about' and VERSION in menu_subtitle.text
                assert not mouse.locked and player.ignore
                if '--about-screenshot' in sys.argv:
                    screenshot(sys.argv[sys.argv.index('--about-screenshot') + 1])
                handle_input('escape')
                assert menu_mode == 'normal' and game.state == 'paused'
                handle_input('escape')
                assert game.state == 'playing'
                if '--display-smoke-test' in sys.argv and window.main_monitor:
                    old_size = tuple(window.size)
                    app.input('f11')
                    assert window.fullscreen and window.borderless and game.state == 'paused'
                    app.graphicsEngine.renderFrame()
                    app.graphicsEngine.renderFrame()
                    held_keys['alt'] = 1
                    app.input('enter')
                    held_keys['alt'] = 0
                    assert not window.fullscreen and not window.borderless
                    app.graphicsEngine.renderFrame()
                    app.graphicsEngine.renderFrame()
                    assert tuple(window.size) == old_size
                    handle_input('escape')
                assert game.state == 'playing' and not mouse.locked
                looking = True
                sync_pointer()
                assert player.look_sensitivity == 20
                looking = False
                sync_pointer()
                assert player.look_sensitivity == 35 and mouse.visible
                verify_aim(player, sync_pointer, handle_input)
                exit_button.on_click()
                assert menu_mode == 'confirm' and game.state == 'paused'
                handle_input('escape')
                assert menu_mode == 'normal' and game.state == 'paused'
                handle_input('escape')
                assert game.state == 'playing'
                bird = birds[0]
                bird.world_position = camera.world_position + camera.forward * 3
                shoot(max(perf_counter(), game.last_shot + SHOT_COOLDOWN))
                assert game.hits == 1 and len(birds) == 7
                player.position = (1, 0, -8)
                player.rotation_y = 12
                player.camera_pivot.rotation_x = 5
                save_quick()
                snapshot = store.read(store.quick)
                assert snapshot['session']['round']['hits'] == 1
                assert len(snapshot['session']['birds']) == 7
                game = GameRound()
                saved_session = snapshot['session']
                show_menu()
                primary_action()
                assert game.state == 'playing' and not player.ignore and not menu.enabled
                assert game.score == 100 and len(birds) == 7
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
                print('SMOKE TEST PASSED: ESC pause, About, cursor policy, display, saves and results', flush=True)
            except Exception:
                import traceback
                traceback.print_exc()
                sys.exit(1)
            application.quit()
        def movement_verify():
            from panda3d.core import Point2
            # 不直接调用 player.update：让真正的引擎帧循环消费 raw WASD 输入。
            cases = [('w', 2, 1), ('s', 2, -1), ('a', 0, -1), ('d', 0, 1)]
            modes = [False, True] if '--display-smoke-test' in sys.argv and window.main_monitor else [False]
            origin = Vec3(0, 0, -10)

            def later(callback, delay=.35):
                def run(task):
                    try:
                        callback()
                    except Exception:
                        import traceback
                        traceback.print_exc()
                        sys.exit(1)
                    return task.done
                app.taskMgr.doMethodLater(delay, run, 'movement-check-' + uuid.uuid4().hex)

            def visible_birds():
                count = 0
                for bird in birds:
                    projected = Point2()
                    point = app.cam.getRelativePoint(scene, bird.world_position)
                    if camera.lens.project(point, projected) and abs(projected.x) <= 1 and abs(projected.y) <= 1:
                        count += 1
                return count

            def enter_case(mode_index, index):
                if index == 4:
                    if mode_index + 1 < len(modes):
                        enter_mode(mode_index + 1)
                    else:
                        finish()
                    return
                player.position = origin
                player.rotation = player.camera_pivot.rotation = (0, 0, 0)
                mouse.velocity = Vec3(0, 0, 0)
                key, axis, sign = cases[index]
                app.input(key, is_raw=True)
                def measure():
                    app.input_up(key, is_raw=True)
                    delta = player.position[axis] - origin[axis]
                    assert game.state == 'playing' and not player.ignore, 'Movement unexpectedly paused'
                    assert delta * sign > .25, f'{key.upper()} failed to move: delta={delta}'
                    assert len(birds) == 8 and visible_birds() >= 5, 'Birds disappeared from the field'
                    print(f'MOVEMENT PASS {"fullscreen" if modes[mode_index] else "windowed"} '
                          f'{key.upper()}: {delta:.3f}, visible birds={visible_birds()}', flush=True)
                    enter_case(mode_index, index + 1)
                later(measure)

            def enter_mode(mode_index):
                if window.fullscreen != modes[mode_index]:
                    toggle_fullscreen()
                start_round()
                # 让真正引擎帧消费持续鼠标输入，而非只校验灵敏度配置。
                # 只替换输入采样；使用生产版 PlayerController.update 和摄像机。
                old_yaw, old_pitch = player.rotation_y, player.camera_pivot.rotation_x
                samples = [0]
                deadline = perf_counter() + 12
                def sample_pointer():
                    samples[0] += 1
                    return (.02, .01), True
                player.read_pointer = sample_pointer
                def aim_measure():
                    if samples[0] < 6:
                        assert perf_counter() < deadline, 'Engine did not process aiming frames'
                        later(aim_measure, .1)
                        return
                    del player.read_pointer
                    assert player.rotation_y > old_yaw + .3, 'Frame-driven yaw failed'
                    assert player.camera_pivot.rotation_x < old_pitch - .1, 'Frame-driven pitch failed'
                    print(f'AIM FRAME PASS {"fullscreen" if modes[mode_index] else "windowed"}: '
                          f'yaw={player.rotation_y:.2f}, pitch={player.camera_pivot.rotation_x:.2f}', flush=True)
                    enter_case(mode_index, 0)
                later(aim_measure, .2)

            def finish():
                if window.fullscreen:
                    toggle_fullscreen()
                start_round()
                assert visible_birds() == 8, 'Fresh round must show all 8 birds'
                if '--screenshot' in sys.argv:
                    screenshot(sys.argv[sys.argv.index('--screenshot') + 1])
                # 模拟旧存档朝向天空或背后：Home 必须能找回真实目标，且不清分。
                saved_score, saved_id = game.score, game.round_id
                player.rotation_y = 180
                player.camera_pivot.rotation_x = 80
                handle_input('home')
                assert visible_birds() >= 1 and game.score == saved_score and game.round_id == saved_id
                verify_aim(player, sync_pointer, handle_input)
                assert not mouse.locked and mouse.visible
                handle_input('escape')
                assert game.state == 'paused' and player.ignore
                handle_input('escape')
                assert game.state == 'playing' and not player.ignore
                print('MOVEMENT SMOKE PASSED: real-frame WASD, 8 visible birds, Home and ESC', flush=True)
                application.quit()

            enter_mode(0)

        invoke(movement_verify if movement_test else verify, delay=1)

    app.run()
