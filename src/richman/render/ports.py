"""Framework-neutral contracts shared by render adapters and the engine boundary."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GameSnapshotView:
    """Minimal placeholder for engine-produced view data.

    This type will be replaced or expanded when the real `GameSnapshot` domain model lands.
    It deliberately uses only standard Python types so Textual and future Web adapters can
    consume the same boundary.
    """

    title: str = "终端大富翁"
    message: str = "开发环境已就绪"
    available_actions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DecisionRequest:
    """A request for human input produced by the engine/controller boundary."""

    player_name: str
    prompt: str
    options: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlayerDecision:
    """A user decision submitted by a render adapter."""

    action: str
    target: str | int | None = None
    payload: Mapping[str, object] = field(default_factory=dict)


class RenderAdapter(Protocol):
    """Synchronous render adapter protocol for framework-neutral boundaries."""

    def render(
        self,
        snapshot: GameSnapshotView,
        decision_request: DecisionRequest | None = None,
    ) -> None:
        """Render a snapshot and optional decision request."""
