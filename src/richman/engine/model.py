"""Game engine that owns the complete mutable state tree and the five-phase turn loop."""

from __future__ import annotations

import random
from collections.abc import Sequence
from copy import deepcopy

from richman.board import (
    Board,
    get_cell_type,
    get_property_template,
    get_range,
)
from richman.board import (
    move as board_move,
)
from richman.domain import (
    Action,
    CardIntent,
    CardType,
    CellType,
    DeductMoneyIntent,
    GameConfig,
    GameEvent,
    GameEventType,
    GameSnapshot,
    GoToJailIntent,
    GrantMoneyIntent,
    HandCards,
    InternalGameState,
    MoveDirection,
    MoveIntent,
    ObtainCardIntent,
    Phase,
    PlayerState,
    PlayerView,
    PropertyRef,
    PropertyState,
    PublicBoardInfo,
    PublicCellInfo,
    PublicPlayerInfo,
)
from richman.player import Player
from richman.render import Renderer
from richman.rules import (
    calculate_bankruptcy,
    calculate_rent,
    can_afford,
    can_upgrade,
    resolve_card_intent,
)


class _EngineInputContext:
    """Restricted input surface exposed to players. Only prompt_choice is visible."""

    __slots__ = ("_renderer",)

    def __init__(self, renderer: Renderer) -> None:
        self._renderer = renderer

    def prompt_choice(self, question: str, options: Sequence[str]) -> str:
        return self._renderer.prompt_choice(question, tuple(options))


class GameEngine:
    """Owns InternalGameState and executes the five-phase turn loop.

    The engine is the only module that mutates game state. It calls board for
    spatial queries, rules for pure calculations, player for decisions, and
    render for display.
    """

    __slots__ = (
        "_acquisition_counter",
        "_board",
        "_config",
        "_context",
        "_jail_position",
        "_players",
        "_renderer",
        "_rng",
        "_state",
        "_winner_name",
    )

    def __init__(
        self,
        config: GameConfig,
        board: Board,
        players: Sequence[Player],
        renderer: Renderer,
        rng: random.Random,
        jail_position: int,
    ) -> None:
        self._config = config
        self._board = board
        self._players = tuple(players)
        self._renderer = renderer
        self._rng = rng
        self._jail_position = jail_position
        self._context = _EngineInputContext(renderer)
        self._acquisition_counter = 0
        self._winner_name: str | None = None
        self._state = self._init_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def create(
        config: GameConfig,
        board: Board,
        players: Sequence[Player],
        renderer: Renderer,
        seed: int | None = None,
    ) -> GameEngine:
        """Factory with optional determinism seed for reproducible tests."""
        rng = random.Random(seed)
        jail_positions = [
            pos
            for pos, cell_def in enumerate(board.cells)
            if cell_def.cell_type is CellType.JAIL_SPACE
        ]
        if len(jail_positions) != 1:
            raise ValueError("board must contain exactly one JAIL_SPACE cell")
        return GameEngine(config, board, players, renderer, rng, jail_positions[0])

    def get_state(self) -> InternalGameState:
        """Return the current mutable state tree for debugging/verification."""
        return self._state

    def snapshot_for(self, viewer_index: int) -> GameSnapshot:
        """Build a render-oriented snapshot for the given viewer."""
        return self._build_snapshot(viewer_index)

    def start(self, max_turns: int | None = None) -> InternalGameState:
        """Run the main game loop to completion and return the final state.

        Args:
            max_turns: Optional safety limit on total turns processed. ``None``
                       means no limit.
        """
        turns_taken = 0
        while not self._is_game_over():
            ps = self._current_player_state
            if ps.bankrupt:
                self._advance_to_next_player()
                continue

            if max_turns is not None and turns_taken >= max_turns:
                raise RuntimeError("max_turns reached before game over")

            self._state.turn += 1
            self._process_turn()
            turns_taken += 1
            if self._is_game_over():
                break
            self._advance_to_next_player()

        return self._state

    # ------------------------------------------------------------------
    # Main turn loop
    # ------------------------------------------------------------------

    def _process_turn(self) -> None:
        ps = self._current_player_state

        # ---- Phase ①: EFFECT_UPDATE ----
        self._state.phase = Phase.EFFECT_UPDATE
        self._log(GameEventType.TURN_START, player_name=ps.name)

        if ps.jail_rounds_left > 0:
            ps.jail_rounds_left -= 1
            self._log(
                GameEventType.JAIL_TICKED,
                player_name=ps.name,
                remaining=ps.jail_rounds_left,
            )
            if ps.jail_rounds_left == 0:
                self._log(GameEventType.JAIL_RELEASED, player_name=ps.name)

        if ps.jail_rounds_left > 0:
            self._to_end_phase()
            return

        # ---- Phase ②: DICE_ROLL ----
        self._state.phase = Phase.DICE_ROLL
        self._render_frame()
        self._log(GameEventType.WAIT_DICE, player_name=ps.name)
        self._current_player.wait_for_dice()

        dice = self._rng.randint(1, self._config.dice_sides)
        self._state.dice_value = dice
        self._log(GameEventType.DICE_ROLLED, value=dice)

        move_result = board_move(self._board, ps.position, dice)
        old_pos = ps.position
        ps.position = move_result.new_position
        self._log(
            GameEventType.PLAYER_MOVED,
            player_name=ps.name,
            from_position=old_pos,
            to_position=ps.position,
        )

        if move_result.start_crossings > 0:
            bonus = move_result.start_crossings * self._config.start_bonus
            ps.cash += bonus
            self._log(
                GameEventType.START_BONUS_GRANTED,
                player_name=ps.name,
                crossings=move_result.start_crossings,
                total_bonus=bonus,
            )

        # ---- Phase ③: LANDING ----
        turn_ended = self._process_landing()
        if turn_ended:
            self._to_end_phase()
            return

        # ---- Phase ④: ACTION ----
        self._process_action_phase()

        # ---- Phase ⑤: END ----
        self._to_end_phase()

    # ------------------------------------------------------------------
    # Phase ③ — landing logic
    # ------------------------------------------------------------------

    def _process_landing(self) -> bool:
        """Process landing at the current position. Returns True if turn should end."""
        ps = self._current_player_state
        pos = ps.position
        cell_type = get_cell_type(self._board, pos)

        self._state.phase = Phase.LANDING
        self._log(
            GameEventType.LANDED_ON,
            player_name=ps.name,
            cell_type=cell_type.value,
            position=pos,
        )

        if cell_type is CellType.START:
            return False  # bonus already handled by start_crossings

        if cell_type is CellType.PROPERTY:
            return self._process_property_landing()

        if cell_type is CellType.CHANCE:
            return self._process_chance_card()

        if cell_type is CellType.GO_TO_JAIL:
            return self._handle_jail_decision()

        # JAIL_SPACE, BLANK: nothing happens
        return False

    def _process_property_landing(self) -> bool:
        ps = self._current_player_state
        pos = ps.position
        prop = self._state.properties_by_position.get(pos)
        template = get_property_template(self._board, pos)

        if prop is None:
            return False

        owner_idx = prop.owner_player_index

        # Unowned
        if owner_idx is None:
            if template is not None:
                self._log(
                    GameEventType.PROPERTY_AVAILABLE,
                    position=pos,
                    name=template.name,
                    price=template.price,
                    rents=list(template.rents),
                )
            return False

        # Own property
        if owner_idx == self._state.current_player_index:
            if template is not None and can_upgrade(template, prop):
                self._log(
                    GameEventType.PROPERTY_UPGRADABLE,
                    position=pos,
                    name=template.name,
                    current_level=prop.level,
                    upgrade_cost=template.upgrade_cost,
                )
            return False

        # Someone else's property
        owner_state = self._state.players[owner_idx]
        if owner_state.jail_rounds_left > 0:
            self._log(
                GameEventType.RENT_SKIPPED_OWNER_IN_JAIL,
                from_player=ps.name,
                owner_name=owner_state.name,
            )
            return False

        if template is None:
            return False

        rent = calculate_rent(template, prop.level)
        return self._pay_debt(
            rent,
            creditor_index=owner_idx,
            due_event_type=GameEventType.RENT_DUE,
            paid_event_type=GameEventType.RENT_PAID,
            unpaid_event_type=GameEventType.RENT_UNPAID_BANKRUPTCY,
        )

    # ------------------------------------------------------------------
    # Phase ③ — chance card processing
    # ------------------------------------------------------------------

    def _process_chance_card(self) -> bool:
        """Draw and process a chance card. Returns True if turn should end."""
        ps = self._current_player_state

        if not self._config.cards:
            return False

        card = self._rng.choice(self._config.cards)
        self._log(
            GameEventType.CARD_DRAWN,
            player_name=ps.name,
            card_description=card.description,
        )

        intent = resolve_card_intent(card)
        return self._execute_card_intent(intent)

    def _execute_card_intent(self, intent: CardIntent) -> bool:
        """Execute a card intent. Returns True if turn should end."""
        ps = self._current_player_state

        if isinstance(intent, GrantMoneyIntent):
            ps.cash += intent.amount
            self._log(
                GameEventType.MONEY_GAINED,
                player_name=ps.name,
                amount=intent.amount,
            )
            return False

        if isinstance(intent, DeductMoneyIntent):
            self._log(
                GameEventType.MONEY_LOST,
                player_name=ps.name,
                amount=intent.amount,
            )
            return self._pay_debt(intent.amount)

        if isinstance(intent, MoveIntent):
            return self._execute_move_intent(intent)

        if isinstance(intent, GoToJailIntent):
            return self._handle_jail_decision()

        if isinstance(intent, ObtainCardIntent):
            if intent.card_type is CardType.JAIL_PASS:
                ps.hand.jail_pass += 1
            elif intent.card_type is CardType.DEMOLISH:
                ps.hand.demolish += 1
            return False

        return False

    def _execute_move_intent(self, intent: MoveIntent) -> bool:
        """Execute a move card. Handles recursive landing chain."""
        ps = self._current_player_state
        direction = intent.direction
        if direction is MoveDirection.RANDOM:
            direction = self._rng.choice([MoveDirection.FORWARD, MoveDirection.BACKWARD])

        steps = self._rng.randint(intent.min_steps, intent.max_steps)
        if direction is MoveDirection.BACKWARD:
            steps = -steps

        move_result = board_move(self._board, ps.position, steps)
        old_pos = ps.position
        ps.position = move_result.new_position
        self._log(
            GameEventType.PLAYER_MOVED,
            player_name=ps.name,
            from_position=old_pos,
            to_position=ps.position,
        )

        if move_result.start_crossings > 0:
            bonus = move_result.start_crossings * self._config.start_bonus
            ps.cash += bonus
            self._log(
                GameEventType.START_BONUS_GRANTED,
                player_name=ps.name,
                crossings=move_result.start_crossings,
                total_bonus=bonus,
            )

        # Recursive landing — only phase ③ effects, no phase ④
        return self._process_landing()

    # ------------------------------------------------------------------
    # Phase ④ — action phase
    # ------------------------------------------------------------------

    def _process_action_phase(self) -> None:
        self._state.phase = Phase.ACTION
        actions = self._compute_actions()
        self._state.available_actions = list(actions)

        if not actions:
            return

        self._render_frame()
        self._log(
            GameEventType.WAIT_ACTION,
            available_actions=[a.value for a in actions],
        )

        view = self._build_player_view(self._state.current_player_index, actions=actions)
        chosen = self._current_player.decide(view, actions, self._context)
        if chosen not in actions:
            raise ValueError(f"player chose unavailable action: {chosen}")

        self._log(
            GameEventType.ACTION_CHOSEN,
            player_name=self._current_player_state.name,
            action=chosen.value,
        )

        self._execute_action(chosen)

    def _compute_actions(self) -> list[Action]:
        ps = self._current_player_state
        pos = ps.position
        cell_type = get_cell_type(self._board, pos)
        actions: list[Action] = []

        if cell_type is CellType.PROPERTY:
            prop = self._state.properties_by_position.get(pos)
            template = get_property_template(self._board, pos)
            if prop is not None and template is not None:
                owner_idx = prop.owner_player_index
                if owner_idx is None and can_afford(ps.cash, template.price):
                    actions.append(Action.BUY)
                elif (
                    owner_idx == self._state.current_player_index
                    and can_upgrade(template, prop)
                    and can_afford(ps.cash, template.upgrade_cost)
                ):
                    actions.append(Action.UPGRADE)

        if ps.hand.demolish > 0:
            candidates = get_range(self._board, pos, self._config.demolish_range)
            has_target = any(
                self._state.properties_by_position.get(c) is not None
                and self._state.properties_by_position[c].level > 0
                for c in candidates
            )
            if has_target:
                actions.append(Action.USE_DEMOLISH)

        if actions:
            actions.append(Action.SKIP)

        return actions

    def _execute_action(self, action: Action) -> None:
        ps = self._current_player_state
        pos = ps.position

        if action is Action.BUY:
            template = get_property_template(self._board, pos)
            if template is None:
                return
            ps.cash -= template.price
            self._add_property(pos, template.price, template.name)
            self._log(
                GameEventType.PROPERTY_BOUGHT,
                player_name=ps.name,
                position=pos,
                name=template.name,
                price=template.price,
            )

        elif action is Action.UPGRADE:
            template = get_property_template(self._board, pos)
            prop = self._state.properties_by_position.get(pos)
            if template is None or prop is None:
                return
            cost = template.upgrade_cost
            ps.cash -= cost
            old_level = prop.level
            prop.level += 1
            prop.upgrade_invested += cost
            self._log(
                GameEventType.PROPERTY_UPGRADED,
                player_name=ps.name,
                position=pos,
                from_level=old_level,
                to_level=prop.level,
            )

        elif action is Action.USE_DEMOLISH:
            self._execute_demolish()

        # SKIP: nothing happens

    def _execute_demolish(self) -> None:
        ps = self._current_player_state
        pos = ps.position

        range_positions = get_range(self._board, pos, self._config.demolish_range)
        candidates = [
            p
            for p in range_positions
            if self._state.properties_by_position.get(p) is not None
            and self._state.properties_by_position[p].level > 0
        ]

        if not candidates:
            return

        self._render_frame()
        view = self._build_player_view(
            self._state.current_player_index,
            actions=list(self._state.available_actions or []),
        )
        target = self._current_player.choose_demolish_target(view, candidates, self._context)

        if target not in candidates:
            raise ValueError(f"invalid demolish target: {target}")

        ps.hand.demolish -= 1
        target_prop = self._state.properties_by_position[target]
        old_level = target_prop.level
        target_prop.level -= 1
        target_owner_idx = target_prop.owner_player_index
        if target_owner_idx is None:
            raise ValueError(f"demolish target at {target} has no owner")
        target_owner = self._state.players[target_owner_idx]

        self._log(
            GameEventType.PROPERTY_DEMOLISHED,
            user_name=ps.name,
            owner_name=target_owner.name,
            position=target,
            from_level=old_level,
            to_level=target_prop.level,
        )

    # ------------------------------------------------------------------
    # Jail handling
    # ------------------------------------------------------------------

    def _handle_jail_decision(self) -> bool:
        """Handle the go-to-jail flow. Returns True if turn should end."""
        ps = self._current_player_state

        if ps.hand.jail_pass > 0:
            actions = [Action.USE_JAIL_PASS, Action.ACCEPT_JAIL]
            self._render_frame()
            view = self._build_player_view(self._state.current_player_index, actions=actions)
            decision = self._current_player.decide(view, actions, self._context)
            if decision not in actions:
                raise ValueError(f"player chose unavailable jail action: {decision}")

            if decision is Action.USE_JAIL_PASS:
                ps.hand.jail_pass -= 1
                self._log(GameEventType.JAIL_PASS_USED, player_name=ps.name)
                return False
        else:
            decision = Action.ACCEPT_JAIL

        # Go to jail
        ps.position = self._jail_position
        ps.jail_rounds_left = self._config.jail_rounds
        self._log(
            GameEventType.PLAYER_SENT_TO_JAIL,
            player_name=ps.name,
            jail_position=self._jail_position,
        )
        return True

    # ------------------------------------------------------------------
    # Payment / bankruptcy
    # ------------------------------------------------------------------

    def _pay_debt(
        self,
        amount: int,
        creditor_index: int | None = None,
        due_event_type: GameEventType | None = None,
        paid_event_type: GameEventType | None = None,
        unpaid_event_type: GameEventType | None = None,
    ) -> bool:
        """Pay amount to a creditor (or bank if None). Returns True if bankrupt."""
        ps = self._current_player_state
        creditor_name: str | None = (
            self._state.players[creditor_index].name if creditor_index is not None else None
        )

        if due_event_type is not None and creditor_name is not None:
            self._log(
                due_event_type,
                from_player=ps.name,
                to_player=creditor_name,
                amount=amount,
            )

        if can_afford(ps.cash, amount):
            ps.cash -= amount
            if creditor_index is not None:
                self._state.players[creditor_index].cash += amount
            if paid_event_type is not None and creditor_name is not None:
                self._log(
                    paid_event_type,
                    from_player=ps.name,
                    to_player=creditor_name,
                    amount=amount,
                )
            return False

        shortfall = amount - ps.cash
        player_properties = [
            self._state.properties_by_position[ref.position] for ref in ps.holdings
        ]
        plan = calculate_bankruptcy(player_properties, shortfall)

        for position, refund in plan.reclaimed:
            self._reclaim_property(ps, position, refund)

        if plan.remaining_shortfall > 0:
            if unpaid_event_type is not None and creditor_name is not None:
                self._log(
                    unpaid_event_type,
                    from_player=ps.name,
                    to_player=creditor_name,
                    amount=amount,
                )
            self._finalize_bankruptcy(ps)
            return True

        # Full payment
        ps.cash += plan.total_refund
        ps.cash -= amount
        if creditor_index is not None:
            self._state.players[creditor_index].cash += amount
        if paid_event_type is not None and creditor_name is not None:
            self._log(
                paid_event_type,
                from_player=ps.name,
                to_player=creditor_name,
                amount=amount,
            )
        return False

    def _reclaim_property(self, player_state: PlayerState, position: int, refund: int) -> None:
        prop = self._state.properties_by_position[position]
        prop.owner_player_index = None
        prop.level = 0
        prop.purchase_price = 0
        prop.upgrade_invested = 0
        player_state.holdings = [r for r in player_state.holdings if r.position != position]
        self._log(
            GameEventType.PROPERTY_RECLAIMED,
            player_name=player_state.name,
            position=position,
            refund=refund,
        )

    def _finalize_bankruptcy(self, player_state: PlayerState) -> None:
        player_state.cash = 0
        player_state.hand = HandCards()
        player_state.bankrupt = True
        self._log(
            GameEventType.PLAYER_BANKRUPT,
            player_name=player_state.name,
        )

    # ------------------------------------------------------------------
    # Property management
    # ------------------------------------------------------------------

    def _add_property(self, position: int, price: int, name: str) -> None:
        ps = self._current_player_state
        prop = self._state.properties_by_position[position]
        prop.owner_player_index = self._state.current_player_index
        prop.level = 0
        prop.acquired_at = self._acquisition_counter
        prop.purchase_price = price
        prop.upgrade_invested = 0
        ps.holdings.append(PropertyRef(position=position))
        self._acquisition_counter += 1

    # ------------------------------------------------------------------
    # State initialization
    # ------------------------------------------------------------------

    def _init_state(self) -> InternalGameState:
        properties: dict[int, PropertyState] = {}
        for pos, cell_def in enumerate(self._board.cells):
            if cell_def.cell_type is CellType.PROPERTY:
                properties[pos] = PropertyState(position=pos, owner_player_index=None)

        players = [PlayerState(name=p.name, cash=self._config.start_cash) for p in self._players]

        return InternalGameState(
            players=players,
            turn=0,
            current_player_index=0,
            phase=Phase.EFFECT_UPDATE,
            dice_value=None,
            properties_by_position=properties,
            event_log=[],
            available_actions=None,
        )

    # ------------------------------------------------------------------
    # Phase ⑤ — end of turn
    # ------------------------------------------------------------------

    def _to_end_phase(self) -> None:
        self._state.phase = Phase.END
        self._log(
            GameEventType.TURN_END,
            player_name=self._current_player_state.name,
        )
        self._state.dice_value = None
        self._state.available_actions = None
        self._check_game_over()

    # ------------------------------------------------------------------
    # Turn progression
    # ------------------------------------------------------------------

    def _advance_to_next_player(self) -> None:
        n = len(self._state.players)
        for _ in range(n):
            self._state.current_player_index = (self._state.current_player_index + 1) % n
            if not self._state.players[self._state.current_player_index].bankrupt:
                return

    # ------------------------------------------------------------------
    # Game over
    # ------------------------------------------------------------------

    def _check_game_over(self) -> None:
        if self._winner_name is not None:
            return

        alive = [ps for ps in self._state.players if not ps.bankrupt]
        if len(alive) == 1:
            self._winner_name = alive[0].name
            self._log(
                GameEventType.GAME_OVER,
                winner_name=alive[0].name,
            )
            self._renderer.render_game_over(alive[0].name)

    def _is_game_over(self) -> bool:
        return self._winner_name is not None

    # ------------------------------------------------------------------
    # View generation
    # ------------------------------------------------------------------

    def _build_player_view(
        self,
        viewer_index: int,
        actions: Sequence[Action] | None = None,
    ) -> PlayerView:
        viewer_ps = self._state.players[viewer_index]
        viewer_props = tuple(
            self._copy_property_state(self._state.properties_by_position[ref.position])
            for ref in viewer_ps.holdings
            if ref.position in self._state.properties_by_position
        )
        return PlayerView(
            turn=self._state.turn,
            current_player_index=self._state.current_player_index,
            viewer_index=viewer_index,
            phase=self._state.phase,
            dice_value=self._state.dice_value,
            public_board=self._build_public_board(),
            public_players=self._build_public_players(),
            viewer_private=self._copy_player_state(viewer_ps),
            viewer_private_properties=viewer_props,
            available_actions=tuple(actions) if actions else (),
        )

    def _build_snapshot(self, viewer_index: int) -> GameSnapshot:
        viewer_ps = self._state.players[viewer_index]
        viewer_props = tuple(
            self._copy_property_state(self._state.properties_by_position[ref.position])
            for ref in viewer_ps.holdings
            if ref.position in self._state.properties_by_position
        )
        return GameSnapshot(
            turn=self._state.turn,
            current_player_index=self._state.current_player_index,
            viewer_index=viewer_index,
            phase=self._state.phase,
            dice_value=self._state.dice_value,
            public_board=self._build_public_board(),
            public_players=self._build_public_players(),
            viewer_private=self._copy_player_state(viewer_ps),
            viewer_private_properties=viewer_props,
            event_log=tuple(self._copy_event(event) for event in self._state.event_log),
            available_actions=tuple(self._state.available_actions)
            if self._state.available_actions is not None
            else None,
        )

    def _build_public_board(self) -> PublicBoardInfo:
        cells: list[PublicCellInfo] = []
        for pos, cell_def in enumerate(self._board.cells):
            prop = self._state.properties_by_position.get(pos)
            cells.append(
                PublicCellInfo(
                    position=pos,
                    cell_type=cell_def.cell_type,
                    property_name=(
                        cell_def.property_template.name
                        if cell_def.property_template is not None
                        else None
                    ),
                    owner_player_index=(prop.owner_player_index if prop is not None else None),
                    level=prop.level if prop is not None and prop.level > 0 else None,
                )
            )
        return PublicBoardInfo(cells=tuple(cells))

    def _build_public_players(self) -> tuple[PublicPlayerInfo, ...]:
        return tuple(
            PublicPlayerInfo(
                player_index=i,
                name=ps.name,
                position=ps.position,
                jail_rounds_left=ps.jail_rounds_left,
                bankrupt=ps.bankrupt,
            )
            for i, ps in enumerate(self._state.players)
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _current_player(self) -> Player:
        return self._players[self._state.current_player_index]

    @property
    def _current_player_state(self) -> PlayerState:
        return self._state.players[self._state.current_player_index]

    def _log(self, event_type: GameEventType, **data: object) -> None:
        self._state.event_log.append(GameEvent(event_type=event_type, data=data))

    def _render_frame(self) -> None:
        snapshot = self._build_snapshot(self._state.current_player_index)
        self._renderer.render_frame(snapshot)

    @staticmethod
    def _copy_player_state(player_state: PlayerState) -> PlayerState:
        return PlayerState(
            name=player_state.name,
            cash=player_state.cash,
            position=player_state.position,
            holdings=list(player_state.holdings),
            hand=HandCards(
                jail_pass=player_state.hand.jail_pass,
                demolish=player_state.hand.demolish,
            ),
            jail_rounds_left=player_state.jail_rounds_left,
            bankrupt=player_state.bankrupt,
        )

    @staticmethod
    def _copy_property_state(property_state: PropertyState) -> PropertyState:
        return PropertyState(
            position=property_state.position,
            owner_player_index=property_state.owner_player_index,
            level=property_state.level,
            acquired_at=property_state.acquired_at,
            purchase_price=property_state.purchase_price,
            upgrade_invested=property_state.upgrade_invested,
        )

    @staticmethod
    def _copy_event(event: GameEvent) -> GameEvent:
        return GameEvent(event_type=event.event_type, data=deepcopy(dict(event.data)))
