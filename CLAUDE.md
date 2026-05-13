# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Richman 是一个终端优先的大富翁游戏。核心使用 step API（`engine.advance(engine_input)` → `StepResult`）驱动回合，不依赖传统 game loop。渲染层通过 adapter 模式支持控制台（`rich` 库）和 TUI（`textual` 库）两种前端。

## Commands

```bash
uv run pytest tests/ -q              # 全量测试
uv run pytest tests/test_app.py -v   # 单个文件
uv run ruff check tests/ src/        # lint
uv run mypy src/                     # 类型检查（29 个文件）
richman play --players 2             # 控制台模式
richman tui --players 2              # TUI 模式
```

运行环境：Python 3.13+，依赖 `rich>=14`、`textual>=6`、`typer>=0.19`。CI 要求 ruff、mypy、pytest 全通过。

## Architecture

### Layers（自上而下）

```
cli.py          → Typer 命令行解析（play / tui / version）
app.py          → 装配层：工厂函数创建 config、players、engine，组装并启动
adapters/       → 渲染 adapter（仅 textual_tui 在 TUI 路径中使用）
  textual_tui/
    app.py        → RichmanTuiApp（三种模式入口）
    layout.py     → TuiLayout 几何计算、校验
    screens/      → Textual Screen：TitleScreen → SetupScreen → GameScreen
    widgets/      → BoardWidget、CellWidget、ActionBar、CenterPanel
board/model.py  → Board 创建与移动
rules/model.py  → 规则层（租金、破产、卡片结算）
engine/model.py → GameEngine：step API（advance / get_state / snapshot_for）
player/model.py → Player ABC、AIPlayer（确定性 AI）、HumanPlayer
domain/models.py → 数据模型、枚举、GameConfig、StepResult、EngineInput
render/ports.py → Renderer protocol、ConsoleRenderer
```

### 核心流程

**控制台路径**：`richman play` → `run_game()` → `create_engine()` → `run_console_game()` —— 同步推进，renderer 直接 `prompt_choice()` 获取人类输入。

**TUI 路径**：`richman tui` → `run_tui_game()` → `RichmanTuiApp(run_game_mode=True)` → `on_mount` → push `TitleScreen` → `SetupScreen` → `GameScreen._advance_loop()` —— 异步 worker 模式。人类输入由 `ActionBar` widget 提交，AI 输入在 worker 中自动处理。

### Step API

`GameEngine.advance(engine_input: EngineInput | None)` 返回 `StepResult`：
- `snapshot`：当前游戏画面
- `required_input`：`RequiredInput | None`，非空时引擎等待输入
- `game_over`：终局标志

非输入 step 间 `advance(None)` 自动推进；遇到 `required_input` 时，AI 玩家自动在 `_advance_loop` 内提交，人类玩家停止等待 UI 交互。`game_over=True` 时停止推进。

### RichmanTuiApp 三种模式

| 构造参数 | on_mount 行为 |
|----------|--------------|
| `run_game_mode=True` | push TitleScreen → SetupScreen → GameScreen |
| `engine=..., player_controllers=...` | 直接 push GameScreen（测试/快速路径） |
| 默认 | 仅 compose 静态棋盘（展示用） |

### OpenSpec workflow

所有变更使用 `openspec` spec-driven 流程。工件顺序：`proposal.md` → `design.md` + `specs/` → `tasks.md`。实现通过 `/openspec-apply-change`，完成后 `/openspec-archive-change`。归档前必须同步 delta specs 到 `openspec/specs/` 主目录。

## Testing

- **CLI 测试**：`CliRunner().invoke(app, [...])`，mock `run_game()` / `run_tui_game()`
- **TUI smoke test**：`async with app.run_test(size=(40, 120)) as pilot:` + `pilot.pause()` / `pilot.click()` / `pilot.press()`
- **Engine 测试**：`create_tui_players()` + `create_engine()` 直接创建，同步调用 `engine.advance()`
- **Fake engine**：在 `test_textual_tui_game_screen.py` 中已有模式，用于测试 GameScreen 行为
- Textual `run_test()` 必须在 async 测试函数中使用；用 `size` 参数提供足够终端尺寸
