## Why

当前 TUI 游戏界面只有棋盘和操作栏，玩家无法直观看到自己的现金、手牌、位置状态，也无法在棋盘外看到最近事件摘要。人类玩家需要翻看 CenterPanel 的事件列表才能知道发生了什么，且 AI 玩家的状态对用户不可见——这些信息本应紧凑展示在棋盘外围，提升信息密度和操作效率。

## What Changes

- **新增 PlayerStrip widget**：一行横向玩家状态条，人类玩家展示现金、位置、手牌（出狱卡/拆除卡数量）、入狱/破产状态；AI 玩家仅展示名称、位置、入狱/破产状态，不泄露现金和手牌
- **新增 EventLine widget**：一行最新事件摘要，使用 `GameSnapshot.event_log[-1]` 渲染最近一条事件；点击或通过 GameScreen 级 E 键绑定发出 `OpenRequested` 消息供后续 EventLogModal 使用
- **调整 GameScreen 布局**：垂直排列变为 Header → BoardWidget → PlayerStrip → EventLine → ActionBar，棋盘可用高度扣减新增两行（PlayerStrip 1行 + EventLine 1行）
- **补测试**：覆盖 PlayerStrip 组件存在与内容、AI 隐私不泄露、EventLine 事件更新与消息发出、棋盘尺寸扣减后的正确渲染

## Capabilities

### New Capabilities

- `tui-player-strip`: PlayerStrip widget，展示所有玩家的紧凑状态行，人类/AI 差异化显示
- `tui-event-line`: EventLine widget，展示最新事件并发出 OpenRequested 消息

### Modified Capabilities

- `tui-game-screen`: GameScreen compose 布局从 Header→Board→ActionBar 变为 Header→Board→PlayerStrip→EventLine→ActionBar；棋盘可用高度扣减逻辑从 `height - 1 - 5` 变为 `height - 1 - 1 - 1 - 5`

## Impact

- **新增文件**: `widgets/player_strip.py`、`widgets/event_line.py`
- **修改文件**: `screens/game.py`（布局调整、高度扣减）、`widgets/__init__.py`（导出新 widget）
- **新增测试**: `tests/test_textual_tui_player_strip.py`、`tests/test_textual_tui_event_line.py`
- **修改测试**: `tests/test_textual_tui_game_screen.py`（验证新组件存在）
- 不影响 domain 模型、engine、非 TUI 路径
