"""Command line entry points for Richman."""

import typer

from richman import __app_name__, __version__
from richman.adapters.textual_tui.app import RichmanTuiApp

app = typer.Typer(add_completion=False, help="终端大富翁开发入口。")


@app.command()
def play() -> None:
    """启动 Textual TUI。"""

    RichmanTuiApp().run()


@app.command()
def version() -> None:
    """输出应用版本。"""

    typer.echo(f"{__app_name__} {__version__}")


def main() -> None:
    """Run the Typer CLI."""

    app()
