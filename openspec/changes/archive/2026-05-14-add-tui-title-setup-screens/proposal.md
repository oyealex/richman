## Why

当前 `richman tui` 启动后直接进入 GameScreen 开始对局，没有标题画面或设置环节。用户体验突兀，且无法在游戏开始前调整玩家数量或名称。需要在 GameScreen 之前插入 TitleScreen（欢迎）和 SetupScreen（设置），形成完整的 TUI 启动流程。

## What Changes

- 新增 `TitleScreen`：展示欢迎文字，按 Enter 进入 SetupScreen
- 新增 `SetupScreen`：配置总玩家数（2-4）、人类玩家名称、开始游戏按钮（本轮 AI 名称固定不编辑）
- `RichmanTuiApp.on_mount` 改为先推送 `TitleScreen`，由 TitleScreen → SetupScreen → GameScreen 形成屏幕流
- `RichmanTuiApp.__init__` 保留 `engine` / `player_controllers` 参数（直接进 GameScreen 快速路径），新增 `seed`、`player_count`、`run_game_mode: bool` 以支持 TitleScreen → SetupScreen → GameScreen 流程
- `run_tui_game()` 不再预创建 engine 和 players，改为将 config/seed/player_count 传给 RichmanTuiApp（run_game_mode=True），由 SetupScreen 确认后调用 `create_tui_players()` + `create_engine()`
- 扩展现有 `create_tui_players(players_count, human_name)` 工厂函数，增加 `human_name` 参数

## Capabilities

### New Capabilities

- `tui-title-screen`: TitleScreen 展示欢迎画面，用户按键后导航到 SetupScreen
- `tui-setup-screen`: SetupScreen 提供玩家数量选择（2-4）、人类玩家名称编辑、开始游戏按钮

### Modified Capabilities

- `tui-app-entry`: RichmanTuiApp 增加 `run_game_mode` 屏幕流分支（保留 engine 直接进 GameScreen 路径）；`create_tui_players()` 增加 `human_name` 参数；`run_tui_game()` 的 engine 创建时机延后到 SetupScreen 确认后

## Impact

- `src/richman/adapters/textual_tui/screens/title.py`：新增 TitleScreen
- `src/richman/adapters/textual_tui/screens/setup.py`：新增 SetupScreen
- `src/richman/adapters/textual_tui/app.py`：`RichmanTuiApp` 参数调整，屏幕流改为 TitleScreen 起
- `src/richman/app.py`：`run_tui_game()` 延后 engine 创建
- `tests/test_textual_tui_app.py`：更新以覆盖新屏幕流
- `tests/test_cli.py`：更新以匹配 run_tui_game 签名变更
