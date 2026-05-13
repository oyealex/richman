## 1. 新增 TitleScreen

- [x] 1.1 创建 `src/richman/adapters/textual_tui/screens/title.py`，定义 `TitleScreen(Screen[None])` 类
- [x] 1.2 `compose()` 渲染居中欢迎文字（"大富翁"）和"按 Enter 开始"提示
- [x] 1.3 绑定 Enter 键 → 通过 `self.app.config`、`self.app.seed`、`self.app.player_count` 创建 `SetupScreen(config=..., seed=..., player_count=...)` 并 `await self.app.push_screen(...)`
- [x] 1.4 绑定 q 键 → 退出应用

## 2. 新增 SetupScreen

- [x] 2.1 创建 `src/richman/adapters/textual_tui/screens/setup.py`，定义 `SetupScreen(Screen[None])` 类
- [x] 2.2 `__init__` 接收 `config: GameConfig`、`seed: int | None`、`player_count: int`
- [x] 2.3 `compose()` 渲染：玩家数量选择（2-4）、人类玩家名称输入框（默认"玩家"）、AI 名称标签（固定显示，不可编辑）、开始游戏按钮
- [x] 2.4 玩家数变更时动态更新 AI 名称标签数量
- [x] 2.5 点击"开始游戏"时：读取玩家数量和人类玩家名称 → 调用 `create_tui_players(player_count, human_name=...)` → 调用 `create_engine(config, players, seed)` → `await self.app.push_screen(GameScreen(engine, config, players))`

## 3. 扩展 create_tui_players

- [x] 3.1 `create_tui_players(players_count, human_name: str = "玩家")` 新增 `human_name` 参数，用于 `HumanPlayer(human_name)`

## 4. 调整 RichmanTuiApp 三种模式

- [x] 4.1 `RichmanTuiApp.__init__` 保留所有现有参数（`snapshot`、`config`、`engine`、`player_controllers`），新增 `run_game_mode: bool = False`、`seed: int | None = None`、`player_count: int = 2`
- [x] 4.2 暴露 `seed` 和 `player_count` 属性
- [x] 4.3 `on_mount()` 三模式：`run_game_mode=True` → 推送 TitleScreen；`engine and player_controllers` → 推送 GameScreen；否则 → 静态展示

## 5. 调整 run_tui_game

- [x] 5.1 `run_tui_game()` 不再创建 engine 和 players，改为传入 `run_game_mode=True`、`seed`、`player_count`
- [x] 5.2 移除 `run_tui_game` 内部对 `create_tui_players` 和 `create_engine` 的调用

## 6. 测试

- [x] 6.1 TitleScreen smoke test：`app.run_test()` 验证欢迎文字和 Enter 按键
- [x] 6.2 SetupScreen smoke test：验证默认值（玩家数 2、人类名称"玩家"）、玩家数变更时 AI 标签变化
- [x] 6.3 SetupScreen smoke test：验证"开始游戏"后推送 GameScreen，且玩家名称正确
- [x] 6.4 App 装配 test：验证 `run_tui_game()` 传入 RichmanTuiApp 的参数（run_game_mode=True 等）
- [x] 6.5 App 装配 test：验证 engine + player_controllers 快速路径仍直接推送 GameScreen
- [x] 6.6 CLI test：更新以匹配调整后的 `run_tui_game` 行为
- [x] 6.7 更新 create_tui_players 测试，验证 human_name 参数生效
