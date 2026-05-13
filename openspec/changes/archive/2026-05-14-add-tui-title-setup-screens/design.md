## Context

当前 `RichmanTuiApp.on_mount` 直接推送 `GameScreen` 开始游戏。需要插入 TitleScreen 和 SetupScreen 两个前置屏幕。Textual 的 `push_screen` / `switch_screen` 天然支持多屏幕栈，只需新增两个 Screen 子类并调整推送顺序。

现有 `run_tui_game()` 在调用 `app.run()` 之前就创建了 engine 和 players。引入 SetupScreen 后，玩家数量和名称可由用户调整，engine 创建需延后到 SetupScreen 用户确认之后。但 app 层的工厂函数（`create_tui_players`、`create_engine`）保持复用，调用时机推迟到 SetupScreen 内部。

## Goals / Non-Goals

**Goals:**
- 新增 TitleScreen：欢迎文字，按键导航到 SetupScreen
- 新增 SetupScreen：玩家数量（2-4）、人类玩家名称编辑、AI 名称固定、"开始游戏"按钮
- 屏幕流：TitleScreen → SetupScreen → GameScreen
- 延后 engine 创建到 SetupScreen 确认后
- 扩展 `create_tui_players(players_count, human_name)` 增加可选参数，复用 `create_engine()`、`build_default_config()`

**Non-Goals:**
- 不修改 GameScreen 内部
- 不修改 `create_engine`、`build_default_config`
- 不实现配置文件的 SetupScreen 内选择（config 仍从 CLI 传）
- 不实现 TitleScreen 的动画或复杂美术

## Decisions

### 1. engine 创建时机延后

`run_tui_game()` 不再创建 engine 和 players。改为将 `config`、`seed`、`player_count` 传给 `RichmanTuiApp`（`run_game_mode=True`）。RichmanTuiApp 暴露 `config`、`seed`、`player_count` 属性。TitleScreen 创建 `SetupScreen(config=app.config, seed=app.seed, player_count=app.player_count)`。SetupScreen 用户点击"开始游戏"后，调用 `create_tui_players(count, human_name=用户编辑的名称)` 和 `create_engine(config, players, seed)` 创建 engine，然后推送 GameScreen。

**选择理由**：用户可以在 SetupScreen 中修改玩家数量和名称，engine 必须用最终玩家列表创建。延后创建避免"先建后弃"的浪费。

**备选**：run_tui_game 预建 engine，SetupScreen 只允许修改名称（不允许改人数）。不选因为限制太死，用户无法调整人数。

### 2. RichmanTuiApp 三种模式并存

`RichmanTuiApp.__init__` 保留所有现有参数，新增 `run_game_mode: bool = False`、`seed: int | None = None`、`player_count: int = 2`。

三种模式（按优先级判断）：
1. **游戏模式**（`run_game_mode=True`）：`on_mount` 推送 `TitleScreen`，走 TitleScreen → SetupScreen → GameScreen 流
2. **快速启动模式**（`engine is not None and player_controllers is not None`）：`on_mount` 直接推送 `GameScreen`（保留上一轮建立的路径）
3. **静态展示模式**（默认）：仅 compose 棋盘，不推送任何 screen

TitleScreen 通过 `self.app.config`、`self.app.seed`、`self.app.player_count` 取参数，创建 `SetupScreen(config=..., seed=..., player_count=...)`。

**选择理由**：保留 engine 快速路径方便测试和 smoke test；`run_game_mode` 语义明确不依赖 None 判断。

### 3. TitleScreen 设计

简单的 Static 文字展示 + 按键绑定。按 Enter 或 Space 时 `app.push_screen(SetupScreen(...))`。

### 4. SetupScreen 设计

使用 Textual 内置 Input widget 做玩家名称编辑，Select 或数字输入做玩家数量。

结构：
- 顶部 Static："游戏设置"
- 玩家数量选择：Select 或 Input（2-4）
- 玩家名称列表：动态 Input 列表，根据玩家数量显示对应数量的输入框
- "开始游戏" Button

点击"开始游戏"时：
1. 读取当前玩家数量和人类玩家名称
2. 调用 `create_tui_players(count, human_name=用户编辑的名称)` 创建玩家列表
3. 调用 `create_engine(config, players, seed)` 创建 engine
4. `await self.app.push_screen(GameScreen(engine, config, players))`

`create_tui_players` 签名扩展为 `(players_count: int, human_name: str = "玩家") -> tuple[Player, ...]`。`human_name` 用于构造 `HumanPlayer(human_name)`，AI 名称固定。

### 5. RichmanTuiApp 属性暴露

`RichmanTuiApp` 暴露以下只读属性供 Screen 通过 `self.app` 访问：
- `config: GameConfig`（已有）
- `seed: int | None`（新增）
- `player_count: int`（新增，默认 2）

## Risks / Trade-offs

- **engine 创建延后**：run_tui_game 的"装配"职责被分散到 SetupScreen，app.py 的 run_tui_game 变薄。缓解：SetupScreen 仍调用相同的 app 层工厂函数，逻辑未重复。
- **SetupScreen 内的 engine 创建是同步调用**：`create_engine` 涉及 board 创建和状态初始化，但数据量小，不会阻塞 UI。若后续变慢可改为 worker。
