# tui-setup-screen

## Purpose

SetupScreen 提供玩家数量选择、人类玩家名称编辑、开始游戏按钮，确认后创建 engine 并进入 GameScreen。

## Requirements

### Requirement: SetupScreen provides player count selection

系统 SHALL 在 `SetupScreen(config, seed, player_count)` 中提供总玩家数选择，范围 2-4，默认为构造时传入的 player_count。

#### Scenario: SetupScreen defaults to 2 players

- **WHEN** SetupScreen 被 mount
- **THEN** 玩家数量选择 MUST 默认值为 2

#### Scenario: SetupScreen allows selecting player count

- **WHEN** 用户在 SetupScreen 中将玩家数改为 3
- **THEN** MUST 显示 1 个人类玩家名称输入框和 2 个 AI 名称标签（固定"AI 1"、"AI 2"）

### Requirement: SetupScreen provides human player name editing

系统 SHALL 在 SetupScreen 中提供人类玩家名称编辑功能，AI 玩家名称固定显示不可编辑。默认人类名称为"玩家"。

#### Scenario: SetupScreen shows default human player name

- **WHEN** SetupScreen 以默认值 mount
- **THEN** 人类玩家名称输入框 MUST 默认值为"玩家"

#### Scenario: SetupScreen allows editing human player name

- **WHEN** 用户修改人类玩家名称为"小明"
- **THEN** SetupScreen MUST 记录该名称并在"开始游戏"时传给 `create_tui_players(human_name="小明")`

### Requirement: SetupScreen start button creates engine and navigates to GameScreen

系统 SHALL 在用户点击"开始游戏"按钮时，调用 app 层工厂函数创建玩家列表和 engine，然后推送 `GameScreen`。

#### Scenario: Start button creates engine with configured player count

- **WHEN** 用户设置玩家数为 3 并点击"开始游戏"
- **THEN** MUST 调用 `create_tui_players(3, human_name="玩家")` 创建玩家列表
- **AND** MUST 调用 `create_engine(config, players, seed=seed)` 创建 engine
- **AND** MUST 推送 `GameScreen(engine, config, players)`

#### Scenario: Start button uses edited human player name

- **WHEN** 用户将人类玩家名改为"小明"并点击"开始游戏"
- **THEN** `create_tui_players` 调用 MUST 传入 `human_name="小明"`
- **AND** 传入 `GameScreen` 的玩家列表中第一个玩家的 name MUST 为"小明"

#### Scenario: SetupScreen passes config from RichmanTuiApp

- **WHEN** SetupScreen 创建 engine
- **THEN** 使用的 GameConfig MUST 来自 `self.app.config`

### Requirement: SetupScreen code is isolated in screens package

系统 SHALL 确保 SetupScreen 源码位于 `richman.adapters.textual_tui.screens.setup` 模块。

#### Scenario: SetupScreen import path

- **WHEN** 导入 SetupScreen
- **THEN** 导入路径 MUST 为 `richman.adapters.textual_tui.screens.setup.SetupScreen`
