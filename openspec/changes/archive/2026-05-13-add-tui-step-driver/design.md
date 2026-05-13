## Context

当前 TUI 架构是单层 App：`RichmanTuiApp.compose()` 直接产出 Header + BoardWidget + Footer，没有 Screen 概念。本次变更引入 Textual `Screen` 子类 `GameScreen`，负责持有 GameEngine 并通过 step API 驱动游戏循环。

## Goals / Non-Goals

- **Goals**: TUI 能驱动完整的 step 循环；人类输入通过 ActionBar 交互；AI 输入自动提交；game over 停止
- **Non-Goals**: TitleScreen、SetupScreen、richman tui CLI 入口、EventLogModal、CellDetailModal、骰子动画、AI toast

## Decisions

### 1. GameScreen 作为 Screen 而非 App

**决定**: `GameScreen(Screen)` 是 Textual Screen 子类，不修改 `RichmanTuiApp`。

**理由**: Screen 可以被 push/pop，后续 TitleScreen → GameScreen 流程自然成立。当前阶段 GameScreen 可以独立在测试 App 中使用，也可以手动 push 到 RichmanTuiApp 上验证。RichmanTuiApp 的整合留给后续 change。

### 2. Engine 和 Player 传入方式

**决定**: GameScreen 构造函数接收已创建好的 `GameEngine`、`GameConfig` 和 `player_controllers: Sequence[Player]`，不自己创建。

**理由**: Engine 创建涉及 Board、Player 列表等复杂装配，应由调用方（后续的 CLI 入口或测试）完成。GameScreen 只消费 engine，不负责装配。`player_controllers` 用于 AI 玩家类型检测——`engine.get_state().players` 返回的是 `PlayerState`（数据），不是 `Player`（决策接口），无法做 `isinstance` 判断。外层在创建 engine 时同时持有 `Player` 实例列表，传入 GameScreen 即可。

```python
class GameScreen(Screen[None]):
    def __init__(
        self,
        engine: GameEngine,
        config: GameConfig,
        player_controllers: Sequence[Player],
    ) -> None: ...
```

### 3. Compose 布局

**决定**: 垂直三区布局——Header（`show_clock=True`，1 行）、BoardWidget（主体）、ActionBar（底部 5 行固定）。

```
┌──────────────────────────────────┐
│  Header (1 row)                  │
├──────────────────────────────────┤
│         BoardWidget              │
│     (绝对定位，主体区域)          │
│                                  │
├──────────────────────────────────┤
│     ActionBar (5 rows)           │
└──────────────────────────────────┘
```

**BoardWidget 可用尺寸计算**: BoardWidget 不应拿到完整终端尺寸，否则不会为 Header/ActionBar 留空间。计算方式：

```python
# 在 compose() 或 on_mount() 中，此时 self.size 已有实际终端尺寸
header_height = 1
action_bar_height = 5
board_rows = self.size.height - header_height - action_bar_height
board_cols = self.size.width
board_terminal_size = (board_rows, board_cols)
```

`board_terminal_size` 同时传给 `compute_layout_geometry(config, terminal_size=board_terminal_size)` 和 `BoardWidget(snapshot, geometry, terminal_size=board_terminal_size)`。这样 BoardWidget 的尺寸不足判断会基于实际可用空间，而非完整终端尺寸。

### 4. Step 驱动循环

**决定**: 采用 async 循环 `_advance_loop()`，在 `on_mount` 中通过 `self.run_worker(self._advance_loop(), exclusive=True)` 启动为后台 worker。

```
on_mount()
  └→ self.run_worker(self._advance_loop(), exclusive=True)
       └→ while True:
            result = engine.advance(None)
            _apply_step_result(result)
            if result.required_input:
              if AI player → auto_submit, continue
              if human → break (等待 UI 交互)
            if result.game_over → break
            await asyncio.sleep(0.3)
```

`engine.advance()` 本身是同步方法，不阻塞事件循环。用 `run_worker` 将整个循环作为 async worker 运行，`exclusive=True` 确保同一时间只有一个推进循环。

### 5. AI 玩家检测

**决定**: 通过 `isinstance(player_controllers[idx], AIPlayer)` 检测 AI 玩家。

**理由**: `engine.get_state().players` 返回的是 `PlayerState`（运行时数据快照），不是 `Player` 决策接口。真正的 `AIPlayer` / `HumanPlayer` 实例存储在 `engine._players`（私有属性）。因此由调用方将创建 engine 时的同一批 `Player` 实例作为 `player_controllers` 传入 GameScreen，GameScreen 用 `player_controllers[required_input.player_index]` 做 `isinstance` 检测。

`player_controllers` 的索引顺序必须与 `engine.get_state().players` 的索引一致（即创建 engine 时传入的 players 顺序）。

### 6. AI 自动输入策略

**决定**: TUI 层自行构造 `EngineInput`，不使用 `engine._auto_input_for()`（那是私有方法）。策略简单直接：

- ROLL_DICE → `EngineInput(kind=ROLL_DICE, player_index=...)`
- ACTION_CHOICE → 取 `options[0]`（第一个合法动作）
- JAIL_CHOICE → 优先 `USE_JAIL_PASS` 如果在 options 中，否则 `ACCEPT_JAIL`
- DEMOLISH_TARGET → 取 `candidates[0]`

**理由**: 后续可扩展为调用 `AIPlayer.decide()` 获得更智能的决策，但当前阶段简单策略足够。

### 7. ActionBar 设计

**决定**: ActionBar 是普通 `Widget`，包含动态生成的 `Button` 子 widget。通过消息与 GameScreen 通信。

```
ActionBar
  ├─ ROLL_DICE:         [ 掷骰 (Enter) ]
  ├─ ACTION_CHOICE:     [ 购买 ] [ 升级 ] [ 拆除 ] [ 跳过 ]
  ├─ JAIL_CHOICE:       [ 使用出狱卡 ] [ 接受入狱 ]
  └─ DEMOLISH_TARGET:   "请点击棋盘上的目标格子: 3, 5"
```

- 每个按钮点击时发出 `ActionBar.ActionSubmitted(engine_input)` 消息
- Enter / Space 快捷键触发第一个（主）按钮
- DEMOLISH_TARGET 不显示按钮，只显示提示文字，输入通过 BoardWidget 点击完成

**动态更新实现**: Textual 的 `mount()` / `remove_children()` 是 async 方法。`set_required_input()` 作为同步入口，将新的 `RequiredInput` 存入属性并调用 `self.refresh()`；在 `watch_required_input()`（reactive 属性的 watcher）中执行 `await self.remove_children()` + `await self.mount(...)` 完成异步 DOM 操作。这样避免了同步方法中调用 async 的问题。

```python
class ActionBar(Widget):
    required_input: Reactive[RequiredInput | None] = Reactive(None)

    def watch_required_input(self, required: RequiredInput | None) -> None:
        """当 required_input 变化时，异步重建子 widget。"""
        ...

    def set_required_input(self, required: RequiredInput | None) -> None:
        """同步入口：设置 reactive 属性，触发 watcher。"""
        self.required_input = required
```

### 8. BoardWidget 点击接入

**决定**: GameScreen 直接处理 `CellWidget.CellClicked` 冒泡消息，不修改 BoardWidget。

```python
def on_cell_widget_cell_clicked(self, message: CellWidget.CellClicked) -> None:
    required = self._current_result.required_input
    if required is None or required.kind is not InputKind.DEMOLISH_TARGET:
        return
    if message.position in required.candidates:
        self._submit_input(EngineInput(
            kind=InputKind.DEMOLISH_TARGET,
            player_index=required.player_index,
            target_position=message.position,
        ))
```

### 9. Game Over 处理

**决定**: game_over=True 时 ActionBar 显示终局信息（赢家名称），不再调用 advance。

通过 `engine.get_state().event_log` 中最后一个 `GAME_OVER` 事件获取赢家名称，与 console 版逻辑一致。

### 10. 测试策略

**决定**: 测试分为两层：
- **Fake engine 测试**: 用 Fake 对象模拟 `engine.advance()` 返回预设 StepResult，测试 `_apply_step_result()`、`_submit_input()`、`_auto_input_for()`、`on_cell_widget_cell_clicked` 等所有分支。Fake engine 覆盖完整推进逻辑（含 AI 自动推进到 game over）
- **真实 engine smoke test**: 用 `GameEngine.create()` + `AIPlayer`（全 AI），推进有限步（如 5 步）验证 engine 集成正常。不做全 AI 推进到 game over——那样太慢且 sleep(0.3) 累积延迟不可控
- 测试中通过 monkeypatch 将 `asyncio.sleep` 替换为 0 延迟的 mock，避免测试变慢

## Risks / Trade-offs

- **async 循环复杂度**: `_continue_until_input_or_game_over()` 中的 while 循环 + asyncio.sleep 可能在快速 step 时产生视觉闪烁。后续可用 Textual `set_interval` 或 `call_later` 改善。
- **终端尺寸**: GameScreen 需要 BoardWidget 的最小尺寸 + ActionBar 的 5 行。当前默认布局需要 45+5=50 行、168 列。这个约束在后续整合 RichmanTuiApp 时需要处理。
- **引擎私有方法**: 不使用 `engine._auto_input_for()`，TUI 层自行构造输入。如果引擎的 AI 输入逻辑变更，TUI 需要同步更新——这是有意为之的耦合边界。
