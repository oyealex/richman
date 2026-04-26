"""Smoke tests for the Textual render adapter."""

from textual.widgets import Static

from richman.adapters.textual_tui import RichmanTuiApp
from richman.render import DecisionRequest, GameSnapshotView


async def test_textual_app_constructs_headless() -> None:
    tui = RichmanTuiApp(
        snapshot=GameSnapshotView(message="测试快照", available_actions=("SKIP",)),
        decision_request=DecisionRequest(
            player_name="测试玩家",
            prompt="请选择动作",
            options=("SKIP",),
        ),
    )

    async with tui.run_test() as pilot:
        assert tui.query_one("#status", Static)
        assert tui.query_one("#decision", Static)
        await pilot.press("q")
