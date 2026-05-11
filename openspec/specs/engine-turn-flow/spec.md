# engine-turn-flow Specification

## Purpose
Define the ordered turn phases and the state transitions the engine performs during a player turn.
## Requirements
### Requirement: Turn executes five phases in order
Each player turn SHALL progress through phases in the fixed order EFFECT_UPDATE → DICE_ROLL → LANDING → ACTION → END, while allowing step boundaries between phases and at key display points.

#### Scenario: Normal turn flow
- **WHEN** a non-jailed player starts their turn and valid inputs are supplied
- **THEN** the engine progresses through phase EFFECT_UPDATE, then DICE_ROLL, then LANDING, then ACTION, then END in that order

#### Scenario: Step boundaries preserve phase order
- **WHEN** adapter pauses between StepResult frames
- **THEN** subsequent `advance()` calls MUST resume from the same logical turn flow without skipping or reordering phases

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
The system SHALL request a dice-roll input, roll a random dice value after valid input is submitted, move the player on the board, and grant start bonuses.

#### Scenario: Dice input requested before roll
- **WHEN** a non-jailed human player enters phase ②
- **THEN** engine returns RequiredInput for ROLL_DICE before generating the dice value

#### Scenario: Dice roll produces value in range
- **WHEN** valid dice input is submitted during phase ②
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
The system SHALL compute legal actions for the current player and expose them through StepResult required input when a decision is needed.

#### Scenario: Actions computed before decision request
- **WHEN** phase ④ is entered
- **THEN** available_actions is set on InternalGameState before StepResult is returned
- **AND** RequiredInput.options contains the same legal actions

#### Scenario: Empty actions skips decision
- **WHEN** no actions are available
- **THEN** no RequiredInput is returned for action choice and the turn proceeds to phase ⑤

#### Scenario: Submitted action must be legal
- **WHEN** RequiredInput.options contains BUY and SKIP
- **AND** caller submits UPGRADE
- **THEN** engine MUST reject the input

### Requirement: Phase ⑤ resets turn state and checks victory
The system SHALL clear dice_value and available_actions, log TURN_END, and check for game over without directly rendering game-over output.

#### Scenario: Turn end cleanup
- **WHEN** phase ⑤ is entered
- **THEN** dice_value is set to None and available_actions is set to None

#### Scenario: Game over detected
- **WHEN** only one non-bankrupt player remains after phase ⑤
- **THEN** GAME_OVER event is logged
- **AND** StepResult.game_over is true

#### Scenario: Engine does not render game over
- **WHEN** game over is detected
- **THEN** engine MUST NOT call renderer.render_game_over
- **AND** adapter is responsible for presenting the winner from StepResult or snapshot events

### Requirement: Turn flow exposes required input points
系统 SHALL 在所有需要外部输入的节点返回 `RequiredInput`，而不是阻塞调用 player 或 renderer。

#### Scenario: Dice roll requires input
- **WHEN** 当前人类玩家进入 DICE_ROLL 阶段
- **THEN** `advance(None)` 返回 `RequiredInput(kind=ROLL_DICE, player_index=<current>)`

#### Scenario: Action choice requires input
- **WHEN** 当前人类玩家进入 ACTION 阶段且存在合法动作
- **THEN** `advance(None)` 返回 `RequiredInput(kind=ACTION_CHOICE, options=<legal actions>)`

#### Scenario: Demolish target requires input
- **WHEN** 当前人类玩家选择 `USE_DEMOLISH` 且存在候选目标
- **THEN** `advance(input)` 返回 `RequiredInput(kind=DEMOLISH_TARGET, candidates=<candidate positions>)`

#### Scenario: Jail choice requires input
- **WHEN** 当前人类玩家触发入狱判决且持有免狱卡
- **THEN** `advance(None)` 返回 `RequiredInput(kind=JAIL_CHOICE, options=(USE_JAIL_PASS, ACCEPT_JAIL))`

### Requirement: Turn flow exposes key display points
系统 SHALL 在关键展示点返回 StepResult，使 adapter 可以展示事件、播放短动画或暂停。

#### Scenario: Dice result display point
- **WHEN** engine 接受有效的掷骰输入并生成骰子值
- **THEN** 返回的 StepResult 包含 `DICE_ROLLED` 事件
- **AND** snapshot 中的 `dice_value` 为本次骰子值

#### Scenario: Movement display point
- **WHEN** 骰子或移动卡导致玩家位置变化
- **THEN** 返回的 StepResult 包含 `PLAYER_MOVED` 事件
- **AND** snapshot 中公开玩家位置已更新

#### Scenario: Turn end display point
- **WHEN** 当前玩家回合结束
- **THEN** 返回的 StepResult 包含 `TURN_END` 事件
- **AND** phase 为 END

### Requirement: AI turns auto-satisfy required input
系统 SHALL 能用 AI 策略非阻塞地满足 AI 当前玩家的输入请求。

#### Scenario: AI dice input proceeds without blocking
- **WHEN** 当前玩家是 AI 且 step 需要 ROLL_DICE
- **THEN** engine 或 driver 可以立即提交 AI 掷骰输入
- **AND** 不需要终端输入上下文

#### Scenario: AI action input uses legal options
- **WHEN** 当前玩家是 AI 且 step 需要 ACTION_CHOICE
- **THEN** AI 策略 MUST 只从 `RequiredInput.options` 中选择一个动作

