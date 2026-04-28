## ADDED Requirements

### Requirement: Landing on unowned property offers purchase
The system SHALL log PROPERTY_AVAILABLE when landing on an unowned PROPERTY cell.

#### Scenario: Unowned property available
- **WHEN** a player lands on a PROPERTY cell with no owner
- **THEN** PROPERTY_AVAILABLE event is logged with position, name, price, and rents

### Requirement: Landing on own property offers upgrade if possible
The system SHALL log PROPERTY_UPGRADABLE when landing on own property that can be upgraded.

#### Scenario: Own property upgradable
- **WHEN** a player lands on their own property with level < 3
- **THEN** PROPERTY_UPGRADABLE event is logged

#### Scenario: Own property at max level
- **WHEN** a player lands on their own property with level = 3
- **THEN** PROPERTY_UPGRADABLE event is NOT logged

### Requirement: Landing on opponent property pays rent
The system SHALL calculate and charge rent when landing on another player's property, unless the owner is in jail.

#### Scenario: Rent charged to visitor
- **WHEN** a player lands on another player's property and the owner is not in jail
- **THEN** rent is calculated via rules.calculate_rent and deducted from the visitor

#### Scenario: Rent skipped when owner in jail
- **WHEN** a player lands on another player's property and the owner is in jail
- **THEN** RENT_SKIPPED_OWNER_IN_JAIL event is logged and no rent is charged

### Requirement: Landing on CHANCE draws and executes a card
The system SHALL randomly draw a card, resolve its intent, and execute the effect.

#### Scenario: Card drawn and logged
- **WHEN** a player lands on CHANCE
- **THEN** a random card is drawn and CARD_DRAWN event is logged with the card description

#### Scenario: Money gain card
- **WHEN** a MONEY_GAIN card is drawn
- **THEN** the player's cash increases by the card amount and MONEY_GAINED event is logged

#### Scenario: Money loss card with sufficient funds
- **WHEN** a MONEY_LOSS card is drawn and the player has sufficient cash
- **THEN** the player's cash decreases by the amount and MONEY_LOST event is logged

#### Scenario: Money loss card triggers bankruptcy
- **WHEN** a MONEY_LOSS card is drawn and the player cannot afford it even after reclaiming all properties
- **THEN** the player is declared bankrupt and their turn ends

#### Scenario: Move card chains landing
- **WHEN** a MOVE card is drawn
- **THEN** the player moves to a new position, bonuses/crossings are processed, and landing effects at the new position are resolved

#### Scenario: Move card chain only processes phase ③
- **WHEN** a MOVE card causes a chain
- **THEN** intermediate landing positions only process phase ③ effects

#### Scenario: Obtain jail pass card
- **WHEN** a JAIL_PASS card is drawn
- **THEN** the player's hand.jail_pass increases by 1

#### Scenario: Obtain demolish card
- **WHEN** a DEMOLISH card is drawn
- **THEN** the player's hand.demolish increases by 1

### Requirement: Landing on GO_TO_JAIL triggers jail decision
The system SHALL offer the player a choice between using a jail pass or accepting jail.

#### Scenario: Player with jail pass uses it
- **WHEN** a player with jail_pass > 0 lands on GO_TO_JAIL and chooses USE_JAIL_PASS
- **THEN** jail_pass decreases by 1, JAIL_PASS_USED is logged, and the turn continues

#### Scenario: Player with jail pass accepts jail
- **WHEN** a player with jail_pass > 0 lands on GO_TO_JAIL and chooses ACCEPT_JAIL
- **THEN** the player is moved to JAIL_SPACE with jail_rounds_left=config.jail_rounds and PLAYER_SENT_TO_JAIL is logged

#### Scenario: Player without jail pass goes to jail automatically
- **WHEN** a player with jail_pass=0 lands on GO_TO_JAIL
- **THEN** the player is automatically moved to JAIL_SPACE without a decision prompt

### Requirement: Landing on JAIL_SPACE has no effect on non-jailed players
The system SHALL treat landing on JAIL_SPACE as a no-op for players who are not jailed.

#### Scenario: Visiting jail space
- **WHEN** a non-jailed player lands on JAIL_SPACE
- **THEN** no effects are applied and the turn continues

### Requirement: GO_TO_JAIL card triggers jail decision
The system SHALL handle GoToJailIntent from chance cards identically to landing on the GO_TO_JAIL cell.

#### Scenario: Go to jail card with jail pass
- **WHEN** a GoToJailIntent is resolved and the player has jail_pass > 0
- **THEN** the player is offered USE_JAIL_PASS or ACCEPT_JAIL

#### Scenario: Go to jail card without jail pass
- **WHEN** a GoToJailIntent is resolved and the player has jail_pass=0
- **THEN** the player is automatically sent to jail
