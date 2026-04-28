"""Framework-neutral render contracts and default console renderer."""

from richman.render.ports import (
    ConsoleRenderer,
    Renderer,
    format_event,
    format_event_log,
    format_snapshot,
    prompt_choice,
    prompt_number,
    render_event_log,
    render_frame,
    render_game_over,
)

__all__ = [
    "ConsoleRenderer",
    "Renderer",
    "format_event",
    "format_event_log",
    "format_snapshot",
    "prompt_choice",
    "prompt_number",
    "render_event_log",
    "render_frame",
    "render_game_over",
]
