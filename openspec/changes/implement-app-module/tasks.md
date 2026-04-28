## 1. App 模块骨架

- [x] 1.1 新增 `src/richman/app.py`，定义 app 层公共装配函数
- [x] 1.2 实现 `build_default_config()`，提供可运行默认棋盘、地块和机会卡配置
- [x] 1.3 实现 `create_players(count)`，按数量创建稳定命名的 AI 玩家并校验 2-4 人范围

## 2. Engine 装配和运行入口

- [x] 2.1 实现 `create_engine(config, players, renderer, seed)`，创建 Board 并调用 `GameEngine.create`
- [x] 2.2 实现 `run_game(players_count, max_turns, seed, renderer)`，启动 engine 并返回最终 `InternalGameState`

## 3. CLI 接入

- [x] 3.1 更新 `richman play` 命令，支持 `--players`、`--max-turns`、`--seed`
- [x] 3.2 让 `richman play` 使用 app 装配入口启动真实游戏流程
- [x] 3.3 对非法玩家数量给出 CLI 参数错误并避免启动游戏

## 4. 测试

- [x] 4.1 新增 `tests/test_app.py` 覆盖默认配置、玩家创建、engine 装配和受限运行
- [x] 4.2 更新 `tests/test_cli.py` 覆盖 `play` 命令的受限运行和非法玩家数量

## 5. 文档和验证

- [x] 5.1 更新 `docs/DEVELOPMENT_PROGRESS.md`，记录 app 模块实现状态
- [x] 5.2 运行 `uv run pytest`
- [x] 5.3 运行 `uv run ruff check`
- [x] 5.4 运行 `uv run ruff format --check`
- [x] 5.5 运行 `uv run mypy src`
