# Repository Guidelines

## Project Structure & Module Organization

This is a Python 3.13 project managed with `uv`. Source code lives under `src/richman`.
Core game concepts are split by module: `domain`, `board`, `rules`, `player`, `engine`, and
`render`. Runtime assembly and CLI entry points live in `src/richman/app.py` and
`src/richman/cli.py`. Textual TUI code is isolated in `src/richman/adapters/textual_tui`,
with `screens/` for app screens and `widgets/` for reusable UI components. Tests are in
`tests/` and generally mirror the behavior or adapter being tested. Design notes live in
`docs/`; OpenSpec specs and archived changes live in `openspec/`.

## Build, Test, and Development Commands

- `uv run pytest`: run the full test suite.
- `uv run ruff check src tests`: run lint and import-order checks.
- `uv run mypy src tests`: run strict type checks.
- `uv run richman play --players 2 --max-turns 10 --seed 1`: run a deterministic CLI game.
- `uv run richman tui --players 2 --seed 1`: launch the Textual TUI.
- `openspec validate --specs --strict`: validate the current OpenSpec specification set.

Run tests, lint, and mypy before committing behavior changes.

## Coding Style & Naming Conventions

Use 4-space indentation and keep lines at or below 100 characters. All new Python functions
must be typed; mypy is configured with `disallow_untyped_defs = true`. Prefer dataclasses and
small immutable value objects where existing modules already use them. Use snake_case for
modules, functions, variables, and test names; use PascalCase for classes. Keep adapter-specific
code out of core modules so render paths remain pluggable.

## Testing Guidelines

The project uses `pytest` with `pytest-asyncio` in auto mode. Add focused tests beside related
coverage, using names like `test_tui_command_uses_defaults` or `test_engine_step_returns_event`.
For TUI changes, cover layout calculation and screen/widget behavior without relying on manual
inspection. No explicit coverage threshold is configured; protect every changed behavior with a
regression test where practical.

## Commit & Pull Request Guidelines

Recent commits use short, imperative summaries, often in Chinese, describing the implemented
feature or archived OpenSpec change. Keep each commit scoped to one logical change and mention
the OpenSpec change id when relevant. Pull requests should include a concise description,
verification commands run, linked issue or change id, and screenshots or terminal notes for
visible TUI changes.

## Agent-Specific Instructions

Respect the OpenSpec workflow: inspect active changes before implementing, update specs/tasks
with code, and validate before archiving. Do not revert unrelated user changes in the worktree.
