## Why

当前 `richman` CLI 只有 `play`（控制台模式）和 `version` 两个子命令，无法启动 TUI 模式。上一轮已实现了 `GameScreen`（步进驱动）和 `ActionBar`（输入控件），但缺少将二者装配为可运行 App 的入口。需要新增 `richman tui` 命令，打通"命令行启动一局默认 TUI 游戏"的完整闭环。

## What Changes

- 新增 `richman tui` CLI 子命令，接受 `--players`、`--seed`、`--config` 参数。`--players` 为总玩家数（1 人类 + N-1 AI），与 `play --players`（AI 数量）形式对齐但语义不同；暂不引入 `--max-turns`（GameScreen 当前无界数支持）
- 在 app 层新增 `run_tui_game()` 函数：装配默认 GameConfig、Board、玩家列表（含 HumanPlayer）、GameEngine
- 修改 `RichmanTuiApp`：在 `on_mount` 中推送 `GameScreen` 进入引擎驱动循环
- `RichmanTuiApp.__init__` 增加 `engine` 和 `player_controllers` 参数
- 保留现有 `richman play` 行为不变
- 补 CLI/app smoke test，用 `TESTING` 环境变量或 monkeypatch 避免测试中阻塞启动全屏 TUI

## Capabilities

### New Capabilities

- `tui-app-entry`: `richman tui` CLI 命令和 TUI app 装配层，负责解析参数、创建默认配置/玩家/引擎、启动 RichmanTuiApp 并进入 GameScreen

### Modified Capabilities

（无——`RichmanTuiApp` 的修改是实现细节，不改变其对外规格。`GameScreen` 和 `ActionBar` 的规格不变。）

## Impact

- `src/richman/cli.py`：新增 `tui` Typer 子命令
- `src/richman/app.py`：新增 `create_tui_players(players_count)` 函数，直接创建 `HumanPlayer("玩家")` + 若干 `AIPlayer`；新增 `run_tui_game()` 装配并启动 TUI App
- `src/richman/adapters/textual_tui/app.py`：`RichmanTuiApp.__init__` 增加参数，新增 `on_mount` 推送 GameScreen
- `tests/test_cli.py`：新增 CLI smoke test
- `tests/test_textual_tui_app.py`：新增 app 装配 smoke test
