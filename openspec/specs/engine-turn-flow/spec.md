## ADDED Requirements

### Requirement: Turn executes five phases in order
Each player turn SHALL execute phases in the fixed order: EFFECT_UPDATE → DICE_ROLL → LANDING → ACTION → END.

#### Scenario: Normal turn flow
- **WHEN** a non-jailed player starts their turn
- **THEN** the engine executes phase EFFECT_UPDATE, then DICE_ROLL, then LANDING, then ACTION, then END in that order

### Requirement: Phase ① decrements jail counter
The system SHALL decrement jail_rounds_left by 1 during EFFECT_UPDATE if the player is in jail.

#### Scenario: Jail countdown
- **WHEN** a player with jail_rounds_left=2 enters phase ①
- **THEN** jail_rounds_left becomes 1 and JAIL_TICKED event is logged

#### Scenario: Jail release
- **WHEN** a player with jail_rounds_left=1 enters phase ①
- **THEN** jail_rounds_left becomes 0 and JAIL_RELEASED event is logged

### Requirement: Jailed player skips phases ②③④
The system SHALL skip to phase ⑤ directly after phase ① if the player is still in jail.

#### Scenario: Jailed player turn is truncated
- **WHEN** a player has jail_rounds_left > 0 after phase ①
- **THEN** the engine skips DICE_ROLL, LANDING, and ACTION phases

#### Scenario: Released player continues full turn
- **WHEN** a player's jail_rounds_left reaches 0 during phase ①
- **THEN** the engine proceeds to phase ② DICE_ROLL

### Requirement: Phase ② rolls dice and moves player
The system SHALL wait for the player, roll a random dice value, move the player on the board, and grant start bonuses.

#### Scenario: Dice roll produces value in range
- **WHEN** dice is rolled during phase ②
- **THEN** the value is between 1 and config.dice_sides inclusive

#### Scenario: Player position updates after move
- **WHEN** the dice roll is D and the player is at position P
- **THEN** the player's position becomes move(P, D).new_position

#### Scenario: Start bonus granted for crossings
- **WHEN** the move result has start_crossings=N (N > 0)
- **THEN** the player receives N * config.start_bonus cash and START_BONUS_GRANTED event is logged

#### Scenario: No start bonus when no crossing
- **WHEN** the move result has start_crossings=0
- **THEN** no bonus is granted

### Requirement: Phase ③ processes landing effects
The system SHALL determine the cell type at the player's position and execute the corresponding landing logic.

#### Scenario: Landing on START
- **WHEN** the player lands on a START cell
- **THEN** LANDED_ON event is logged and the turn continues (no additional bonus beyond start_crossings)

#### Scenario: Landing on BLANK
- **WHEN** the player lands on a BLANK cell
- **THEN** LANDED_ON event is logged and the turn continues with no additional effects

### Requirement: Phase ④ computes and presents available actions
The system SHALL compute the set of legal actions for the current player and present them for decision.

#### Scenario: Actions computed before decision
- **WHEN** phase ④ is entered
- **THEN** available_actions is set on InternalGameState before calling player.decide()

#### Scenario: Empty actions skips decision
- **WHEN** no actions are available
- **THEN** player.decide() is not called and the turn proceeds to phase ⑤

### Requirement: Phase ⑤ resets turn state and checks victory
The system SHALL clear dice_value and available_actions, log TURN_END, and check for game over.

#### Scenario: Turn end cleanup
- **WHEN** phase ⑤ is entered
- **THEN** dice_value is set to None and available_actions is set to None

#### Scenario: Game over detected
- **WHEN** only one non-bankrupt player remains after phase ⑤
- **THEN** GAME_OVER event is logged and render_game_over is called
