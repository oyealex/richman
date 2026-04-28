## ADDED Requirements

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

### Requirement: Engine input context only exposes prompt_choice
The system SHALL provide an InputContext that only exposes prompt_choice, not InternalGameState or mutation API.

#### Scenario: InputContext delegates to renderer
- **WHEN** a HumanPlayer calls context.prompt_choice("选择动作", ["BUY", "SKIP"])
- **THEN** the call is forwarded to renderer.prompt_choice("选择动作", ("BUY", "SKIP"))

#### Scenario: InputContext has no access to engine internals
- **WHEN** an InputContext is passed to a Player
- **THEN** the Player cannot access InternalGameState, engine mutation methods, or other players private data through it
