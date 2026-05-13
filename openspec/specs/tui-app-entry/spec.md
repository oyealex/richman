# tui-app-entry

## Purpose

`richman tui` CLI 命令和 TUI app 装配层，负责解析参数、创建默认配置/玩家/引擎、启动 RichmanTuiApp 并进入 GameScreen。

## Requirements

### Requirement: CLI provides tui subcommand

系统 SHALL 在 `richman` CLI 中提供 `tui` 子命令，接受与 `play` 对齐的参数集，启动 TUI 游戏模式。

#### Scenario: tui --players specifies total player count

- **WHEN** 用户执行 `richman tui --players 3`
- **THEN** CLI MUST 解析 `players` 为整数 3
- **AND** `--players` 语义 SHALL 为总玩家数（1 人类 + N-1 AI），与 `play --players`（AI 数量）不同

#### Scenario: tui command accepts seed option

- **WHEN** 用户执行 `richman tui --seed 42`
- **THEN** CLI MUST 解析 `seed` 为整数 42

#### Scenario: tui command accepts config option

- **WHEN** 用户执行 `richman tui --config /path/to/config.json`
- **THEN** CLI MUST 解析 `config` 为 Path 对象

#### Scenario: tui command uses defaults when options omitted

- **WHEN** 用户执行 `richman tui`（无任何参数）
- **THEN** CLI MUST 使用默认值：`players=2`、`seed=None`、`config=None`

#### Scenario: richman play behavior unchanged

- **WHEN** 用户执行 `richman play --players 2`
- **THEN** 行为 MUST 与变更前完全一致

### Requirement: run_tui_game assembles and launches TUI app

系统 SHALL 在 app 层提供 `create_tui_players(players_count)` 和 `run_tui_game(players_count, seed, config_path)` 函数。`create_tui_players` 创建 1 个 `HumanPlayer("玩家")` + (players_count - 1) 个 `AIPlayer`。`run_tui_game` 装配 GameConfig、玩家列表、GameEngine，并启动 RichmanTuiApp。

#### Scenario: run_tui_game creates one HumanPlayer

- **WHEN** 调用 `run_tui_game(players_count=2)`
- **THEN** 玩家列表中 MUST 包含恰好 1 个 `HumanPlayer` 实例
- **AND** `HumanPlayer` 的索引位置 MUST 为 0（第一个玩家）

#### Scenario: run_tui_game creates correct number of AIPlayers

- **WHEN** 调用 `run_tui_game(players_count=3)`
- **THEN** 玩家列表中 MUST 包含 2 个 `AIPlayer` 实例
- **AND** 总玩家数 MUST 为 3

#### Scenario: run_tui_game creates engine with default config

- **WHEN** 调用 `run_tui_game()` 不传 config_path
- **THEN** MUST 使用 `build_default_config()` 创建 GameConfig
- **AND** MUST 调用 `create_engine(config, players, seed=seed)` 创建 GameEngine

#### Scenario: run_tui_game creates engine with custom config

- **WHEN** 调用 `run_tui_game(config_path=Path("/custom/config.json"))`
- **THEN** MUST 使用 `load_config(config_path)` 加载 GameConfig

#### Scenario: run_tui_game launches RichmanTuiApp

- **WHEN** 调用 `run_tui_game()`
- **THEN** MUST 创建 `RichmanTuiApp(engine=engine, config=config, player_controllers=players)`
- **AND** MUST 调用 `app.run()`

### Requirement: RichmanTuiApp pushes GameScreen on mount

系统 SHALL 在 `RichmanTuiApp` 的 `on_mount` 中，当持有 engine 和 player_controllers 时，推送 `GameScreen` 启动引擎驱动循环。

#### Scenario: on_mount pushes GameScreen when engine present

- **WHEN** `RichmanTuiApp` 以 `engine=engine, config=config, player_controllers=players` 构造并 mount
- **THEN** `on_mount()` MUST 推送 `GameScreen(engine, config, player_controllers)`

#### Scenario: on_mount does not push GameScreen when engine is None

- **WHEN** `RichmanTuiApp` 以默认参数构造（engine=None, player_controllers=None）
- **THEN** `on_mount()` MUST NOT 推送 GameScreen
- **AND** MUST 保持现有静态展示行为

#### Scenario: GameScreen receives correct arguments

- **WHEN** `RichmanTuiApp.on_mount()` 推送 GameScreen
- **THEN** 传入 GameScreen 的 engine MUST 为构造 `RichmanTuiApp` 时传入的 engine
- **AND** config MUST 为构造时传入的 config
- **AND** player_controllers MUST 为构造时传入的 player_controllers
