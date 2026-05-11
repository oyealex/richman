# engine-view-generation Specification

## Purpose
Define the engine-generated player decision views and render snapshots.
## Requirements
### Requirement: PlayerView is generated for decisions
The system SHALL provide `_build_player_view(viewer_index, actions)` that returns a PlayerView containing only the data needed for player decisions.

#### Scenario: PlayerView contains viewer private data
- **WHEN** _build_player_view(0) is called
- **THEN** the returned PlayerView includes viewer_private with player 0's full PlayerState (cash, hand, holdings)

#### Scenario: PlayerView hides other players private data
- **WHEN** _build_player_view(0) is called
- **THEN** the returned PlayerView's public_players does not expose cash or hand information

#### Scenario: PlayerView includes available actions
- **WHEN** _build_player_view(0, actions=[BUY, SKIP]) is called
- **THEN** the returned PlayerView has available_actions=(BUY, SKIP)

### Requirement: GameSnapshot is generated for rendering
The system SHALL provide `snapshot_for(viewer_index)` that returns a GameSnapshot with the full event log.

#### Scenario: GameSnapshot includes event log
- **WHEN** snapshot_for(0) is called after some events have been logged
- **THEN** the returned GameSnapshot includes all logged events

#### Scenario: GameSnapshot includes viewer private properties
- **WHEN** snapshot_for(0) is called and player 0 owns properties
- **THEN** the returned GameSnapshot includes viewer_private_properties with full PropertyState details

### Requirement: Public board info reflects current state
The system SHALL generate PublicBoardInfo with cell types, property names, owners, and levels from the current state.

#### Scenario: Public board shows property ownership
- **WHEN** player 0 owns a property at position 3 with level 2
- **THEN** the PublicCellInfo at position 3 has owner_player_index=0 and level=2

#### Scenario: Public board shows unowned properties
- **WHEN** a property has no owner
- **THEN** the PublicCellInfo has owner_player_index=None and level=None

### Requirement: Public player info hides private data
The system SHALL include only public data in PublicPlayerInfo: name, position, jail status, and bankrupt status.

#### Scenario: Public player info excludes cash
- **WHEN** PublicPlayerInfo is generated
- **THEN** no cash amount is included

#### Scenario: Public player info includes jail status
- **WHEN** a player has jail_rounds_left=2
- **THEN** the PublicPlayerInfo shows jail_rounds_left=2

### Requirement: StepResult carries renderable snapshot
系统 SHALL 在每个 StepResult 中携带当前 viewer 可展示的 `GameSnapshot`。

#### Scenario: Required input frame has snapshot
- **WHEN** engine 返回 RequiredInput
- **THEN** 同一个 StepResult MUST 包含当前局面的 GameSnapshot
- **AND** adapter 可以在不读取 InternalGameState 的情况下渲染等待输入画面

#### Scenario: Display-only frame has snapshot
- **WHEN** engine 返回骰子、移动、落点或回合结束展示点
- **THEN** StepResult MUST 包含反映该展示点后的 GameSnapshot

### Requirement: StepResult carries incremental event view
系统 SHALL 在 StepResult 中暴露本 step 新增事件，并继续在 GameSnapshot 中提供完整事件日志。

#### Scenario: Incremental events are exposed
- **WHEN** 本次 advance 记录了 DICE_ROLLED 和 PLAYER_MOVED
- **THEN** StepResult.events 包含这两个新增事件

#### Scenario: Snapshot keeps complete event log
- **WHEN** 已经发生多次 step
- **THEN** StepResult.snapshot.event_log 包含当前 viewer 可见的完整事件序列

