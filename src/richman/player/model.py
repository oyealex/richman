"""Player decision implementations.

Player objects choose from options prepared by the engine. They never mutate
game state or calculate whether an action is available.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Protocol

from richman.domain import Action, PlayerView


class InputContext(Protocol):
    """Restricted input surface used by HumanPlayer."""

    def prompt_choice(self, question: str, options: Sequence[str]) -> str:
        """Return one option chosen by the human user."""
        ...


class PlayerDecisionError(ValueError):
    """Raised when player decision input or output violates the boundary."""


class Player(ABC):
    """Decision boundary shared by human and AI players."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name for the player."""
        raise NotImplementedError

    @abstractmethod
    def wait_for_dice(self) -> None:
        """Wait until the player is ready for the engine to roll dice."""
        raise NotImplementedError

    @abstractmethod
    def decide(
        self,
        view: PlayerView,
        actions: Sequence[Action],
        engine_context: InputContext | None,
    ) -> Action:
        """Choose one action from the engine-provided legal actions."""
        raise NotImplementedError

    @abstractmethod
    def choose_demolish_target(
        self,
        view: PlayerView,
        candidates: Sequence[int],
        engine_context: InputContext | None,
    ) -> int:
        """Choose one target from the engine-provided demolish candidates."""
        raise NotImplementedError


class HumanPlayer(Player):
    """Human player that delegates input to a restricted context."""

    __slots__ = ("_dice_waiter", "_name")

    def __init__(self, name: str, dice_waiter: Callable[[], None] | None = None) -> None:
        self._name = name
        self._dice_waiter = dice_waiter

    @property
    def name(self) -> str:
        """Display name for the player."""

        return self._name

    def wait_for_dice(self) -> None:
        """Wait for a human-controlled dice trigger."""

        if self._dice_waiter is not None:
            self._dice_waiter()

    def decide(
        self,
        view: PlayerView,
        actions: Sequence[Action],
        engine_context: InputContext | None,
    ) -> Action:
        """Ask the human to choose one legal action."""

        del view
        actions_tuple = _require_actions(actions)
        context = _require_context(engine_context)
        options_by_value = {action.value: action for action in actions_tuple}
        selected = context.prompt_choice("选择动作", tuple(options_by_value))

        try:
            return options_by_value[selected]
        except KeyError as error:
            raise PlayerDecisionError("selected action is not available") from error

    def choose_demolish_target(
        self,
        view: PlayerView,
        candidates: Sequence[int],
        engine_context: InputContext | None,
    ) -> int:
        """Ask the human to choose one legal demolish target."""

        del view
        candidates_tuple = _require_candidates(candidates)
        context = _require_context(engine_context)
        options_by_value = {str(candidate): candidate for candidate in candidates_tuple}
        selected = context.prompt_choice("选择拆除目标", tuple(options_by_value))

        try:
            return options_by_value[selected]
        except KeyError as error:
            raise PlayerDecisionError("selected demolish target is not available") from error


class AIPlayer(Player):
    """Simple deterministic AI player."""

    __slots__ = ("_action_priority", "_name")

    DEFAULT_ACTION_PRIORITY: tuple[Action, ...] = (
        Action.USE_JAIL_PASS,
        Action.BUY,
        Action.UPGRADE,
        Action.USE_DEMOLISH,
        Action.SKIP,
        Action.ACCEPT_JAIL,
    )

    def __init__(
        self,
        name: str,
        action_priority: Sequence[Action] = DEFAULT_ACTION_PRIORITY,
    ) -> None:
        self._name = name
        self._action_priority = tuple(action_priority)

    @property
    def name(self) -> str:
        """Display name for the player."""

        return self._name

    def wait_for_dice(self) -> None:
        """AI does not need a dice trigger."""

    def decide(
        self,
        view: PlayerView,
        actions: Sequence[Action],
        engine_context: InputContext | None,
    ) -> Action:
        """Choose the first available action in deterministic priority order."""

        del view, engine_context
        actions_tuple = _require_actions(actions)
        action_set = set(actions_tuple)

        for action in self._action_priority:
            if action in action_set:
                return action

        return actions_tuple[0]

    def choose_demolish_target(
        self,
        view: PlayerView,
        candidates: Sequence[int],
        engine_context: InputContext | None,
    ) -> int:
        """Choose the first engine-provided candidate."""

        del view, engine_context
        return _require_candidates(candidates)[0]


def _require_context(engine_context: InputContext | None) -> InputContext:
    if engine_context is None:
        raise PlayerDecisionError("human player requires an input context")
    return engine_context


def _require_actions(actions: Sequence[Action]) -> tuple[Action, ...]:
    actions_tuple = tuple(actions)
    if not actions_tuple:
        raise PlayerDecisionError("actions must not be empty")
    return actions_tuple


def _require_candidates(candidates: Sequence[int]) -> tuple[int, ...]:
    candidates_tuple = tuple(candidates)
    if not candidates_tuple:
        raise PlayerDecisionError("demolish candidates must not be empty")
    return candidates_tuple
