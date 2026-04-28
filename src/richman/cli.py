"""Command line entry points for Richman."""

from typing import Annotated

import typer

from richman import __app_name__, __version__
from richman.app import MAX_PLAYERS, MIN_PLAYERS, run_game

app = typer.Typer(add_completion=False, help="终端大富翁开发入口。")


@app.command()
def play(
    players: Annotated[
        int,
        typer.Option(
            "--players",
            "-p",
            min=MIN_PLAYERS,
            max=MAX_PLAYERS,
            help="AI 玩家数量。",
        ),
    ] = MIN_PLAYERS,
    max_turns: Annotated[
        int | None,
        typer.Option("--max-turns", min=0, help="最多运行回合数；省略则运行到游戏结束。"),
    ] = None,
    seed: Annotated[int | None, typer.Option("--seed", help="随机种子。")] = None,
) -> None:
    """启动一局默认 AI 对局。"""

    run_game(players_count=players, max_turns=max_turns, seed=seed)


@app.command()
def version() -> None:
    """输出应用版本。"""

    typer.echo(f"{__app_name__} {__version__}")


def main() -> None:
    """Run the Typer CLI."""

    app()
