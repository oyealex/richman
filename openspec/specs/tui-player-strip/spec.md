# tui-player-strip Specification

## Purpose
TBD - created by archiving change add-tui-player-event-bars. Update Purpose after archive.
## Requirements
### Requirement: PlayerStrip renders all players in a single row

系统 SHALL 提供 `PlayerStrip` widget（Textual `Widget` 子类），接收 `GameSnapshot` 和 `player_controllers: Sequence[Player]`，在一行内横向展示所有玩家的紧凑状态信息。

#### Scenario: PlayerStrip renders player names

- **WHEN** 传入包含 2 个玩家的 GameSnapshot
- **THEN** PlayerStrip MUST 在渲染内容中包含每位玩家的名称

#### Scenario: PlayerStrip highlights current player

- **WHEN** 渲染 PlayerStrip，当前 `current_player_index` 为 1
- **THEN** PlayerStrip MUST 对索引 1 的玩家使用高亮样式区分

#### Scenario: PlayerStrip has fixed height of 1

- **WHEN** 检查 PlayerStrip CSS
- **THEN** `height` MUST 为 1

### Requirement: PlayerStrip shows full info for viewer human player

系统 SHALL 对当前视角的人类玩家（`player_index == viewer_index` 且对应 controller 为 `HumanPlayer`）展示完整信息：现金、位置、手牌（出狱卡/拆除卡数量）、入狱/破产状态。

#### Scenario: Viewer human player shows cash

- **WHEN** viewer 是人类玩家，`viewer_private.cash` 为 2000
- **THEN** PlayerStrip 内容 MUST 包含 "2000" 或等效现金标识

#### Scenario: Viewer human player shows hand cards

- **WHEN** viewer 是人类玩家，`viewer_private.hand.jail_pass=1, demolish=0`
- **THEN** PlayerStrip 内容 MUST 包含出狱卡数量 1

#### Scenario: Viewer human player shows jail status

- **WHEN** viewer 是人类玩家，`viewer_private.jail_rounds_left` 为 2
- **THEN** PlayerStrip 内容 MUST 展示入狱状态标识

#### Scenario: Viewer human player shows bankrupt status

- **WHEN** viewer 是人类玩家，`viewer_private.bankrupt` 为 True
- **THEN** PlayerStrip 内容 MUST 展示破产标识

### Requirement: PlayerStrip hides private info for AI players

系统 SHALL 对 AI 玩家仅展示公开信息（名称、位置、入狱/破产状态），不展示现金和手牌。

#### Scenario: AI player hides cash

- **WHEN** AI 玩家 `PublicPlayerInfo` 不包含现金字段
- **THEN** PlayerStrip 内容 MUST NOT 包含该 AI 玩家的现金信息

#### Scenario: AI player hides hand cards

- **WHEN** AI 玩家在 strip 中展示
- **THEN** PlayerStrip 内容 MUST NOT 包含该 AI 玩家的手牌信息

#### Scenario: AI player shows position and status

- **WHEN** AI 玩家位于 position=5，未破产
- **THEN** PlayerStrip 内容 MUST 包含位置 "5"
- **AND** MUST NOT 包含破产标识

### Requirement: PlayerStrip updates when snapshot changes

系统 SHALL 通过 `update_snapshot(snapshot: GameSnapshot)` 方法接收新快照并刷新渲染。

#### Scenario: Snapshot update refreshes player info

- **WHEN** 调用 `update_snapshot(new_snapshot)`，其中 viewer 的现金从 2000 变为 1800
- **THEN** PlayerStrip MUST 在渲染中展示 1800

### Requirement: PlayerStrip code is isolated in widgets package

系统 SHALL 确保 PlayerStrip 源码位于 `richman.adapters.textual_tui.widgets.player_strip` 模块。

#### Scenario: PlayerStrip import path

- **WHEN** 导入 PlayerStrip
- **THEN** 导入路径 MUST 为 `richman.adapters.textual_tui.widgets.player_strip.PlayerStrip`

