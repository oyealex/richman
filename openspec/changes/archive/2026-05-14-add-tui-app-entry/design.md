## Context

当前 CLI（`richman/cli.py`）使用 Typer 库，有两个子命令：`play`（控制台模式）和 `version`。`richman/app.py` 提供 `run_game()` 函数装配配置/玩家/引擎并运行控制台游戏。`GameScreen`（`screens/game.py`）已实现引擎步进驱动循环，但缺少将其接入 Textual App 的入口。

`RichmanTuiApp`（`adapters/textual_tui/app.py`）目前是纯展示用的 `App[None]` 子类，不持有引擎也不推送 GameScreen。测试中手动创建 GameScreen 并通过 `app.push_screen(screen)` 使用。

目标是最小化改动，复用现有 `app.py` 中的工厂函数（`build_default_config`、`create_engine`、`create_players`），新增 TUI 入口路径。

## Goals / Non-Goals

**Goals:**
- 新增 `richman tui` CLI 子命令，可通过命令行启动一局 TUI 游戏
- CLI 参数：`--players`（总玩家数，1 人类 + N-1 AI）、`--seed`、`--config`。暂不引入 `--max-turns`（GameScreen 当前无界数支持，后续 change 补）
- `RichmanTuiApp` 在 `on_mount` 中自动推送 `GameScreen` 开始游戏循环
- app 层提供 `run_tui_game()` 函数，创建含一个 HumanPlayer 和若干 AIPlayer 的默认对局
- 保留 `richman play` 控制台模式行为不变

**Non-Goals:**
- 不做完整 TitleScreen / SetupScreen（仅打通默认对局闭环）
- 不修改 GameScreen 的引擎驱动逻辑
- 不修改 BoardWidget / ActionBar 的内部实现
- 不实现 TUI 模式的配置文件热加载

## Decisions

### 1. CLI 结构：新增 `tui` Typer 子命令

在 `cli.py` 中新增第三个子命令 `tui`，参数集对齐 `play` 命令。直接调用 app 层的 `run_tui_game()`。

**选择理由**：Typer 子命令模式最简单，与现有 `play`/`version` 一致，没有引入新库或参数解析框架。

**备选**：创建独立的 `richman-tui` console_scripts 入口点。不选因为会增加维护负担且与 `richman tui` 语义重复。

### 2. app 层装配：`run_tui_game()` 函数

新增 `run_tui_game(players_count: int, seed: int | None, config_path: Path | None)` 函数，逻辑为：

1. 调用 `build_default_config()` 或 `load_config(config_path)` 获取 GameConfig
2. 调用 `create_tui_players(players_count)` 创建玩家列表
3. 调用 `create_engine(config, players, seed=seed)` 创建 GameEngine
4. 创建 `RichmanTuiApp(engine=engine, config=config, player_controllers=players)` 并 `app.run()`

新增 `create_tui_players(players_count: int) -> tuple[Player, ...]`：创建 1 个 `HumanPlayer("玩家")` + (players_count - 1) 个 `AIPlayer("AI 1", ...)`。HumanPlayer 不需要 InputContext——GameScreen 直接响应 ActionBar 消息提交 EngineInput，不经过 player 的 input context 路径。

### 3. RichmanTuiApp 改造

`RichmanTuiApp.__init__` 增加 `engine: GameEngine` 和 `player_controllers: Sequence[Player]` 参数（保持向后兼容，有默认值 None）。

`on_mount()` 中：当 `engine` 和 `player_controllers` 都存在时，推送 `GameScreen(engine, config, player_controllers)`。

当参数为 None 时（旧的测试/展示用路径），维持现有静态展示行为。

### 4. CLI `--players` 语义

`tui --players` 表示**总玩家数**（含人类玩家），与 `play --players`（AI 数量）形式对齐但语义不同。`tui --players 3` → 1 人类 + 2 AI；`play --players 3` → 3 AI。理由：TUI 固定有 1 个本地人类玩家，用总人数更直观；play 的语义保持不变。

### 5. 测试策略

CLI smoke test：用 `CliRunner` 验证 `richman tui` 命令参数解析正确，不实际启动 Textual App。

App smoke test：验证 `run_tui_game()` 创建的 engine/config/players 正确，通过 monkeypatch `RichmanTuiApp.run` 避免启动全屏 TUI。

## Risks / Trade-offs

- **TUI 启动即进入游戏**：没有初始画面/配置界面，用户体验略简陋，但这是明确排除的 Non-Goal，后续可扩展
