"""Smoke tests for the Textual render adapter."""

from textual.widgets import Static

from richman.adapters.textual_tui import RichmanTuiApp
from richman.domain import (
    Action,
    CellType,
    GameSnapshot,
    HandCards,
    Phase,
    PlayerState,
    PublicBoardInfo,
    PublicCellInfo,
    PublicPlayerInfo,
)


async def test_textual_app_constructs_headless() -> None:
    player = PlayerState(
        name="测试玩家",
        cash=2_000,
        position=0,
        hand=HandCards(),
    )
    snapshot = GameSnapshot(
        turn=1,
        current_player_index=0,
        viewer_index=0,
        phase=Phase.ACTION,
        dice_value=None,
        public_board=PublicBoardInfo(
            cells=(PublicCellInfo(position=0, cell_type=CellType.START),),
        ),
        public_players=(PublicPlayerInfo(player_index=0, name=player.name, position=0),),
        viewer_private=player,
        viewer_private_properties=(),
        event_log=(),
        available_actions=(Action.SKIP,),
    )
    tui = RichmanTuiApp(
        snapshot=snapshot,
        decision_prompt="请选择动作",
        decision_options=("SKIP",),
    )

    async with tui.run_test() as pilot:
        assert tui.query_one("#status", Static)
        assert tui.query_one("#decision", Static)
        await pilot.press("q")


async def test_textual_app_constructs_with_default_snapshot() -> None:
    tui = RichmanTuiApp()

    async with tui.run_test() as pilot:
        assert tui.query_one("#status", Static)
        await pilot.press("q")
