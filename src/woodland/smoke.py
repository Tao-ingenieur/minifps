"""引擎内的瞄准回归检查：真实玩家/摄像机对象，不依赖 Home 纠正视角。"""
def verify_aim(player, sync_pointer, handle_input):
    old_yaw = player.rotation_y
    old_pitch = player.camera_pivot.rotation_x
    sync_pointer()
    # 与运行时相同的更新入口，固定鼠标位移，避免测试依赖桌面光标位置。
    player.update_look((0, 0), inside=True)
    player.update_look((.1, .05), inside=True)
    assert player.rotation_y > old_yaw + 3, 'Windowed mouse cannot turn yaw'
    assert player.camera_pivot.rotation_x < old_pitch - 1, 'Mouse cannot move pitch'
    # Home 之后照样能连续瞄准，不需要再次按 Home 或按住右键。
    handle_input('home')
    yaw = player.rotation_y
    player.update_look((.1, 0), inside=True)
    assert player.rotation_y > yaw + 3, 'Home left aiming disabled'
    yaw = player.rotation_y
    player.update_look((10, 10), inside=False)
    assert player.rotation_y == yaw, 'Outside-window mouse moved view'
    player.update_look((10, 10), inside=True)
    assert player.rotation_y == yaw, 'Pointer re-entry caused a jump'
    player.update_look((.1, 0), inside=True)
    assert player.rotation_y > yaw + 3
    handle_input('escape')
    yaw = player.rotation_y
    player.update_look((.1, .1), inside=True)
    assert player.rotation_y == yaw, 'Pause did not freeze aiming'
    handle_input('escape')
    # 暂停时实体不更新：恢复首帧仍需屏蔽陈旧/重定位位移。
    handle_input('escape')
    handle_input('escape')
    yaw = player.rotation_y
    player.update_look((10, 10), inside=True)
    assert player.rotation_y == yaw, 'Resume without paused frames caused a jump'
    player.rotation_y = old_yaw
    player.camera_pivot.rotation_x = old_pitch
    player.update_look((0, 0), inside=True)
    print('AIM PASS: mouse yaw/pitch, Home then aim, outside/re-entry, pause/resume', flush=True)
