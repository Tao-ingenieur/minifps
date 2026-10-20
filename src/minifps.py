"""MiniFPS 启动入口。功能代码位于 woodland 包，可直接运行此文件。"""
from woodland.config import VERSION, SAVE_FORMAT, RULESET, SLOTS, TARGET_COUNT, ROUND_SECONDS, SHOT_COOLDOWN
from woodland.scoring import GameRound, SaveError
from woodland.profiles import new_profile, record_result, merge_profiles
from woodland.storage import SaveStore, validate_save


def main():
    # 延迟加载渲染引擎，使计分/存档测试无需初始化窗口。
    from woodland.game import main as run
    run()


if __name__ == '__main__':
    main()
