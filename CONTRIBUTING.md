# 发布与版本规范

每次向 GitHub 发布玩家能感知的变化，都必须完成下面步骤：

1. 修改 `src/minifps.py` 的 `VERSION`。新功能增加次版本号，修复增加修订版本号。
2. 在 `CHANGELOG.md` 顶部添加对应版本、日期、具体变化和修正，写清玩家会看到什么变化。
3. 同步 README 的玩法、规则和完整代码。界面改变时更新实机截图。
4. 运行计分测试和引擎自检，再通过 `build.ps1` 构建 exe 并验证。构建文件只放在同级 `minifps-local`。
5. 提交源码，创建与版本号一致的带注释标签（例如 `v0.3.0`），推送提交和该标签。
6. 为标签创建 GitHub Release，将对应 CHANGELOG 条目作为发布说明。默认不上传 exe。

测试命令（在仓库根目录执行）：

```powershell
& ..\minifps-local\.venv\Scripts\python.exe -m unittest discover -s tests -v
& ..\minifps-local\.venv\Scripts\python.exe src\minifps.py --smoke-test
```

历史版本标签不可移动或覆盖；发现问题通过新的修订版本修复。

存档或档案功能的变更必须通过 `tests/test_persistence.py`。保持旧版本格式兼容，或显式提高格式版本并提供清晰报错；不能静默清空最高分。自检应使用独立测试目录，不可读写真实玩家数据。

显示与输入变更须验证 ESC 不会退出、窗口模式能释放鼠标、About 版本号正确，执行 `--smoke-test --display-smoke-test` 检查 F11 / Alt+Enter 和窗口尺寸恢复。
