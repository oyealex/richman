## ADDED Requirements

### Requirement: Engine factory creates validated engine instance
The system SHALL provide `GameEngine.create(config, board, players, renderer, seed=None)` that validates input and returns an initialized engine with a fresh InternalGameState.

#### Scenario: Factory validates jail space existence
- **WHEN** create is called with a board that has no JAIL_SPACE cell
- **THEN** a ValueError is raised

#### Scenario: Factory validates single jail space
- **WHEN** create is called with a board that has exactly one JAIL_SPACE cell
- **THEN** the engine is created successfully

#### Scenario: Factory initializes state with correct player count
- **WHEN** create is called with N players
- **THEN** the engine's state contains exactly N PlayerState entries, each with name matching the player and cash equal to config.start_cash

#### Scenario: Factory initializes properties from board
- **WHEN** create is called with a board containing PROPERTY cells
- **THEN** the engine's state properties_by_position contains a PropertyState for each PROPERTY cell, all unowned (owner_player_index=None, level=0)

#### Scenario: Factory with seed produces deterministic state
- **WHEN** create is called twice with the same seed
- **THEN** both engine instances produce identical random sequences

### Requirement: Engine exposes current state
The system SHALL provide `get_state()` that returns the current InternalGameState.

#### Scenario: State reflects initial conditions
- **WHEN** `get_state()` is called after create but before start
- **THEN** it returns InternalGameState with turn=0, phase=EFFECT_UPDATE, dice_value=None, available_actions=None

### Requirement: Engine generates view snapshot
The system SHALL provide `snapshot_for(viewer_index)` that returns a GameSnapshot for the given viewer.

#### Scenario: Snapshot contains viewer private data
- **WHEN** `snapshot_for(0)` is called
- **THEN** the returned GameSnapshot has viewer_index=0 and includes viewer_private for player 0

#### Scenario: Snapshot masks other players private data
- **WHEN** `snapshot_for(0)` is called
- **THEN** the returned GameSnapshot's public_players does not include cash amounts for any player

### Requirement: Engine starts and runs main loop
The system SHALL provide `start()` that executes the main game loop until game over and returns the final InternalGameState.

#### Scenario: Start increments turn counter
- **WHEN** start() is called
- **THEN** the turn counter advances for each non-bankrupt player that takes a turn

#### Scenario: Start skips bankrupt players
- **WHEN** a player is marked bankrupt
- **THEN** that player is skipped in subsequent turns

#### Scenario: Start ends when one player remains
- **WHEN** only one non-bankrupt player remains
- **THEN** the game ends and that player is the winner

### Requirement: Engine skips bankrupt players during turn advancement
The system SHALL skip bankrupt players when advancing to the next player.

#### Scenario: Bankrupt player skipped
- **WHEN** player at index 1 is bankrupt and the current player index is 0
- **THEN** after advancing to next player, the current player index is 2 (skipping 1)
