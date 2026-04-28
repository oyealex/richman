## ADDED Requirements

### Requirement: Debt payment with sufficient cash
The system SHALL deduct the full amount from the player's cash when they can afford it.

#### Scenario: Simple payment to creditor
- **WHEN** a player with cash=1000 owes rent=300 to another player
- **THEN** the player's cash becomes 700 and the creditor receives 300

#### Scenario: Simple payment to bank
- **WHEN** a player with cash=500 draws a MONEY_LOSS card for 200
- **THEN** the player's cash becomes 300 (money disappears to the bank)

### Requirement: Debt payment with property reclamation
When a player cannot afford a debt, the system SHALL reclaim properties via rules.calculate_bankruptcy to cover the shortfall.

#### Scenario: Partial reclamation covers debt
- **WHEN** a player owes 500 with 100 cash and has a property worth 450 refund
- **THEN** the property is reclaimed, the debt is fully paid, and the player's final cash is 50 (100 + 450 - 500)

#### Scenario: Properties reclaimed in acquisition order
- **WHEN** a player owns two properties acquired at times 1 and 2
- **THEN** the property acquired at time 1 is reclaimed before the one acquired at time 2

#### Scenario: Reclaimed property resets to unowned
- **WHEN** a property is reclaimed
- **THEN** its owner_player_index becomes None, level becomes 0, purchase_price becomes 0, and upgrade_invested becomes 0

#### Scenario: Reclaimed property removed from holdings
- **WHEN** a property at position P is reclaimed
- **THEN** the player's holdings no longer contain a PropertyRef for position P

### Requirement: Bankruptcy when debt cannot be covered
When all properties are reclaimed and the debt still cannot be paid, the system SHALL declare the player bankrupt.

#### Scenario: Full bankruptcy
- **WHEN** a player's total cash + property refunds cannot cover the debt
- **THEN** PLAYER_BANKRUPT event is logged, cash is set to 0, hand cards are cleared, and bankrupt is set to True

#### Scenario: Creditor receives nothing on bankruptcy
- **WHEN** a player goes bankrupt while owing rent
- **THEN** the creditor receives no money at all (not even the bankrupt player's remaining cash)

#### Scenario: Bankrupt player skipped in future turns
- **WHEN** a player is marked bankrupt
- **THEN** subsequent turns skip that player

### Requirement: Rent payment event logging
The system SHALL log appropriate events for each stage of the rent payment process.

#### Scenario: Rent due logged
- **WHEN** rent is calculated for a landing
- **THEN** RENT_DUE event is logged with from_player, to_player, and amount

#### Scenario: Rent paid logged
- **WHEN** rent is successfully paid
- **THEN** RENT_PAID event is logged with from_player, to_player, and amount

#### Scenario: Rent unpaid bankruptcy logged
- **WHEN** rent cannot be paid and player goes bankrupt
- **THEN** RENT_UNPAID_BANKRUPTCY event is logged

### Requirement: Property reclamation events
The system SHALL log PROPERTY_RECLAIMED for each property reclaimed during bankruptcy resolution.

#### Scenario: Each reclaimed property logged
- **WHEN** N properties are reclaimed during bankruptcy resolution
- **THEN** N PROPERTY_RECLAIMED events are logged, each with position and refund amount
