## MODIFIED Requirements

### Requirement: run_tui_game assembles and launches TUI app

系统 SHALL 在 app 层提供 `create_tui_players(players_count, human_name)` 和 `run_tui_game(players_count, seed, config_path)` 函数。`create_tui_players` 创建 1 个 `HumanPlayer(human_name)` + (players_count - 1) 个 `AIPlayer`。`run_tui_game` 装配 GameConfig，将 config、seed、player_count 传给 `RichmanTuiApp`（`run_game_mode=True`）并启动。engine 和 players 的创建延后到 SetupScreen 用户确认后。

#### Scenario: create_tui_players accepts custom human name

- **WHEN** 调用 `create_tui_players(3, human_name="小明")`
- **THEN** 返回的玩家列表中 `players[0].name` MUST 为 "小明"
- **AND** `players[0]` MUST 为 `HumanPlayer` 实例

#### Scenario: create_tui_players uses default human name

- **WHEN** 调用 `create_tui_players(2)`
- **THEN** 返回的玩家列表中 `players[0].name` MUST 为 "玩家"

#### Scenario: run_tui_game creates game config

- **WHEN** 调用 `run_tui_game()` 不传 config_path
- **THEN** MUST 使用 `build_default_config()` 创建 GameConfig

#### Scenario: run_tui_game creates game config from custom path

- **WHEN** 调用 `run_tui_game(config_path=Path("/custom/config.json"))`
- **THEN** MUST 使用 `load_config(config_path)` 加载 GameConfig

#### Scenario: run_tui_game launches RichmanTuiApp in game mode

- **WHEN** 调用 `run_tui_game(players_count=3)`
- **THEN** MUST 创建 `RichmanTuiApp(config=config, seed=seed, player_count=3, run_game_mode=True)`
- **AND** MUST 调用 `app.run()`
- **AND** MUST NOT 在 `run_tui_game` 内调用 `create_engine` 或 `create_tui_players`

### Requirement: RichmanTuiApp supports three mount modes

系统 SHALL 在 `RichmanTuiApp` 的 `on_mount` 中按优先级判断三种模式：游戏模式推送 TitleScreen、快速启动模式直接推送 GameScreen、静态展示模式仅 compose。

#### Scenario: on_mount pushes TitleScreen in game mode

- **WHEN** `RichmanTuiApp` 以 `run_game_mode=True` 构造并 mount
- **THEN** `on_mount()` MUST 推送 `TitleScreen`

#### Scenario: on_mount pushes GameScreen when engine and players present

- **WHEN** `RichmanTuiApp` 以 `engine=engine, config=config, player_controllers=players` 构造并 mount（run_game_mode=False）
- **THEN** `on_mount()` MUST 推送 `GameScreen(engine, config, player_controllers)`

#### Scenario: on_mount does nothing in static mode

- **WHEN** `RichmanTuiApp` 以默认参数构造（run_game_mode=False，engine=None）
- **THEN** `on_mount()` MUST NOT 推送任何 screen
- **AND** MUST 保持现有静态展示行为

#### Scenario: TitleScreen to SetupScreen parameter flow

- **WHEN** TitleScreen 导航到 SetupScreen
- **THEN** SetupScreen 构造参数 MUST 为 `SetupScreen(config=self.app.config, seed=self.app.seed, player_count=self.app.player_count)`

### Requirement: RichmanTuiApp exposes config, seed, and player_count

系统 SHALL 在 `RichmanTuiApp` 上暴露 `seed: int | None` 和 `player_count: int` 属性，供子 Screen 通过 `self.app` 访问。

#### Scenario: seed attribute is accessible from screen

- **WHEN** TitleScreen 通过 `self.app.seed` 访问
- **THEN** 返回值 MUST 为构造 RichmanTuiApp 时传入的 seed

#### Scenario: player_count attribute is accessible from screen

- **WHEN** TitleScreen 通过 `self.app.player_count` 访问
- **THEN** 返回值 MUST 为构造 RichmanTuiApp 时传入的 player_count
